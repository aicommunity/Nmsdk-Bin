#!/usr/bin/env python3
"""Helpers for identical-cold repro harness (clone, soft/strip cold, TipR@Rmin, compare)."""
from __future__ import annotations

import csv
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
NM = Path("/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole")
TIPR_COLD = "86000000 86000000 86000000 86000000"
TIPR_RMIN = "20000000 20000000 20000000 86000000"
RMIN = "20000000"
L_COLD = "1 1 1 1"
ColdMode = Literal["soft", "strip"]

sys.path.insert(0, str(ROOT / "scripts"))
from audit_structtrain import last_pulse_ok  # noqa: E402
from selectivity_metrics import classify  # noqa: E402


@dataclass(frozen=True)
class Family:
    key: str
    gold: Path
    clone_name: str
    train_t: float
    metric: str  # ltz_potential_max | soma_amp_sum
    kind: str  # fastspan | branch
    span_ms: int


FAMILIES: dict[str, Family] = {
    "fastspan": Family(
        key="fastspan",
        gold=ROOT / "SelectivityFastSpan" / "EXP_span25ms_fast_C1e9",
        clone_name="FastSpan_span25_gen_C1e9",
        train_t=160.0,
        metric="ltz_potential_max",
        kind="fastspan",
        span_ms=25,
    ),
    "branch": Family(
        key="branch",
        gold=ROOT / "SelectivityBranch" / "EXP_br_span25_packA_gen_C1e9",
        clone_name="Branch_span25_packA_gen_C1e9",
        train_t=320.0,
        metric="soma_amp_sum",
        kind="branch",
        span_ms=25,
    ),
}

REPRO_ROOT = ROOT / "_repro"
INVEST_ROOT = REPRO_ROOT / "_invest"

# invest job id -> (family_key, cold_mode, dest_name)
INVEST_JOBS: dict[str, tuple[str, ColdMode, str]] = {
    "A1": ("fastspan", "soft", "A1_fs_soft_r1"),
    "A2": ("fastspan", "strip", "A2_fs_strip_r1"),
    "B1": ("branch", "soft", "B1_br_soft_r1"),
    "B2": ("branch", "strip", "B2_br_strip_r1"),
    "A1r2": ("fastspan", "soft", "A1_fs_soft_r2"),
    "B1r2": ("branch", "soft", "B1_br_soft_r2"),
}


def set_tag(text: str, tag: str, value: str, count: int = 0) -> str:
    return re.sub(
        rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)",
        lambda m: m.group(1) + value + m.group(2),
        text,
        count=count or 0,
    )


def get_tag(text: str, tag: str) -> str | None:
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)
    return m.group(1).strip() if m else None


def clone_root(family: Family, rep: int) -> Path:
    return REPRO_ROOT / family.clone_name / f"r{rep}"


def invest_root(job_id: str) -> Path:
    if job_id not in INVEST_JOBS:
        raise SystemExit(f"unknown invest job {job_id}")
    return INVEST_ROOT / INVEST_JOBS[job_id][2]


def free_gib(path: Path = Path("/")) -> float:
    import os

    st = os.statvfs(path)
    return (st.f_bavail * st.f_frsize) / (1 << 30)


def assert_disk_for_train() -> None:
    free = free_gib()
    if free < 50:
        raise SystemExit(f"HARD STOP Avail={free:.1f}G < 50G")
    if free < 80:
        raise SystemExit(f"STOP Avail={free:.1f}G < 80G — pack first")


def rsync_clone(gold: Path, dst: Path, project_name: str) -> None:
    if dst.exists():
        raise SystemExit(f"refuse existing clone {dst}")
    dst.mkdir(parents=True, exist_ok=False)
    excludes = [
        "--exclude=EventsLog/",
        "--exclude=StatisticLog/",
        "--exclude=SelectivityLog/",
        "--exclude=History.xml",
        "--exclude=*.log",
        "--exclude=settings.qt",
        "--exclude=ltz_sweep/",
        "--exclude=Test_bak_phase9/",
        "--exclude=bak_pre_eval/",
    ]
    subprocess.check_call(["rsync", "-a", *excludes, f"{gold}/", f"{dst}/"])
    for ini in (dst / "Train" / "Project.ini", dst / "Test" / "Project.ini"):
        if not ini.exists():
            continue
        t = ini.read_text(encoding="utf-8")
        t = re.sub(
            r"<ProjectName>[^<]*</ProjectName>",
            f"<ProjectName>{project_name}</ProjectName>",
            t,
            count=1,
        )
        ini.write_text(t, encoding="utf-8")


def strip_dendrite_segments_above_one(model_text: str) -> str:
    """Remove <DendriteX_Y>...</DendriteX_Y> for Y > 1 (keep tip-1 only)."""

    def repl(m: re.Match[str]) -> str:
        tip = int(m.group(3))
        return m.group(0) if tip <= 1 else ""

    return re.sub(
        r"<(Dendrite(\d+)_(\d+))\b[^>]*>.*?</\1>\s*",
        repl,
        model_text,
        flags=re.S,
    )


def rewrite_links_to_tip1(model_text: str) -> str:
    return re.sub(
        r"(NeuronTimeLearner(?:Branch)?\.Neuron\.Dendrite\d+)_\d+(\.(?:Exc|Inh)Synapse)",
        r"\1_1\2",
        model_text,
    )


def dendrite_tips_above_one(model_text: str) -> list[str]:
    tips = sorted(set(re.findall(r"<Dendrite(\d+)_(\d+)\b", model_text)))
    return [f"Dendrite{a}_{b}" for a, b in tips if int(b) > 1]


def tip_indices(model_text: str) -> list[int]:
    return sorted({int(b) for b in re.findall(r"<Dendrite\d+_(\d+)\b", model_text)})


def read_need(params: Path | str) -> str:
    text = params if isinstance(params, str) else params.read_text(encoding="utf-8")
    return (get_tag(text, "IsNeedToTrain") or "").strip()


def assert_train_cold_flags(params: Path, *, mode: ColdMode) -> None:
    t = params.read_text(encoding="utf-8")
    need = get_tag(t, "IsNeedToTrain")
    autocal = get_tag(t, "AutoCalibrateFixedLTZThreshold")
    L = " ".join((get_tag(t, "DendriteLength") or "").replace(",", " ").split())
    tipr = " ".join((get_tag(t, "TipSynapseResistance") or "").replace(",", " ").split())
    errs: list[str] = []
    if need != "1":
        errs.append(f"Need={need}")
    if autocal != "0":
        errs.append(f"AutoCal={autocal} (want 0)")
    if L != L_COLD:
        errs.append(f"L={L}")
    if tipr != TIPR_COLD:
        errs.append(f"TipR={tipr}")
    if errs:
        raise SystemExit(f"cold flags fail ({mode}): {', '.join(errs)}")


def _ensure_tag(text: str, tag: str, value: str, *, after_tag: str | None = None) -> str:
    """Set tag value, or insert a minimal tag block if missing."""
    if re.search(rf"<{tag}\b", text):
        return set_tag(text, tag, value, 1)
    # Match TimeLearner property attrs (bool)
    block = f'<{tag} Type="b" PType="257" IoType="17">{value}</{tag}>'
    if after_tag and re.search(rf"</{after_tag}>", text):
        return re.sub(rf"(</{after_tag}>)", rf"\1\n\t\t\t\t\t\t\t{block}", text, count=1)
    if re.search(r"</IsNeedToTrain>", text):
        return re.sub(r"(</IsNeedToTrain>)", rf"\1\n\t\t\t\t\t\t\t{block}", text, count=1)
    return text


def _cold_params_common(t: str, neuron: str) -> str:
    t = set_tag(t, "IsNeedToTrain", "1", 1)
    t = set_tag(t, "StructureBuildMode", "1", 1)
    t = set_tag(t, "NeuronClassName", neuron, 0)
    t = set_tag(t, "TipSynapseResistance", TIPR_COLD, 1)
    t = set_tag(t, "ResistanceMin", RMIN, 1)
    t = set_tag(t, "DendriteLength", L_COLD, 1)
    t = set_tag(t, "NumDendriteMembranePartsVec", L_COLD, 0)
    t = set_tag(t, "InitialSomaPotential", "0 0 0 0", 1)
    # Gold Done XML often lacks this tag — must inject or soft-cold never rebuilds
    t = _ensure_tag(t, "ResetToUntrainedState", "1", after_tag="IsNeedToTrain")
    t = set_tag(t, "UseFixedLTZThreshold", "0", 1) if re.search(r"<UseFixedLTZThreshold\b", t) else _ensure_tag(t, "UseFixedLTZThreshold", "0", after_tag="IsNeedToTrain")
    t = _ensure_tag(t, "AutoCalibrateFixedLTZThreshold", "0", after_tag="IsNeedToTrain")
    return t


def _cold_model_common(mt: str, neuron: str) -> str:
    mt = re.sub(r'(<Neuron Class=")[^"]+(">)', rf"\g<1>{neuron}\2", mt, count=1)
    mt = set_tag(mt, "NeuronClassName", neuron, 0)
    mt = set_tag(mt, "DendriteLength", L_COLD, 0)
    mt = set_tag(mt, "NumDendriteMembranePartsVec", L_COLD, 0)
    mt = set_tag(mt, "TipSynapseResistance", TIPR_COLD, 1)
    mt = set_tag(mt, "ResistanceMin", RMIN, 1)
    mt = set_tag(mt, "InitialSomaPotential", "0 0 0 0", 1)
    mt = set_tag(mt, "IsNeedToTrain", "1", 1)
    mt = set_tag(mt, "StructureBuildMode", "1", 1)
    mt = _ensure_tag(mt, "ResetToUntrainedState", "1", after_tag="IsNeedToTrain")
    if re.search(r"<UseFixedLTZThreshold\b", mt):
        mt = set_tag(mt, "UseFixedLTZThreshold", "0", 1)
    if re.search(r"<AutoCalibrateFixedLTZThreshold\b", mt):
        mt = set_tag(mt, "AutoCalibrateFixedLTZThreshold", "0", 1)
    return mt


def soft_cold_reset_train(train: Path) -> None:
    """Historical soft-cold: param L/TipR + links→tip-1; keep fat Model cable."""
    params = train / "Parameters_00.xml"
    model = train / "Model_00.xml"
    pt = params.read_text(encoding="utf-8")
    neuron = get_tag(pt, "NeuronClassName") or "NSPNeuronGenAsymRmD001C1e9"
    params.write_text(_cold_params_common(pt, neuron), encoding="utf-8")
    mt = _cold_model_common(model.read_text(encoding="utf-8"), neuron)
    mt = rewrite_links_to_tip1(mt)
    model.write_text(mt, encoding="utf-8")
    assert_train_cold_flags(params, mode="soft")
    tips = tip_indices(mt)
    if tips and max(tips) <= 1:
        print("WARN soft-cold: Model already tip-1 only (no fat cable)")


def strip_cold_reset_train(train: Path) -> None:
    """Strip Model to tip-1 segments + links (prior harness); AutoCal=0."""
    params = train / "Parameters_00.xml"
    model = train / "Model_00.xml"
    pt = params.read_text(encoding="utf-8")
    neuron = get_tag(pt, "NeuronClassName") or "NSPNeuronGenAsymRmD001C1e9"
    params.write_text(_cold_params_common(pt, neuron), encoding="utf-8")
    mt = _cold_model_common(model.read_text(encoding="utf-8"), neuron)
    mt = strip_dendrite_segments_above_one(mt)
    mt = rewrite_links_to_tip1(mt)
    model.write_text(mt, encoding="utf-8")
    assert_train_cold_flags(params, mode="strip")
    left = dendrite_tips_above_one(mt)
    if left:
        raise SystemExit(f"strip Model still has tips>1: {left[:12]}")


def cold_reset_train(train: Path, *, mode: ColdMode = "soft") -> None:
    if mode == "soft":
        soft_cold_reset_train(train)
    else:
        strip_cold_reset_train(train)


def apply_tiprmin(paths: list[Path]) -> None:
    for p in paths:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8").replace(",", ".")
        t = set_tag(t, "TipSynapseResistance", TIPR_RMIN, 1)
        t = set_tag(t, "ResistanceMin", RMIN, 1)
        p.write_text(t, encoding="utf-8")


def read_lengths(params: Path) -> list[int]:
    raw = get_tag(params.read_text(encoding="utf-8"), "DendriteLength") or ""
    return [int(float(x)) for x in raw.replace(",", " ").split()]


def patch_tip_exc_r(text: str, tips: list[int], *, branch: bool) -> str:
    """Set tip ExcSynapse1 Resistance to TipR@Rmin values (Branch: Dendrite1_L)."""
    for i, L in enumerate(tips):
        r = "20000000" if i < 3 else "86000000"
        if branch:
            pat = re.compile(
                rf'(<Dendrite1_{L} Class="[^"]+">.*?<ExcSynapse1 Class="[^"]+">'
                rf'.*?<Resistance Type="d"[^>]*>)[^<]*(</Resistance>)',
                re.S,
            )
        else:
            di = i + 1
            pat = re.compile(
                rf'(<Dendrite{di}_{L} Class="[^"]+">.*?<ExcSynapse1 Class="[^"]+">'
                rf'.*?<Resistance Type="d"[^>]*>)[^<]*(</Resistance>)',
                re.S,
            )
        text, n = pat.subn(lambda m, _r=r: m.group(1) + _r + m.group(2), text, count=1)
        if not n:
            print(f"WARN: no ExcSynapse Resistance tip L={L}", file=sys.stderr)
    return text


def fix_generator_tip_links(model_text: str, tips: list[int]) -> str:
    out = model_text
    for i, L in enumerate(tips, start=1):
        out = re.sub(
            rf"(NeuronTimeLearner\.Neuron\.Dendrite{i}_)\d+(\.(?:Exc|Inh)Synapse)",
            rf"\g<1>{L}\2",
            out,
        )
    return out


def fix_branch_tip_links(model_text: str, tips: list[int]) -> str:
    it = iter(tips)
    last = tips[-1] if tips else 1

    def repl(m: re.Match[str]) -> str:
        try:
            L = next(it)
        except StopIteration:
            L = last
        return f"{m.group(1)}{L}{m.group(3)}"

    return re.sub(
        r"(NeuronTimeLearnerBranch\.Neuron\.Dendrite1_)(\d+)(\.(?:Exc|Inh)Synapse)",
        repl,
        model_text,
    )


def overlay_neuron(train_model: Path, test_model: Path) -> None:
    train = train_model.read_text(encoding="utf-8")
    test = test_model.read_text(encoding="utf-8")
    mn = re.search(r'(<Neuron Class="[^"]+">.*?</Neuron>)', train, re.S)
    if not mn:
        raise SystemExit(f"no Neuron in {train_model}")
    test2, n = re.subn(
        r'<Neuron Class="[^"]+">.*?</Neuron>', mn.group(1), test, count=1, flags=re.S
    )
    if not n:
        raise SystemExit(f"no Neuron in {test_model}")
    test_model.write_text(test2, encoding="utf-8")


def first_tip_exc_r(model: Path, *, branch: bool, tip_L: int = 1) -> str:
    t = model.read_text(encoding="utf-8")
    if branch:
        pat = rf'<Dendrite1_{tip_L} Class="[^"]+">.*?<ExcSynapse1 Class="[^"]+">.*?<Resistance Type="d"[^>]*>([^<]*)</Resistance>'
    else:
        pat = rf'<Dendrite1_{tip_L} Class="[^"]+">.*?<ExcSynapse1 Class="[^"]+">.*?<Resistance Type="d"[^>]*>([^<]*)</Resistance>'
    m = re.search(pat, t, re.S)
    return (m.group(1).strip().replace(",", ".") if m else "")


def post_train_hygiene(root: Path, family: Family) -> None:
    """FastSpan pre-gate hygiene. Branch full prepare is done by phase8_tiprmin_gate."""
    if family.kind == "branch":
        # TipR property on Train only; Exc + Test rebuild via phase8 prepare_test
        apply_tiprmin([root / "Train" / "Parameters_00.xml", root / "Train" / "Model_00.xml"])
        tips = read_lengths(root / "Train" / "Parameters_00.xml")
        mp = root / "Train" / "Model_00.xml"
        mt = patch_tip_exc_r(mp.read_text(encoding="utf-8").replace(",", "."), tips, branch=True)
        mp.write_text(mt, encoding="utf-8")
        return

    train, test = root / "Train", root / "Test"
    apply_tiprmin(
        [
            train / "Parameters_00.xml",
            train / "Model_00.xml",
            test / "Parameters_00.xml",
            test / "Model_00.xml",
        ]
    )
    tips = read_lengths(train / "Parameters_00.xml")
    merge = ROOT / "SelectivityFastSpan" / "scripts" / "merge_train_weights.py"
    subprocess.check_call(
        [
            sys.executable,
            str(merge),
            str(train / "Parameters_00.xml"),
            str(test / "Parameters_00.xml"),
        ]
    )
    overlay_neuron(train / "Model_00.xml", test / "Model_00.xml")
    mt = (test / "Model_00.xml").read_text(encoding="utf-8").replace(",", ".")
    mt = fix_generator_tip_links(mt, tips)
    mt = patch_tip_exc_r(mt, tips, branch=False)
    (test / "Model_00.xml").write_text(mt, encoding="utf-8")
    for p in (test / "Parameters_00.xml", test / "Model_00.xml"):
        t = p.read_text(encoding="utf-8").replace(",", ".")
        t = set_tag(t, "IsNeedToTrain", "0", 1)
        t = set_tag(t, "UseFixedLTZThreshold", "1", 1)
        t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0", 1)
        t = set_tag(t, "TipSynapseResistance", TIPR_RMIN, 1)
        p.write_text(t, encoding="utf-8")
    # also tip Exc on Train Model
    mp = train / "Model_00.xml"
    mt = patch_tip_exc_r(mp.read_text(encoding="utf-8").replace(",", "."), tips, branch=False)
    mp.write_text(mt, encoding="utf-8")


def snapshot_gate(root: Path) -> dict[str, str]:
    train_p = root / "Train" / "Parameters_00.xml"
    test_p = root / "Test" / "Parameters_00.xml"
    model_p = root / "Train" / "Model_00.xml"
    csv_path = root / "Test" / "SelectivityLog" / "results.csv"
    tp = train_p.read_text(encoding="utf-8")
    L = get_tag(tp, "DendriteLength") or ""
    tipr = (
        get_tag(test_p.read_text(encoding="utf-8"), "TipSynapseResistance")
        if test_p.exists()
        else ""
    ) or ""
    thr = (
        get_tag(test_p.read_text(encoding="utf-8"), "FixedLTZThreshold")
        if test_p.exists()
        else ""
    ) or ""
    branch = "NeuronTimeLearnerBranch" in (
        model_p.read_text(encoding="utf-8") if model_p.exists() else ""
    )
    tips = read_lengths(train_p) if L else [1]
    tip1 = first_tip_exc_r(model_p, branch=branch, tip_L=tips[0] if tips else 1) if model_p.exists() else ""
    out = {
        "L": L.replace(",", " "),
        "TipR": tipr.replace(",", " "),
        "thr": thr.replace(",", "."),
        "Need": read_need(tp),
        "InitSoma": (get_tag(tp, "InitialSomaPotential") or "").replace(",", ".")[:64],
        "tip1_ExcR": tip1,
        "fires": "",
        "acc": "",
        "mode": "",
        "ok_audit": "",
        "last_pulse_ok": "0",
        "n": "0",
    }
    if not csv_path.exists():
        return out
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    m = classify(rows)
    out.update(
        {
            "fires": m.get("fires", ""),
            "acc": str(m.get("acc_strict", m.get("acc", ""))),
            "mode": m.get("mode", m.get("mode_legacy", "")),
            "ok_audit": str(int(bool(m.get("ok_audit")))),
            "n": str(m.get("n", len(rows))),
            "last_pulse_ok": last_pulse_ok(rows),
        }
    )
    return out


def verdict_family(gold: dict[str, str], r1: dict[str, str], r2: dict[str, str]) -> str:
    def L(d: dict[str, str]) -> str:
        return " ".join(d.get("L", "").split())

    def fires(d: dict[str, str]) -> str:
        return d.get("fires", "")

    if fires(r1) != fires(r2) or L(r1) != L(r2):
        return "NONDET"
    try:
        acc_ok = int(r1.get("acc") or 0) >= 8 and int(r2.get("acc") or 0) >= 8
    except ValueError:
        acc_ok = False
    if r1.get("ok_audit") == "1" and r2.get("ok_audit") == "1" and acc_ok:
        if fires(r1) == fires(gold) and L(r1) == L(gold):
            return "REPRO_OK_EXACT"
        return "REPRO_OK_QUALITY"
    for r in (r1, r2):
        if r.get("ok_audit") != "1":
            return "REPRO_FAIL"
        if fires(r) != fires(gold):
            return "REPRO_FAIL"
    if L(r1) == L(gold) and r1.get("last_pulse_ok") == "1" and r2.get("last_pulse_ok") == "1":
        return "REPRO_OK"
    try:
        if int(r1.get("acc") or 0) >= 7 and int(r2.get("acc") or 0) >= 7:
            return "REPRO_SOFT"
    except ValueError:
        pass
    return "REPRO_SOFT"


def _cold_test_params(dst: Path) -> None:
    tp = dst / "Test" / "Parameters_00.xml"
    if not tp.exists():
        return
    t = tp.read_text(encoding="utf-8")
    t = set_tag(t, "IsNeedToTrain", "0", 1)
    t = set_tag(t, "DendriteLength", L_COLD, 1)
    t = set_tag(t, "TipSynapseResistance", TIPR_COLD, 1)
    tp.write_text(t, encoding="utf-8")


def prepare_family(
    family: Family,
    reps: tuple[int, ...] = (1, 2),
    *,
    force: bool = False,
    mode: ColdMode = "soft",
) -> list[Path]:
    REPRO_ROOT.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for rep in reps:
        dst = clone_root(family, rep)
        if dst.exists():
            if force:
                shutil.rmtree(dst)
            else:
                print(f"skip existing {dst}")
                out.append(dst)
                continue
        pname = f"{family.clone_name}_r{rep}_{mode}"
        print(f"clone {family.gold.name} -> {dst} cold={mode}")
        rsync_clone(family.gold, dst, pname)
        cold_reset_train(dst / "Train", mode=mode)
        _cold_test_params(dst)
        mt = (dst / "Train" / "Model_00.xml").read_text(encoding="utf-8")
        if mode == "strip":
            left = dendrite_tips_above_one(mt)
            if left:
                raise SystemExit(f"prepare assert failed tips>1: {left}")
            print("  strip ok L=1 1 1 1 TipR cold AutoCal=0")
        else:
            tips = tip_indices(mt)
            print(f"  soft ok L=1 1 1 1 TipR cold AutoCal=0 tips_max={max(tips) if tips else 0}")
        out.append(dst)
    return out


def prepare_invest(job_id: str, *, force: bool = False) -> Path:
    fam_key, mode, _name = INVEST_JOBS[job_id]
    family = FAMILIES[fam_key]
    dst = invest_root(job_id)
    INVEST_ROOT.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if force:
            shutil.rmtree(dst)
        else:
            raise SystemExit(f"refuse existing invest {dst} (use --force)")
    pname = f"invest_{job_id}_{mode}"
    print(f"INVEST prepare {job_id}: {family.gold.name} -> {dst} cold={mode}")
    rsync_clone(family.gold, dst, pname)
    cold_reset_train(dst / "Train", mode=mode)
    _cold_test_params(dst)
    assert_train_cold_flags(dst / "Train" / "Parameters_00.xml", mode=mode)
    mt = (dst / "Train" / "Model_00.xml").read_text(encoding="utf-8")
    tips = tip_indices(mt)
    if mode == "soft":
        if tips and max(tips) <= 1:
            print("WARN soft invest: tip max <=1")
        else:
            print(f"  soft preflight tips_max={max(tips)}")
    else:
        if dendrite_tips_above_one(mt):
            raise SystemExit("strip invest still has tips>1")
        print("  strip preflight tip-1 only")
    return dst


def append_compare_row(job_id: str, family: Family, mode: ColdMode, root: Path) -> Path:
    snap = snapshot_gate(root)
    gold = snapshot_gate(family.gold)
    compare = INVEST_ROOT / "COMPARE.md"
    INVEST_ROOT.mkdir(parents=True, exist_ok=True)
    if not compare.exists():
        compare.write_text(
            "# Cold invest COMPARE\n\n"
            "| ID | cold | Need_end | L | InitSoma | TipR | tip1_ExcR | thr | fires | acc | ok_audit | last_pulse | vs_gold_L | vs_gold_fires |\n"
            "|----|------|----------|---|----------|------|-----------|-----|-------|-----|----------|------------|-----------|---------------|\n",
            encoding="utf-8",
        )
    vs_L = "Y" if " ".join(snap.get("L", "").split()) == " ".join(gold.get("L", "").split()) else "N"
    vs_f = "Y" if snap.get("fires") == gold.get("fires") else "N"
    line = (
        f"| {job_id} | {mode} | {snap.get('Need','')} | `{snap.get('L','')}` | "
        f"`{snap.get('InitSoma','')[:40]}` | `{snap.get('TipR','')[:40]}` | "
        f"`{snap.get('tip1_ExcR','')}` | {snap.get('thr','')} | `{snap.get('fires','')}` | "
        f"{snap.get('acc','')} | {snap.get('ok_audit','')} | {snap.get('last_pulse_ok','')} | "
        f"{vs_L} | {vs_f} |\n"
    )
    # replace existing row for same ID if present
    text = compare.read_text(encoding="utf-8")
    rows = text.splitlines(keepends=True)
    out_lines: list[str] = []
    replaced = False
    for r in rows:
        if r.startswith(f"| {job_id} |"):
            out_lines.append(line)
            replaced = True
        else:
            out_lines.append(r)
    if not replaced:
        if out_lines and not out_lines[-1].endswith("\n"):
            out_lines[-1] += "\n"
        out_lines.append(line)
    compare.write_text("".join(out_lines), encoding="utf-8")
    return compare

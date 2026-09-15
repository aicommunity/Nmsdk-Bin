#!/usr/bin/env python3
"""Helpers for identical-cold repro harness (clone, cold reset, TipR@Rmin, compare)."""
from __future__ import annotations

import csv
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NM = Path("/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole")
TIPR_COLD = "86000000 86000000 86000000 86000000"
TIPR_RMIN = "20000000 20000000 20000000 86000000"
RMIN = "20000000"
L_COLD = "1 1 1 1"

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


def free_gib(path: Path = Path("/")) -> float:
    st = path.stat() if False else None
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
    ]
    subprocess.check_call(
        ["rsync", "-a", *excludes, f"{gold}/", f"{dst}/"]
    )
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
    model_text = re.sub(
        r"(NeuronTimeLearner(?:Branch)?\.Neuron\.Dendrite\d+)_\d+(\.(?:Exc|Inh)Synapse)",
        r"\1_1\2",
        model_text,
    )
    return model_text


def dendrite_tips_above_one(model_text: str) -> list[str]:
    tips = sorted(set(re.findall(r"<Dendrite(\d+)_(\d+)\b", model_text)))
    return [f"Dendrite{a}_{b}" for a, b in tips if int(b) > 1]


def cold_reset_train(train: Path) -> None:
    """Canonical cold on Train Parameters+Model (in-clone, after rsync from gold)."""
    params = train / "Parameters_00.xml"
    model = train / "Model_00.xml"
    pt = params.read_text(encoding="utf-8")
    neuron = get_tag(pt, "NeuronClassName") or "NSPNeuronGenAsymRmD001C1e9"

    def cold_params(t: str) -> str:
        t = set_tag(t, "IsNeedToTrain", "1", 1)
        t = set_tag(t, "StructureBuildMode", "1", 1)
        t = set_tag(t, "NeuronClassName", neuron, 0)
        t = set_tag(t, "TipSynapseResistance", TIPR_COLD, 1)
        t = set_tag(t, "ResistanceMin", RMIN, 1)
        t = set_tag(t, "DendriteLength", L_COLD, 1)
        t = set_tag(t, "NumDendriteMembranePartsVec", L_COLD, 0)
        t = set_tag(t, "InitialSomaPotential", "0 0 0 0", 1)
        if re.search(r"<ResetToUntrainedState\b", t):
            t = set_tag(t, "ResetToUntrainedState", "1", 1)
        t = set_tag(t, "UseFixedLTZThreshold", "0", 1)
        t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "1", 1)
        return t

    params.write_text(cold_params(pt), encoding="utf-8")

    mt = model.read_text(encoding="utf-8")
    mt = re.sub(r'(<Neuron Class=")[^"]+(">)', rf"\g<1>{neuron}\2", mt, count=1)
    mt = set_tag(mt, "NeuronClassName", neuron, 0)
    mt = set_tag(mt, "DendriteLength", L_COLD, 0)
    mt = set_tag(mt, "NumDendriteMembranePartsVec", L_COLD, 0)
    mt = set_tag(mt, "TipSynapseResistance", TIPR_COLD, 1)
    mt = set_tag(mt, "ResistanceMin", RMIN, 1)
    mt = set_tag(mt, "InitialSomaPotential", "0 0 0 0", 1)
    mt = set_tag(mt, "IsNeedToTrain", "1", 1)
    mt = set_tag(mt, "StructureBuildMode", "1", 1)
    if re.search(r"<ResetToUntrainedState\b", mt):
        mt = set_tag(mt, "ResetToUntrainedState", "1", 1)
    mt = strip_dendrite_segments_above_one(mt)
    mt = rewrite_links_to_tip1(mt)
    model.write_text(mt, encoding="utf-8")

    left = dendrite_tips_above_one(mt)
    if left:
        raise SystemExit(f"cold Model still has tips>1: {left[:12]}")


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


def fix_generator_tip_links(model_text: str, tips: list[int]) -> str:
    """TimeLearner: Dendrite{i}_{tips[i-1]} for i=1..4."""
    out = model_text
    for i, L in enumerate(tips, start=1):
        out = re.sub(
            rf"(NeuronTimeLearner\.Neuron\.Dendrite{i}_)\d+(\.(?:Exc|Inh)Synapse)",
            rf"\g<1>{L}\2",
            out,
        )
    return out


def fix_branch_tip_links(model_text: str, tips: list[int]) -> str:
    """Rewrite Branch Generator tip connectors to Dendrite1_{L[i]} in order of appearance."""
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


def post_train_hygiene(root: Path, family: Family) -> None:
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
    # merge params
    if family.kind == "fastspan":
        merge = ROOT / "SelectivityFastSpan" / "scripts" / "merge_train_weights.py"
        subprocess.check_call(
            [
                sys.executable,
                str(merge),
                str(train / "Parameters_00.xml"),
                str(test / "Parameters_00.xml"),
            ]
        )
    else:
        merge = ROOT / "SelectivityLtzCalibrate" / "scripts" / "merge_train_weights.py"
        # branch merge signature may differ — try FastSpan-style first via local copy of tags
        _merge_params_simple(train / "Parameters_00.xml", test / "Parameters_00.xml")

    overlay_neuron(train / "Model_00.xml", test / "Model_00.xml")
    mt = (test / "Model_00.xml").read_text(encoding="utf-8").replace(",", ".")
    if family.kind == "branch":
        mt = fix_branch_tip_links(mt, tips)
    else:
        mt = fix_generator_tip_links(mt, tips)
    (test / "Model_00.xml").write_text(mt, encoding="utf-8")

    # Test inference flags
    for p in (test / "Parameters_00.xml", test / "Model_00.xml"):
        t = p.read_text(encoding="utf-8").replace(",", ".")
        t = set_tag(t, "IsNeedToTrain", "0", 1)
        t = set_tag(t, "UseFixedLTZThreshold", "1", 1)
        t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0", 1)
        t = set_tag(t, "TipSynapseResistance", TIPR_RMIN, 1)
        p.write_text(t, encoding="utf-8")


def _merge_params_simple(train_p: Path, test_p: Path) -> None:
    tags = [
        "TipSynapseResistance",
        "DendriteLength",
        "InitialSomaPotential",
        "NumSynapse",
        "NumDendriteMembranePartsVec",
        "NeuronClassName",
        "FixedLTZThreshold",
        "LTZThreshold",
        "UseFixedLTZThreshold",
        "AutoCalibrateFixedLTZThreshold",
    ]
    train = train_p.read_text(encoding="utf-8")
    test = test_p.read_text(encoding="utf-8")
    for tag in tags:
        m = re.search(rf"(<{tag}\b[^>]*>.*?</{tag}>)", train, re.S)
        if not m:
            continue
        block = m.group(1).replace(",", ".")
        if re.search(rf"<{tag}\b", test):
            test = re.sub(rf"<{tag}\b[^>]*>.*?</{tag}>", block, test, count=1, flags=re.S)
    test = set_tag(test, "IsNeedToTrain", "0", 1)
    test_p.write_text(test, encoding="utf-8")


def snapshot_gate(root: Path) -> dict[str, str]:
    train_p = root / "Train" / "Parameters_00.xml"
    test_p = root / "Test" / "Parameters_00.xml"
    csv_path = root / "Test" / "SelectivityLog" / "results.csv"
    L = get_tag(train_p.read_text(encoding="utf-8"), "DendriteLength") or ""
    tipr = get_tag(test_p.read_text(encoding="utf-8"), "TipSynapseResistance") or ""
    thr = get_tag(test_p.read_text(encoding="utf-8"), "FixedLTZThreshold") or ""
    out = {
        "L": L.replace(",", " "),
        "TipR": tipr.replace(",", " "),
        "thr": thr.replace(",", "."),
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
    for r in (r1, r2):
        if r.get("ok_audit") != "1":
            return "REPRO_FAIL"
        if fires(r) != fires(gold):
            return "REPRO_FAIL"
    if L(r1) == L(gold) and r1.get("last_pulse_ok") == "1" and r2.get("last_pulse_ok") == "1":
        return "REPRO_OK"
    # both audit ok + same fires as gold but L/thr drift
    try:
        if int(r1.get("acc") or 0) >= 7 and int(r2.get("acc") or 0) >= 7:
            return "REPRO_SOFT"
    except ValueError:
        pass
    return "REPRO_SOFT"


def prepare_family(family: Family, reps: tuple[int, ...] = (1, 2), *, force: bool = False) -> list[Path]:
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
        pname = f"{family.clone_name}_r{rep}"
        print(f"clone {family.gold.name} -> {dst}")
        rsync_clone(family.gold, dst, pname)
        cold_reset_train(dst / "Train")
        # also cold-ish Test params so TipR not Done tiprmin before merge (gate will set thr)
        tp = dst / "Test" / "Parameters_00.xml"
        if tp.exists():
            t = tp.read_text(encoding="utf-8")
            t = set_tag(t, "IsNeedToTrain", "0", 1)
            t = set_tag(t, "DendriteLength", L_COLD, 1)
            t = set_tag(t, "TipSynapseResistance", TIPR_COLD, 1)
            tp.write_text(t, encoding="utf-8")
        left = dendrite_tips_above_one((dst / "Train" / "Model_00.xml").read_text(encoding="utf-8"))
        if left:
            raise SystemExit(f"prepare assert failed tips>1: {left}")
        print(f"  cold ok L=1 1 1 1 TipR cold neuron tips stripped")
        out.append(dst)
    return out

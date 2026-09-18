"""PHASE12 Wave3+ registries and runners (FS / AsymRm / LtzCal / Phase6).

Imported by phase12_validate.py — keep CLI entrypoints there.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from repro_cold_lib import (
    ROOT,
    Family,
    apply_tiprmin,
    get_tag,
    overlay_neuron,
    patch_tip_exc_r,
    post_train_hygiene,
    read_lengths,
    read_need,
    fix_generator_tip_links,
    set_tag,
    snapshot_gate,
    TIPR_RMIN,
)

if TYPE_CHECKING:
    from phase12_validate import ExpSpec

PHASE9 = ROOT / "SelectivityAsymRm" / "scripts" / "phase9_preinh_bc_gate.py"
FASTSPAN = ROOT / "SelectivityFastSpan"
ASYM = ROOT / "SelectivityAsymRm"
LTZCAL = ROOT / "SelectivityLtzCalibrate" / "AsymRmLtzCal"
PHASE6 = ROOT / "SelectivityPhaseA" / "Phase6"
COPY_CONFIG = ROOT / "SelectivityLtzCalibrate" / "scripts" / "copy_config.sh"
PATCH_LTZ_TEST = ROOT / "SelectivityLtzCalibrate" / "scripts" / "patch_ltz_calibrate_test.py"
FS_MERGE = ROOT / "SelectivityFastSpan" / "scripts" / "merge_train_weights.py"
INVEST_W3 = ROOT / "_repro" / "_invest" / "w3_clone_bak"
FS25_INVEST = ROOT / "_repro" / "_invest" / "fs25_unblock"

GEN_ASYM = "NSPNeuronGenAsymRmD001C1e9"
PRE_ASYM = "NSPNeuronGenPreinh2_5AsymRmD001C1e9"


def _fs(
    exp_id: str,
    span_ms: int,
    neuron: str,
    gold_L: str,
    gold_thr: str,
    train_t: float,
) -> "ExpSpec":
    from phase12_validate import ExpSpec

    return ExpSpec(
        exp_id=exp_id,
        gold=FASTSPAN / exp_id,
        clone_name="FastSpan_" + exp_id.removeprefix("EXP_"),
        span_ms=span_ms,
        train_t=train_t,
        neuron=neuron,
        next_seg=False,
        tipr_recipe="tiprmin",
        metric="ltz_potential_max",
        kind="fastspan",
        gold_L=gold_L,
        gold_thr=gold_thr,
    )


def _asym(
    exp_id: str,
    span_ms: int,
    neuron: str,
    gold_L: str,
    gold_thr: str,
    train_t: float,
) -> "ExpSpec":
    from phase12_validate import ExpSpec

    return ExpSpec(
        exp_id=exp_id,
        gold=ASYM / exp_id,
        clone_name="AsymRm_" + exp_id.removeprefix("EXP_"),
        span_ms=span_ms,
        train_t=train_t,
        neuron=neuron,
        next_seg=False,
        tipr_recipe="tiprmin",
        metric="ltz_potential_max",
        kind="asymrm",
        gold_L=gold_L,
        gold_thr=gold_thr,
    )


WAVE3_FS: dict[str, "ExpSpec"] = {
    s.exp_id: s
    for s in (
        _fs("EXP_span25ms_fast_C1e9", 25, GEN_ASYM, "6 5 4 1", "0.0328372", 180),
        _fs("EXP_span25ms_fast_preinh_C1e9", 25, PRE_ASYM, "6 5 4 1", "0.01563085", 180),
        _fs("EXP_span50ms_fast_preinh_C1e9", 50, PRE_ASYM, "11 10 7 1", "0.0112976", 240),
        _fs("EXP_span100ms_fast_C1e9", 100, GEN_ASYM, "21 18 12 1", "0.01568185", 320),
        _fs("EXP_span100ms_fast_preinh_C1e9", 100, PRE_ASYM, "21 18 12 1", "0.00708053", 320),
    )
}
WAVE3_FS_ORDER = list(WAVE3_FS.keys())

WAVE3_ASYM_COLD: dict[str, "ExpSpec"] = {
    s.exp_id: s
    for s in (
        _asym("EXP_span25ms_packA_gen", 25, GEN_ASYM, "15 12 8 1", "0.00962", 180),
        _asym("EXP_span25ms_packA_preinh", 25, PRE_ASYM, "15 12 8 1", "0.00469", 180),
        _asym("EXP_span50ms_packA_gen", 50, GEN_ASYM, "25 23 15 1", "0.011759", 240),
        _asym("EXP_span50ms_packA_preinh", 50, PRE_ASYM, "25 23 15 1", "0.011759", 240),
        _asym("EXP_span100ms_packA_gen", 100, GEN_ASYM, "52 48 27 1", "0.006681", 320),
        _asym("EXP_span100ms_packA_preinh", 100, PRE_ASYM, "52 48 27 1", "0.006681", 320),
    )
}
WAVE3_ASYM_COLD_ORDER = list(WAVE3_ASYM_COLD.keys())


@dataclass(frozen=True)
class AsymCloneSpec:
    exp_id: str
    gold: Path
    parent_id: str
    span_ms: int
    pack: str  # B | C
    variant: str  # gen | preinh


def _asym_clone(exp_id: str, parent_id: str, span_ms: int, pack: str, variant: str) -> AsymCloneSpec:
    return AsymCloneSpec(
        exp_id=exp_id,
        gold=ASYM / exp_id,
        parent_id=parent_id,
        span_ms=span_ms,
        pack=pack,
        variant=variant,
    )


WAVE3_ASYM_CLONES: dict[str, AsymCloneSpec] = {}
WAVE3_ASYM_CLONE_ORDER: list[str] = []
for _span in (25, 50, 100):
    for _pack in ("B", "C"):
        for _var, _suf in (("gen", "gen"), ("preinh", "preinh_C1e9")):
            _eid = f"EXP_span{_span}ms_pack{_pack}_{_suf}"
            _parent = f"EXP_span{_span}ms_packA_{'gen' if _var == 'gen' else 'preinh'}"
            WAVE3_ASYM_CLONES[_eid] = _asym_clone(_eid, _parent, _span, _pack, _var)
            WAVE3_ASYM_CLONE_ORDER.append(_eid)


def _ltz(exp_id: str, twin_id: str, span_ms: int) -> "ExpSpec":
    from phase12_validate import ExpSpec

    return ExpSpec(
        exp_id=exp_id,
        gold=LTZCAL / exp_id,
        clone_name="LtzCal_" + exp_id.removeprefix("EXP_"),
        span_ms=span_ms,
        train_t=0.0,
        neuron="",
        next_seg=False,
        tipr_recipe="tiprmin",
        metric="ltz_potential_max",
        kind="sync",
        gold_L="",
        gold_thr="",
    )


# twin_id stored via gold sibling naming
WAVE3_LTZCAL: dict[str, "ExpSpec"] = {}
WAVE3_LTZCAL_TWINS: dict[str, str] = {}
WAVE3_LTZCAL_ORDER: list[str] = []
for _span in (25, 50, 100):
    for _var in ("gen", "preinh"):
        _eid = f"EXP_span{_span}ms_packA_{_var}"
        WAVE3_LTZCAL[_eid] = _ltz(_eid, _eid, _span)
        WAVE3_LTZCAL_TWINS[_eid] = _eid
        WAVE3_LTZCAL_ORDER.append(_eid)


def _p6(
    exp_id: str,
    kind: str,
    gold_L: str,
    gold_thr: str,
    neuron: str,
    train_t: float,
    tipr_recipe: str,
) -> "ExpSpec":
    from phase12_validate import ExpSpec

    return ExpSpec(
        exp_id=exp_id,
        gold=PHASE6 / exp_id,
        clone_name="Phase6_" + exp_id.removeprefix("EXP_"),
        span_ms=480,
        train_t=train_t,
        neuron=neuron,
        next_seg=False,
        tipr_recipe=tipr_recipe,  # type: ignore[arg-type]
        metric="ltz_potential_max",
        kind=kind,
        gold_L=gold_L,
        gold_thr=gold_thr,
    )


WAVE4_PHASE6: dict[str, "ExpSpec"] = {
    s.exp_id: s
    for s in (
        _p6("EXP_480_gen_tiprmin", "phase6", "49 41 25 1", "0.016894", "NSPNeuronGen", 600, "tiprmin"),
        _p6("EXP_480_gen_thr_only", "phase6", "49 41 25 1", "0.014386", "NSPNeuronGen", 600, "done_tipr"),
        _p6(
            "EXP_480_preinh250_tiprmin",
            "phase6",
            "51 43 25 1",
            "0.038722",
            "NSPNeuronGenPreinh2_5",
            600,
            "tiprmin",
        ),
        _p6("EXP_480_ltzcal_twin_gen", "sync", "49 41 25 1", "0.016894", "NSPNeuronGen", 0, "tiprmin"),
    )
}
WAVE4_PHASE6_ORDER = list(WAVE4_PHASE6.keys())
WAVE4_PHASE6_COLD_ORDER = [
    "EXP_480_gen_tiprmin",
    "EXP_480_gen_thr_only",
    "EXP_480_preinh250_tiprmin",
]


def as_family(spec: "ExpSpec") -> Family:
    return Family(
        key=spec.exp_id,
        gold=spec.gold,
        clone_name=spec.clone_name,
        train_t=spec.train_t,
        metric=spec.metric,
        kind="fastspan" if spec.kind in ("fastspan", "asymrm", "phase6") else spec.kind,
        span_ms=spec.span_ms,
    )


def post_hygiene_fs_asym(spec: "ExpSpec", root: Path) -> None:
    """TipR@Rmin (unless done_tipr) + merge Train→Test for TimeLearner families."""
    fam = as_family(spec)
    if spec.tipr_recipe == "tiprmin":
        post_train_hygiene(root, fam)
        return
    # thr_only / done_tipr: merge without forcing TipR@Rmin
    train, test = root / "Train", root / "Test"
    tips = read_lengths(train / "Parameters_00.xml")
    tipr = get_tag((train / "Parameters_00.xml").read_text(encoding="utf-8"), "TipSynapseResistance") or ""
    print(f"  keep TipR (no force): {tipr}")
    subprocess.check_call(
        [sys.executable, str(FS_MERGE), str(train / "Parameters_00.xml"), str(test / "Parameters_00.xml")]
    )
    overlay_neuron(train / "Model_00.xml", test / "Model_00.xml")
    mt = (test / "Model_00.xml").read_text(encoding="utf-8").replace(",", ".")
    mt = fix_generator_tip_links(mt, tips)
    (test / "Model_00.xml").write_text(mt, encoding="utf-8")
    for p in (test / "Parameters_00.xml", test / "Model_00.xml"):
        t = p.read_text(encoding="utf-8").replace(",", ".")
        t = set_tag(t, "IsNeedToTrain", "0", 1)
        t = set_tag(t, "UseFixedLTZThreshold", "1", 1)
        t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0", 1)
        if tipr:
            t = set_tag(t, "TipSynapseResistance", tipr, 1)
        p.write_text(t, encoding="utf-8")


def run_gate_fs_asym(spec: "ExpSpec", root: Path, *, dry_run: bool = False) -> None:
    """phase9 silent mid on ltz_potential_max; SIGTERM when CSV n>=8."""
    from phase12_validate import METRICS

    print(f"GATE_FS_ASYM {root} metric={spec.metric} recipe={spec.tipr_recipe}")
    if dry_run:
        return
    post_hygiene_fs_asym(spec, root)
    test_t = "80" if spec.span_ms >= 100 else "40"
    if spec.span_ms >= 480:
        test_t = "80"
    cmd = [
        sys.executable,
        str(PHASE9),
        str(root),
        "--test-t",
        test_t,
        "--metric",
        spec.metric or "ltz_potential_max",
    ]
    log = root / "Test" / "run_phase12_gate_phase9.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(cmd, stdout=log.open("w"), stderr=subprocess.STDOUT)
    csv_path = root / "Test" / "SelectivityLog" / "results.csv"
    tsec = float(test_t)
    hard_deadline = max(tsec, 100.0)
    if spec.span_ms >= 100:
        hard_deadline = max(hard_deadline, 600.0)
    for _ in range(150):
        time.sleep(8)
        if proc.poll() is not None:
            break
        for pid_s in Path("/proc").iterdir():
            if not pid_s.name.isdigit():
                continue
            try:
                cmdl = (pid_s / "cmdline").read_bytes().replace(b"\0", b" ").decode()
            except OSError:
                continue
            if "NeuroModelerConsole" not in cmdl:
                continue
            if str(root / "Test") not in cmdl:
                continue
            if csv_path.exists():
                n = sum(1 for _ in csv_path.open()) - 1
                try:
                    et = int(
                        subprocess.check_output(
                            ["ps", "-o", "etimes=", "-p", pid_s.name], text=True
                        ).strip()
                        or "0"
                    )
                except subprocess.CalledProcessError:
                    et = 0
                if n >= 8 and et > hard_deadline:
                    print(f"  SIGTERM NM pid={pid_s.name} n={n} et={et}")
                    subprocess.call(["kill", "-TERM", pid_s.name])
    try:
        proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        proc.kill()
    if csv_path.exists():
        subprocess.call([sys.executable, str(METRICS), "-v", str(csv_path)])


def _path_hint(gold: Path) -> str:
    try:
        return str(gold.relative_to(ROOT)).split("/")[0]
    except ValueError:
        return gold.parent.name


def run_fs_or_asym_cold(
    spec: "ExpSpec",
    *,
    replicas: int = 2,
    dry_run: bool = False,
    force_prepare: bool = False,
    max_extensions: int = 2,
    fail_status: str = "FAIL",
    no_promote: bool = False,
    no_commit: bool = False,
    commit_prefix: str = "phase12 W3",
) -> str:
    """Soft-cold × replicas → train → pack → phase9 gate → compare/promote."""
    from phase12_validate import (
        bin_commit_paths,
        clone_root,
        pack_root,
        prepare_exp,
        promote_pass,
        run_train,
        write_compare,
        _update_manifest_status,
        MANIFEST,
    )

    reps = tuple(range(1, replicas + 1))
    for rep in reps:
        root = clone_root(spec, rep)
        if not root.exists() or force_prepare:
            prepare_exp(
                spec,
                reps=(rep,),
                force=bool(force_prepare or not root.exists()),
            )
        status = run_train(spec, root, dry_run=dry_run, max_extensions=max_extensions)
        print(f"TRAIN_STATUS={status} r{rep}")
        if status not in ("done", "dry"):
            need = read_need(root / "Train" / "Parameters_00.xml")
            notes = f"train {status} Need={need} r{rep}"
            _update_manifest_status(
                spec.exp_id, fail_status, notes=notes, path_substr=_path_hint(spec.gold)
            )
            write_compare(spec)
            if fail_status == "FAIL_ROOTCAUSE":
                FS25_INVEST.mkdir(parents=True, exist_ok=True)
                cmp = ROOT / "_repro" / spec.clone_name / "COMPARE.md"
                if cmp.exists():
                    shutil.copy2(cmp, FS25_INVEST / "COMPARE.md")
            raise SystemExit(f"train failed: {status}")
        pack_root(root, dry_run=dry_run)
        run_gate_fs_asym(spec, root, dry_run=dry_run)
        print(f"SNAP r{rep}: {snapshot_gate(root)}")
    v = write_compare(spec)
    if v in ("REPRO_OK_EXACT", "REPRO_OK_QUALITY", "REPRO_OK", "REPRO_SOFT"):
        print(f"PASS candidate verdict={v}")
        if not dry_run and not no_promote:
            promote_pass(spec, dry_run=False)
            if not no_commit:
                bin_commit_paths(
                    [MANIFEST, spec.gold],
                    f"{commit_prefix}: VALIDATED {spec.exp_id}",
                )
        return v
    _update_manifest_status(
        spec.exp_id, fail_status, notes=f"verdict={v}", path_substr=_path_hint(spec.gold)
    )
    raise SystemExit(f"compare FAIL {v}")


def _overlay_matrix_from_gen(clone: AsymCloneSpec) -> None:
    """If preinh clone MatrixData stale, overlay from packB/C gen sibling."""
    if clone.variant != "preinh":
        return
    gen_id = f"EXP_span{clone.span_ms}ms_pack{clone.pack}_gen"
    gen_root = ASYM / gen_id
    src = gen_root / "Test" / "MatrixData"
    dst = clone.gold / "Test" / "MatrixData"
    if not src.is_dir():
        print(f"WARN no MatrixData overlay source {src}")
        return
    if dst.exists():
        # only overlay if dst looks empty/missing patterns
        if any(dst.iterdir()):
            print(f"keep existing MatrixData {dst}")
            return
    print(f"overlay MatrixData {src} -> {dst}")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def asym_clone_gate(clone: AsymCloneSpec, *, dry_run: bool = False) -> dict[str, str]:
    from phase12_validate import (
        METRICS,
        MANIFEST,
        _manifest_parent_validated,
        _update_manifest_status,
        _read_thr,
    )

    if not _manifest_parent_validated(clone.parent_id):
        notes = f"parent {clone.parent_id} not VALIDATED"
        _update_manifest_status(clone.exp_id, "DEFERRED_PARENT_FAIL", notes=notes, path_substr="SelectivityAsymRm")
        return {"status": "DEFERRED_PARENT_FAIL", "notes": notes}
    if not clone.gold.exists():
        raise SystemExit(f"missing gold {clone.gold}")

    bak = INVEST_W3 / clone.exp_id
    test = clone.gold / "Test"
    csv_p = test / "SelectivityLog" / "results.csv"
    if not dry_run:
        bak.mkdir(parents=True, exist_ok=True)
        for rel in ("SelectivityLog/results.csv", "Parameters_00.xml", "Model_00.xml"):
            src = test / rel
            if src.exists():
                dst = bak / ("results.csv" if "results" in rel else Path(rel).name)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        print(f"bak -> {bak}")
        _overlay_matrix_from_gen(clone)

    test_t = "80" if clone.span_ms >= 100 else "40"
    cmd = [
        sys.executable,
        str(PHASE9),
        str(clone.gold),
        "--test-t",
        test_t,
        "--metric",
        "ltz_potential_max",
    ]
    print("ASYM_CLONE_GATE", " ".join(cmd))
    if dry_run:
        return {"status": "dry"}
    log = test / "run_phase12_asym_clone_gate.log"
    # SIGTERM watchdog while phase9 runs NM
    proc = subprocess.Popen(cmd, stdout=log.open("w"), stderr=subprocess.STDOUT)
    hard = max(float(test_t), 100.0)
    if clone.span_ms >= 100:
        hard = max(hard, 600.0)
    for _ in range(150):
        time.sleep(8)
        if proc.poll() is not None:
            break
        for pid_s in Path("/proc").iterdir():
            if not pid_s.name.isdigit():
                continue
            try:
                cmdl = (pid_s / "cmdline").read_bytes().replace(b"\0", b" ").decode()
            except OSError:
                continue
            if "NeuroModelerConsole" not in cmdl or str(test) not in cmdl:
                continue
            if csv_p.exists():
                n = sum(1 for _ in csv_p.open()) - 1
                try:
                    et = int(
                        subprocess.check_output(
                            ["ps", "-o", "etimes=", "-p", pid_s.name], text=True
                        ).strip()
                        or "0"
                    )
                except subprocess.CalledProcessError:
                    et = 0
                if n >= 8 and et > hard:
                    print(f"  SIGTERM NM pid={pid_s.name} n={n} et={et}")
                    subprocess.call(["kill", "-TERM", pid_s.name])
    try:
        rc = proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = -1
    print(f"asym-clone-gate rc={rc} log={log}")
    if not csv_p.exists():
        _restore_w3_bak(clone, bak)
        _update_manifest_status(
            clone.exp_id, "FAIL", notes="no results.csv after phase9", path_substr="SelectivityAsymRm"
        )
        raise SystemExit(f"asym-clone FAIL no csv {clone.exp_id}")
    subprocess.call([sys.executable, str(METRICS), "-v", str(csv_p)])
    snap = snapshot_gate(clone.gold)
    try:
        acc = int(snap.get("acc") or 0)
    except ValueError:
        acc = 0
    ok = snap.get("ok_audit") == "1" and acc >= 7
    thr = snap.get("thr") or _read_thr(clone.gold)
    notes = f"phase9 pack{clone.pack}; thr={thr}; acc={acc}; ok_audit={snap.get('ok_audit')}"
    if not ok:
        _restore_w3_bak(clone, bak)
        _update_manifest_status(
            clone.exp_id, "FAIL", notes=notes, path_substr="SelectivityAsymRm"
        )
        raise SystemExit(f"asym-clone FAIL {clone.exp_id} {notes}")
    _update_manifest_status(
        clone.exp_id, "VALIDATED_CLONE", notes=notes, path_substr="SelectivityAsymRm"
    )
    return {"status": "VALIDATED_CLONE", **snap, "notes": notes}


def _restore_w3_bak(clone: AsymCloneSpec, bak: Path) -> None:
    test = clone.gold / "Test"
    for name, dst in (
        ("results.csv", test / "SelectivityLog" / "results.csv"),
        ("Parameters_00.xml", test / "Parameters_00.xml"),
        ("Model_00.xml", test / "Model_00.xml"),
    ):
        src = bak / name
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"restored {dst}")


def sync_ltzcal(exp_id: str, *, dry_run: bool = False) -> str:
    from phase12_validate import (
        METRICS,
        MANIFEST,
        _manifest_parent_validated,
        _update_manifest_status,
        bin_commit_paths,
    )

    twin_id = WAVE3_LTZCAL_TWINS[exp_id]
    if not _manifest_parent_validated(twin_id):
        # accept VALIDATED on AsymRm twin (same id under AsymRm)
        raise SystemExit(f"AsymRm twin {twin_id} not VALIDATED — refuse sync {exp_id}")
    src_train = ASYM / twin_id / "Train"
    dst = LTZCAL / exp_id
    dst_train = dst / "Train"
    dst_test = dst / "Test"
    if not src_train.exists() or not dst_train.exists():
        raise SystemExit(f"missing paths src={src_train} dst={dst_train}")
    print(f"SYNC_LTZCAL {src_train} -> {dst_train} -> {dst_test}")
    if dry_run:
        return "dry"
    subprocess.check_call(["bash", str(COPY_CONFIG), "sync", str(src_train), str(dst_train)])
    subprocess.check_call(["bash", str(COPY_CONFIG), "sync", str(dst_train), str(dst_test)])
    # patch UseFixedLTZ on Test params
    subprocess.check_call(
        [
            sys.executable,
            str(PATCH_LTZ_TEST),
            str(dst_test / "Parameters_00.xml"),
            "--train",
            str(dst_train / "Parameters_00.xml"),
        ]
    )
    # phase9 silent mid on existing LtzCal Test
    spec = WAVE3_LTZCAL[exp_id]
    run_gate_fs_asym(spec, dst, dry_run=False)
    csv_p = dst_test / "SelectivityLog" / "results.csv"
    if csv_p.exists():
        subprocess.call([sys.executable, str(METRICS), "-v", str(csv_p)])
    snap = snapshot_gate(dst)
    try:
        acc = int(snap.get("acc") or 0)
    except ValueError:
        acc = 0
    if snap.get("ok_audit") != "1" or acc < 7:
        notes = f"sync gate fail acc={acc} ok={snap.get('ok_audit')}"
        _update_manifest_status(
            exp_id, "FAIL", notes=notes, path_substr="SelectivityLtzCalibrate"
        )
        raise SystemExit(f"sync-ltzcal FAIL {exp_id} {notes}")
    notes = f"sync from AsymRm; thr={snap.get('thr')}; acc={acc}"
    _update_manifest_status(
        exp_id, "VALIDATED", notes=notes, path_substr="SelectivityLtzCalibrate"
    )
    bin_commit_paths([MANIFEST, dst], f"phase12 W3c: VALIDATED sync {exp_id}")
    return "VALIDATED"


def run_phase6_cold(
    spec: "ExpSpec",
    *,
    dry_run: bool = False,
    force_prepare: bool = False,
    no_commit: bool = False,
) -> str:
    from phase12_validate import (
        MANIFEST,
        bin_commit_paths,
        clone_root,
        pack_root,
        prepare_exp,
        promote_pass,
        run_train,
        write_compare,
        _update_manifest_status,
    )

    # soft×2 with early ARTIFACT_KEEP if Need≠0 (avoid br480 marathon)
    for rep in (1, 2):
        root = clone_root(spec, rep)
        if not root.exists() or force_prepare:
            prepare_exp(spec, reps=(rep,), force=bool(force_prepare or not root.exists()))
        status = run_train(spec, root, dry_run=dry_run, max_extensions=2)
        print(f"TRAIN_STATUS={status} r{rep}")
        if status not in ("done", "dry"):
            need = read_need(root / "Train" / "Parameters_00.xml")
            notes = f"soft-cold Need≠0; gold registry kept; train={status} Need={need} r{rep}"
            _update_manifest_status(
                spec.exp_id,
                "ARTIFACT_KEEP",
                notes=notes,
                path_substr="SelectivityPhaseA",
            )
            write_compare(spec)
            if not dry_run and not no_commit:
                bin_commit_paths([MANIFEST], f"phase12 W4: ARTIFACT_KEEP {spec.exp_id}")
            return "ARTIFACT_KEEP"
        pack_root(root, dry_run=dry_run)
        run_gate_fs_asym(spec, root, dry_run=dry_run)
        print(f"SNAP r{rep}: {snapshot_gate(root)}")
    v = write_compare(spec)
    if v in ("REPRO_OK_EXACT", "REPRO_OK_QUALITY", "REPRO_OK", "REPRO_SOFT"):
        if not dry_run:
            promote_pass(spec, dry_run=False)
            if not no_commit:
                bin_commit_paths(
                    [MANIFEST, spec.gold],
                    f"phase12 W4: VALIDATED {spec.exp_id}",
                )
        return v
    notes = f"verdict={v}; gold kept as ARTIFACT_KEEP"
    _update_manifest_status(
        spec.exp_id, "ARTIFACT_KEEP", notes=notes, path_substr="SelectivityPhaseA"
    )
    if not dry_run and not no_commit:
        bin_commit_paths([MANIFEST], f"phase12 W4: ARTIFACT_KEEP {spec.exp_id}")
    return "ARTIFACT_KEEP"


def sync_phase6_twin(*, dry_run: bool = False, no_commit: bool = False) -> str:
    """EXP_480_ltzcal_twin_gen ← sync from EXP_480_gen_tiprmin (or ARTIFACT_KEEP pair)."""
    from phase12_validate import MANIFEST, bin_commit_paths, _update_manifest_status

    src = PHASE6 / "EXP_480_gen_tiprmin"
    dst = PHASE6 / "EXP_480_ltzcal_twin_gen"
    if not src.exists() or not dst.exists():
        raise SystemExit("missing Phase6 twin paths")
    print(f"SYNC_PHASE6_TWIN {src}/Train -> {dst}")
    if dry_run:
        return "dry"
    subprocess.check_call(
        ["bash", str(COPY_CONFIG), "sync", str(src / "Train"), str(dst / "Train")]
    )
    subprocess.check_call(
        ["bash", str(COPY_CONFIG), "sync", str(dst / "Train"), str(dst / "Test")]
    )
    subprocess.check_call(
        [
            sys.executable,
            str(PATCH_LTZ_TEST),
            str(dst / "Test" / "Parameters_00.xml"),
            "--train",
            str(dst / "Train" / "Parameters_00.xml"),
        ]
    )
    spec = WAVE4_PHASE6["EXP_480_ltzcal_twin_gen"]
    run_gate_fs_asym(spec, dst, dry_run=False)
    snap = snapshot_gate(dst)
    try:
        acc = int(snap.get("acc") or 0)
    except ValueError:
        acc = 0
    status = "VALIDATED" if snap.get("ok_audit") == "1" and acc >= 7 else "ARTIFACT_KEEP"
    notes = f"twin sync; thr={snap.get('thr')}; acc={acc}; ok={snap.get('ok_audit')}"
    _update_manifest_status(
        "EXP_480_ltzcal_twin_gen", status, notes=notes, path_substr="SelectivityPhaseA"
    )
    if not no_commit:
        bin_commit_paths([MANIFEST, dst], f"phase12 W4: {status} twin sync")
    return status


# ----- CLI handlers (bound from phase12_validate.main) -----


def cmd_list_wave3(_args: argparse.Namespace) -> None:
    print("=== WAVE3_FS ===")
    for eid in WAVE3_FS_ORDER:
        s = WAVE3_FS[eid]
        print(f"{eid}\tspan={s.span_ms}\tL={s.gold_L}\tthr={s.gold_thr}\ttrain_t={s.train_t}")
    print("=== WAVE3_ASYM_COLD ===")
    for eid in WAVE3_ASYM_COLD_ORDER:
        s = WAVE3_ASYM_COLD[eid]
        print(f"{eid}\tspan={s.span_ms}\tL={s.gold_L}\tthr={s.gold_thr}")
    print("=== WAVE3_ASYM_CLONES ===")
    for eid in WAVE3_ASYM_CLONE_ORDER:
        c = WAVE3_ASYM_CLONES[eid]
        print(f"{eid}\tparent={c.parent_id}\tpack={c.pack}")
    print("=== WAVE3_LTZCAL ===")
    for eid in WAVE3_LTZCAL_ORDER:
        print(f"{eid}\ttwin=AsymRm/{WAVE3_LTZCAL_TWINS[eid]}")
    print("=== WAVE4_PHASE6 ===")
    for eid in WAVE4_PHASE6_ORDER:
        s = WAVE4_PHASE6[eid]
        print(f"{eid}\tkind={s.kind}\tL={s.gold_L}\tthr={s.gold_thr}\trecipe={s.tipr_recipe}")


def cmd_run_fs(args: argparse.Namespace) -> None:
    spec = WAVE3_FS[args.exp]
    fail_st = "FAIL_ROOTCAUSE" if args.exp == "EXP_span25ms_fast_C1e9" else "FAIL"
    run_fs_or_asym_cold(
        spec,
        replicas=args.replicas,
        dry_run=args.dry_run,
        force_prepare=args.force_prepare,
        fail_status=fail_st,
        no_promote=args.no_promote,
        no_commit=args.no_commit,
        commit_prefix="phase12 W3a" if args.exp == "EXP_span25ms_fast_C1e9" else "phase12 W3b",
    )


def cmd_run_fs_all(args: argparse.Namespace) -> None:
    from phase12_validate import _manifest_parent_validated

    # only if FS25 unblocked (VALIDATED)
    if not args.force and not _manifest_parent_validated("EXP_span25ms_fast_C1e9"):
        print("FS25 not VALIDATED — refuse run-fs-all (use --force to override)")
        raise SystemExit("BLOCKED_FS: need FS25 unblock first")
    started = False if args.from_exp else True
    for eid in WAVE3_FS_ORDER:
        if not started:
            if eid == args.from_exp:
                started = True
            else:
                continue
        print(f"\n===== FS {eid} =====")
        ns = argparse.Namespace(
            exp=eid,
            replicas=args.replicas,
            dry_run=args.dry_run,
            force_prepare=args.force_prepare,
            no_promote=args.no_promote,
            no_commit=args.no_commit,
        )
        try:
            cmd_run_fs(ns)
        except SystemExit as e:
            print(f"FAIL {eid}: {e}")
            if args.stop_on_fail:
                raise


def cmd_run_asym_packa(args: argparse.Namespace) -> None:
    spec = WAVE3_ASYM_COLD[args.exp]
    run_fs_or_asym_cold(
        spec,
        replicas=args.replicas,
        dry_run=args.dry_run,
        force_prepare=args.force_prepare,
        fail_status="FAIL",
        no_promote=args.no_promote,
        no_commit=args.no_commit,
        commit_prefix="phase12 W3b",
    )


def cmd_run_asym_packa_all(args: argparse.Namespace) -> None:
    started = False if args.from_exp else True
    for eid in WAVE3_ASYM_COLD_ORDER:
        if not started:
            if eid == args.from_exp:
                started = True
            else:
                continue
        print(f"\n===== ASYM_PACKA {eid} =====")
        ns = argparse.Namespace(
            exp=eid,
            replicas=args.replicas,
            dry_run=args.dry_run,
            force_prepare=args.force_prepare,
            no_promote=args.no_promote,
            no_commit=args.no_commit,
        )
        try:
            cmd_run_asym_packa(ns)
        except SystemExit as e:
            print(f"FAIL {eid}: {e}")
            if args.stop_on_fail:
                raise


def cmd_asym_clone_gate(args: argparse.Namespace) -> None:
    from phase12_validate import MANIFEST, bin_commit_paths

    clone = WAVE3_ASYM_CLONES[args.exp]
    result = asym_clone_gate(clone, dry_run=args.dry_run)
    if (
        not args.dry_run
        and not args.no_commit
        and result.get("status") == "VALIDATED_CLONE"
    ):
        bin_commit_paths(
            [MANIFEST, clone.gold / "Test"],
            f"phase12 W3b: VALIDATED_CLONE {clone.exp_id}",
        )


def cmd_run_asym_clones(args: argparse.Namespace) -> None:
    from phase12_validate import MANIFEST, bin_commit_paths

    started = False if args.from_exp else True
    for eid in WAVE3_ASYM_CLONE_ORDER:
        if not started:
            if eid == args.from_exp:
                started = True
            else:
                continue
        print(f"\n===== ASYM_CLONE {eid} =====")
        clone = WAVE3_ASYM_CLONES[eid]
        try:
            result = asym_clone_gate(clone, dry_run=args.dry_run)
        except SystemExit as e:
            print(f"FAIL {eid}: {e}")
            if args.stop_on_fail:
                raise
            continue
        if (
            not args.dry_run
            and not args.no_commit
            and result.get("status") == "VALIDATED_CLONE"
        ):
            bin_commit_paths(
                [MANIFEST, clone.gold / "Test"],
                f"phase12 W3b: VALIDATED_CLONE {eid}",
            )


def cmd_sync_ltzcal(args: argparse.Namespace) -> None:
    sync_ltzcal(args.exp, dry_run=args.dry_run)


def cmd_sync_ltzcal_all(args: argparse.Namespace) -> None:
    for eid in WAVE3_LTZCAL_ORDER:
        print(f"\n===== SYNC_LTZCAL {eid} =====")
        try:
            sync_ltzcal(eid, dry_run=args.dry_run)
        except SystemExit as e:
            print(f"FAIL {eid}: {e}")
            if args.stop_on_fail:
                raise


def cmd_run_phase6(args: argparse.Namespace) -> None:
    if args.exp == "EXP_480_ltzcal_twin_gen":
        sync_phase6_twin(dry_run=args.dry_run, no_commit=args.no_commit)
        return
    run_phase6_cold(
        WAVE4_PHASE6[args.exp],
        dry_run=args.dry_run,
        force_prepare=args.force_prepare,
        no_commit=args.no_commit,
    )


def cmd_run_phase6_all(args: argparse.Namespace) -> None:
    for eid in WAVE4_PHASE6_COLD_ORDER:
        print(f"\n===== PHASE6 {eid} =====")
        ns = argparse.Namespace(
            exp=eid,
            dry_run=args.dry_run,
            force_prepare=args.force_prepare,
            no_commit=args.no_commit,
        )
        try:
            cmd_run_phase6(ns)
        except SystemExit as e:
            print(f"FAIL {eid}: {e}")
            if args.stop_on_fail:
                raise
    print("\n===== PHASE6 twin sync =====")
    sync_phase6_twin(dry_run=args.dry_run, no_commit=args.no_commit)


def register_wave3_cli(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("list-wave3")
    p.set_defaults(func=cmd_list_wave3)

    p = sub.add_parser("run-fs")
    p.add_argument("--exp", required=True, choices=WAVE3_FS_ORDER)
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-prepare", action="store_true")
    p.add_argument("--no-promote", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.set_defaults(func=cmd_run_fs)

    p = sub.add_parser("run-fs-all")
    p.add_argument("--from", dest="from_exp", default=None, choices=WAVE3_FS_ORDER)
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-prepare", action="store_true")
    p.add_argument("--no-promote", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.add_argument("--force", action="store_true", help="run even if FS25 not VALIDATED")
    p.set_defaults(func=cmd_run_fs_all)

    p = sub.add_parser("run-asym-packa")
    p.add_argument("--exp", required=True, choices=WAVE3_ASYM_COLD_ORDER)
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-prepare", action="store_true")
    p.add_argument("--no-promote", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.set_defaults(func=cmd_run_asym_packa)

    p = sub.add_parser("run-asym-packa-all")
    p.add_argument("--from", dest="from_exp", default=None, choices=WAVE3_ASYM_COLD_ORDER)
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-prepare", action="store_true")
    p.add_argument("--no-promote", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.set_defaults(func=cmd_run_asym_packa_all)

    p = sub.add_parser("asym-clone-gate")
    p.add_argument("--exp", required=True, choices=WAVE3_ASYM_CLONE_ORDER)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.set_defaults(func=cmd_asym_clone_gate)

    p = sub.add_parser("run-asym-clones")
    p.add_argument("--from", dest="from_exp", default=None, choices=WAVE3_ASYM_CLONE_ORDER)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.set_defaults(func=cmd_run_asym_clones)

    p = sub.add_parser("sync-ltzcal")
    p.add_argument("--exp", required=True, choices=WAVE3_LTZCAL_ORDER)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_sync_ltzcal)

    p = sub.add_parser("sync-ltzcal-all")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.set_defaults(func=cmd_sync_ltzcal_all)

    p = sub.add_parser("run-phase6")
    p.add_argument("--exp", required=True, choices=WAVE4_PHASE6_ORDER)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-prepare", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.set_defaults(func=cmd_run_phase6)

    p = sub.add_parser("run-phase6-all")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-prepare", action="store_true")
    p.add_argument("--no-commit", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.set_defaults(func=cmd_run_phase6_all)

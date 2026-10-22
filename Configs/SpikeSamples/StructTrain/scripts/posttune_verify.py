#!/usr/bin/env python3
"""PostTune verification: soft-cold → train → snapshot (no tiprmin) → gate → compare gold.

A16: run isolation, numeric TipR vs own snapshot, separated Train/Test flags,
strict gate rc, slog abort before prune continue, non-zero exit on FAIL.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Sequence

ROOT = Path(__file__).resolve().parents[1]
NMSDK_ROOT = Path(__file__).resolve().parents[5]
PROVENANCE_SOURCE_REL = (
    "Libraries/Nmsdk-PulseLib/Core/NPatternResponseAnalyzer.cpp",
    "Libraries/Nmsdk-PulseLib/Core/NPatternResponseAnalyzer.h",
    "Libraries/Nmsdk-PulseLib/Core/NNeuronPostTrainTune.cpp",
    "Libraries/Nmsdk-PulseLib/Core/NNeuronPostTrainTune.h",
    "Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp",
    "Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.h",
    "Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearnerBranch.cpp",
    "Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearnerBranch.h",
    "Libraries/Nmsdk-PulseLib/Core/NDatasetBase.cpp",
    "Libraries/Nmsdk-PulseLib/Core/NDatasetBase.h",
    "Rdk/GUI/Qt/UModernDiagramLinkRouter.cpp",
    "App/NeuroModelerConsole/main.cpp",
    "Bin/Configs/SpikeSamples/StructTrain/scripts/posttune_verify.py",
    "Bin/Configs/SpikeSamples/StructTrain/scripts/run_timelearner_matrix_queue.py",
    "Bin/Configs/SpikeSamples/StructTrain/scripts/timelearner_matrix.py",
    "Bin/Configs/SpikeSamples/StructTrain/scripts/repro_cold_lib.py",
    "Bin/Configs/SpikeSamples/StructTrain/scripts/selectivity_metrics.py",
    "Bin/Configs/SpikeSamples/StructTrain/SelectivityBranch/scripts/phase8_tiprmin_gate.py",
    "Bin/Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts/phase9_preinh_bc_gate.py",
)

# Inputs allowed into a clean workdir (archive flags/CSV/live stay out).
ALLOWLIST_INPUTS = (
    "Model_00.xml",
    "Parameters_00.xml",
    "Project.ini",
    "Interface.xml",
)
ALLOWLIST_OPTIONAL_GLOBS = (
    "Matrix*.xml",
    "Pack*.xml",
    "*.pack",
)
sys.path.insert(0, str(ROOT / "scripts"))
from repro_cold_lib import (  # noqa: E402
    DEFAULT_AUTOSAVE_MODEL_S,
    NM,
    TIPR_COLD,
    apply_branch_segment_rm_profile_to_train,
    assert_disk_for_train,
    free_gib,
    get_tag,
    set_tag,
    soft_cold_reset_train,
    tipr_looks_posttuned,
    write_cold_reset_contract,
)

PHASE8 = ROOT / "SelectivityBranch" / "scripts" / "phase8_tiprmin_gate.py"
PHASE9 = ROOT / "SelectivityAsymRm" / "scripts" / "phase9_preinh_bc_gate.py"
METRICS = ROOT / "scripts" / "selectivity_metrics.py"
OUT = ROOT / "_repro" / "POSTTUNE_VERIFY_RESULT.md"
RUNS_ROOT = Path(
    os.environ.get("TIMELEARNER_MATRIX_RUNS_ROOT", str(ROOT / "_repro" / "runs"))
).expanduser().resolve()

CASES = {
    "br25_on": {
        "root": ROOT / "SelectivityBranch" / "EXP_br_span25_packA_gen_C1e9_posttune",
        "gold": ROOT / "SelectivityBranch" / "EXP_br_span25_packA_gen_C1e9",
        "train_t": 320.0,
        "span_ms": 25,
        "kind": "branch",
        "expect_tipr": "canon",
        "skip_tipr_mid": True,
    },
    "br25_off": {
        "root": ROOT / "SelectivityBranch" / "EXP_br_span25_packA_gen_C1e9_posttune_off",
        "gold": ROOT / "SelectivityBranch" / "EXP_br_span25_packA_gen_C1e9",
        "train_t": 320.0,
        "span_ms": 25,
        "kind": "branch",
        "expect_tipr": "legacy",
        "expect_fires": "10110000",
        "skip_tipr_mid": False,
    },
    "asym25": {
        "root": ROOT / "SelectivityAsymRm" / "EXP_span25ms_packA_gen_posttune",
        "gold": ROOT / "SelectivityAsymRm" / "EXP_span25ms_packA_gen",
        "train_t": 160.0,
        "span_ms": 25,
        "kind": "asym",
        "expect_tipr": "flat",
        "skip_tipr_mid": True,
    },
    "br100_keep": {
        "root": ROOT / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9_posttune_keep",
        "gold": ROOT / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9",
        "train_t": 640.0,
        "span_ms": 100,
        "kind": "branch",
        "expect_tipr": "keep",
        "skip_tipr_mid": True,
    },
    "br100_search": {
        "root": ROOT / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9_posttune_search",
        "gold": ROOT / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9",
        "train_t": 2400.0,
        "span_ms": 100,
        "kind": "branch",
        "expect_tipr": "search",
        "skip_tipr_mid": True,
        "expect_fires": "10000000",
    },
    "asym50": {
        "root": ROOT / "SelectivityAsymRm" / "EXP_span50ms_packA_gen_posttune",
        "gold": ROOT / "SelectivityAsymRm" / "EXP_span50ms_packA_gen",
        # D2.1: 320s left Need=1 / no Train flag (Finalize not reached). Bump with provenance note.
        "train_t": 640.0,
        "span_ms": 50,
        "kind": "asym",
        "expect_tipr": "canon",
        "skip_tipr_mid": True,
    },
    "phase6_480": {
        "root": ROOT / "SelectivityPhaseA" / "Phase6" / "EXP_480_gen_posttune",
        "gold": ROOT / "SelectivityPhaseA" / "Phase6" / "EXP_480_gen_tiprmin",
        "train_t": 900.0,
        "span_ms": 480,
        "kind": "phase6",
        "expect_tipr": "canon",
        "skip_tipr_mid": True,
        "expect_fires": "10000010",
    },
}

# SoftCold wave C1/C2: packA/parent archives as templates (clean workdir via prepare_clean_case).
# Excludes canons already SoftCold-tested on HEAD (br25_on/off, br100_*, asym25/50, phase6_480).
def _case(
    root: Path,
    *,
    train_t: float,
    span_ms: int,
    kind: str,
    expect_tipr: str = "canon",
    skip_tipr_mid: bool = True,
    expect_fires: str | None = None,
    gold: Path | None = None,
) -> dict:
    d: dict = {
        "root": root,
        "gold": gold or root,
        "train_t": train_t,
        "span_ms": span_ms,
        "kind": kind,
        "expect_tipr": expect_tipr,
        "skip_tipr_mid": skip_tipr_mid,
    }
    if expect_fires is not None:
        d["expect_fires"] = expect_fires
    return d


BR = ROOT / "SelectivityBranch"
ASYM = ROOT / "SelectivityAsymRm"
P6 = ROOT / "SelectivityPhaseA" / "Phase6"
FS = ROOT / "SelectivityFastSpan"
LTZ = ROOT / "SelectivityLtzCalibrate" / "AsymRmLtzCal"
PA = ROOT / "SelectivityPhaseA"
PSI = ROOT / "SelectivityPresynapticInhib"

CASES.update(
    {
        # --- C1 Branch ---
        "br50_gen": _case(BR / "EXP_br_span50_packA_gen_C1e9", train_t=320, span_ms=50, kind="branch"),
        "br25_preinh": _case(BR / "EXP_br_span25_packA_preinh_C1e9", train_t=320, span_ms=25, kind="branch"),
        "br50_preinh": _case(BR / "EXP_br_span50_packA_preinh_C1e9", train_t=320, span_ms=50, kind="branch"),
        "br100_preinh": _case(BR / "EXP_br_span100_packA_preinh_C1e9", train_t=640, span_ms=100, kind="branch"),
        "br25_nextseg": _case(BR / "EXP_br_span25_packA_nextseginh_C1e9", train_t=320, span_ms=25, kind="branch"),
        "br50_nextseg": _case(BR / "EXP_br_span50_packA_nextseginh_C1e9", train_t=320, span_ms=50, kind="branch"),
        "br100_nextseg": _case(BR / "EXP_br_span100_packA_nextseginh_C1e9", train_t=640, span_ms=100, kind="branch"),
        "br480_tiprmin": _case(BR / "EXP_br480_tiprmin", train_t=900, span_ms=480, kind="branch"),
        "br480_nextseg": _case(BR / "EXP_br480_nextseginh_tiprmin", train_t=900, span_ms=480, kind="branch"),
        "br480_preinh": _case(BR / "EXP_br480_preinh250_tiprmin", train_t=900, span_ms=480, kind="branch"),
        # --- C1 AsymRm ---
        "asym25_preinh": _case(ASYM / "EXP_span25ms_packA_preinh", train_t=160, span_ms=25, kind="asym"),
        "asym50_preinh": _case(ASYM / "EXP_span50ms_packA_preinh", train_t=640, span_ms=50, kind="asym"),
        "asym100_gen": _case(ASYM / "EXP_span100ms_packA_gen", train_t=640, span_ms=100, kind="asym"),
        "asym100_preinh": _case(ASYM / "EXP_span100ms_packA_preinh", train_t=640, span_ms=100, kind="asym"),
        # --- C1 Phase6 ---
        "phase6_thr_only": _case(P6 / "EXP_480_gen_thr_only", train_t=900, span_ms=480, kind="phase6"),
        "phase6_preinh250": _case(P6 / "EXP_480_preinh250_tiprmin", train_t=900, span_ms=480, kind="phase6"),
        "phase6_ltzcal_twin": _case(P6 / "EXP_480_ltzcal_twin_gen", train_t=900, span_ms=480, kind="phase6"),
        # --- C1 FastSpan ---
        "fs25_gen": _case(FS / "EXP_span25ms_fast_C1e9", train_t=160, span_ms=25, kind="asym"),
        "fs25_preinh": _case(FS / "EXP_span25ms_fast_preinh_C1e9", train_t=160, span_ms=25, kind="asym"),
        "fs50_preinh": _case(FS / "EXP_span50ms_fast_preinh_C1e9", train_t=320, span_ms=50, kind="asym"),
        "fs100_gen": _case(FS / "EXP_span100ms_fast_C1e9", train_t=640, span_ms=100, kind="asym"),
        "fs100_preinh": _case(FS / "EXP_span100ms_fast_preinh_C1e9", train_t=640, span_ms=100, kind="asym"),
        # --- C2 LtzCal ---
        "ltz25_gen": _case(LTZ / "EXP_span25ms_packA_gen", train_t=160, span_ms=25, kind="asym"),
        "ltz25_preinh": _case(LTZ / "EXP_span25ms_packA_preinh", train_t=160, span_ms=25, kind="asym"),
        "ltz50_gen": _case(LTZ / "EXP_span50ms_packA_gen", train_t=640, span_ms=50, kind="asym"),
        "ltz50_preinh": _case(LTZ / "EXP_span50ms_packA_preinh", train_t=640, span_ms=50, kind="asym"),
        "ltz100_gen": _case(LTZ / "EXP_span100ms_packA_gen", train_t=640, span_ms=100, kind="asym"),
        "ltz100_preinh": _case(LTZ / "EXP_span100ms_packA_preinh", train_t=640, span_ms=100, kind="asym"),
        # --- C2 PhaseA / TN ---
        "pa00_baseline": _case(PA / "EXP00_baseline", train_t=640, span_ms=480, kind="asym"),
        "pa01_ltz_sweep": _case(PA / "EXP01_ltz_threshold_sweep", train_t=160, span_ms=480, kind="asym"),
        "pa02_ltzone_avg": _case(PA / "EXP02_ltzone_average_mode", train_t=160, span_ms=480, kind="asym"),
        "pa06_ltzone_int": _case(PA / "EXP06_ltzone_integration", train_t=160, span_ms=480, kind="asym"),
        "tn_classic": _case(ROOT / "TimeNeuronTimeLearner", train_t=640, span_ms=480, kind="asym"),
        # --- C2 PSI (sample of 9) ---
        "psi01_050": _case(PSI / "EXP01_preinh_050", train_t=640, span_ms=480, kind="asym"),
        "psi14_260": _case(PSI / "EXP14_preinh_260", train_t=160, span_ms=480, kind="asym"),
        "psi15_270": _case(PSI / "EXP15_preinh_270", train_t=160, span_ms=480, kind="asym"),
        "psi21_100": _case(PSI / "EXP21_span100ms_preinh250", train_t=640, span_ms=100, kind="asym"),
        "psi31_200": _case(PSI / "EXP31_span200ms_preinh250", train_t=640, span_ms=200, kind="asym"),
        "psi32_300": _case(PSI / "EXP32_span300ms_baseline", train_t=640, span_ms=300, kind="asym"),
        "psi33_300": _case(PSI / "EXP33_span300ms_preinh250", train_t=640, span_ms=300, kind="asym"),
        "psi34_400": _case(PSI / "EXP34_span400ms_baseline", train_t=900, span_ms=400, kind="asym"),
        "psi35_400": _case(PSI / "EXP35_span400ms_preinh250", train_t=900, span_ms=400, kind="asym"),
    }
)


@dataclass
class PostTuneSalvage:
    mid: str | None = None
    tipr_s: str | None = None
    tipr_snapshot: str | None = None
    lens_s: str | None = None
    source: str = "none"


@dataclass
class GateResult:
    fires: str
    metrics_line: str
    rc: int | None
    csv_mtime: float | None
    gate_started: float
    ok: bool | None
    fail_reason: str = ""
    evaluated: bool = True
    quality_ok: bool | None = None
    target_detected: bool | None = None
    quality_metrics: dict[str, Any] = field(default_factory=dict)
    external_classifier_evaluated: bool = True
    test_mid_quality: str = "not_available"
    test_mid_gap: str = ""
    test_mid_result: str = ""
    diagnostic_evaluations: dict[str, Any] = field(default_factory=dict)
    commands: list[list[str]] = field(default_factory=list)


@dataclass
class PhaseMeta:
    train: dict[str, str] = field(default_factory=dict)
    test: dict[str, str] = field(default_factory=dict)

    @property
    def search_reverted(self) -> bool:
        return self.train.get("search_reverted") == "1"


def snap_params(params: Path) -> dict[str, str]:
    t = params.read_text(encoding="utf-8") if params.exists() else ""
    keys = (
        "TipSynapseResistance",
        "FixedLTZThreshold",
        "ResistanceMin",
        "IsNeedToTrain",
        "EnablePostTrainTuning",
        "PostTrainTipResistanceMode",
        "PostTrainTuneComplete",
        "TrainingPhase",
        "DendriteLength",
    )
    return {k: (get_tag(t, k) or "") for k in keys}


def _latest_stat_dir(train: Path) -> Path | None:
    slog = train / "StatisticLog"
    if not slog.is_dir():
        return None
    dirs = [p for p in slog.iterdir() if p.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.stat().st_mtime)


def _last_trace_vector(stat_dir: Path, name: str) -> list[str] | None:
    path = stat_dir / f"NeuronTimeLearnerBranch.{name}.txt"
    if not path.exists():
        path = stat_dir / f"NeuronTimeLearner.{name}.txt"
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    if not lines:
        return None
    parts = lines[-1].replace(",", ".").split()
    if len(parts) < 3:
        return None
    return parts[2:]


def flush_current_train_flag(train: Path) -> str:
    """Sync Parameters/Model from THIS workdir's Train flag when -S lagged.

    Console SaveProject runs only after IsCalcFinished (A15). Early stop after
    posttune_complete.flag often leaves TipR/Need stale in XML while the flag
    already has Finalize's TipSynapseResistance (T3 H2). This is not archive
    salvage: the flag must exist in the current clean workdir.
    """
    flag = train / "posttune_complete.flag"
    if not flag.exists():
        return "none"
    meta = parse_flag_file(flag)
    if not meta.get("result") and not meta.get("tipr"):
        return "none"
    tipr = meta.get("tipr")
    mid = meta.get("FixedLTZ") or meta.get("mid")
    changed = False
    for rel in ("Parameters_00.xml", "Model_00.xml"):
        p = train / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        if tipr:
            tipr_xml = tipr.replace("+", "")
            t = set_tag(t, "TipSynapseResistance", tipr_xml, 1)
            changed = True
        if meta.get("result") is not None:
            t = set_tag(t, "IsNeedToTrain", "0", 1)
            changed = True
        if mid:
            t = set_tag(t, "FixedLTZThreshold", mid, 1)
            t = set_tag(t, "LTZThreshold", mid, 1)
            changed = True
        p.write_text(t, encoding="utf-8")
    return "flag_flush" if changed else "none"


def parse_flag_file(path: Path) -> dict[str, str]:
    """Line-aware flag parser: tipr=/tipr_snapshot=/metrics= take rest-of-line."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("tipr_snapshot="):
            out["tipr_snapshot"] = s.split("=", 1)[1].strip()
            continue
        if s.startswith("tipr="):
            out["tipr"] = s.split("=", 1)[1].strip()
            continue
        if s.startswith("metrics="):
            out["metrics"] = s.split("=", 1)[1].strip()
            continue
        for tok in s.split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                out[k] = v
    return out


def parse_flag_meta(flag: Path) -> dict[str, str]:
    """Backward-compatible alias."""
    return parse_flag_file(flag)


def load_phase_meta(train_flag: Path, test_flag: Path) -> PhaseMeta:
    return PhaseMeta(train=parse_flag_file(train_flag), test=parse_flag_file(test_flag))


def parse_tipr_vec(s: str, *, n: int = 4) -> list[float] | None:
    if not s:
        return None
    parts = s.replace(",", " ").split()
    if len(parts) < n:
        return None
    try:
        return [float(x) for x in parts[:n]]
    except ValueError:
        return None


def tipr_close(
    a: Sequence[float],
    b: Sequence[float],
    *,
    rtol: float = 1e-4,
    atol: float = 1.0,
) -> bool:
    if len(a) != len(b) or not a:
        return False
    for ai, bi in zip(a, b):
        if not math.isfinite(ai) or not math.isfinite(bi):
            return False
        if abs(ai - bi) > max(atol, rtol * abs(bi)):
            return False
    return True


def tipr_vs_snapshot(
    final_tipr: str,
    snapshot_tipr: str,
    *,
    search_reverted: bool,
) -> str:
    """Numeric compare vs OWN Train snapshot (not keep-clone)."""
    a = parse_tipr_vec(final_tipr)
    b = parse_tipr_vec(snapshot_tipr)
    if a is None or b is None:
        return "unknown"
    if tipr_close(a, b):
        return "same_reverted" if search_reverted else "same_FAIL"
    if search_reverted:
        return "diff_after_revert"
    return "applied_best"


def tipr_vs_keep(tipr: str, keep_tipr: str, search_reverted: bool) -> str:
    """Informational keep-clone compare (numeric). Not a V5b PASS criterion."""
    return tipr_vs_snapshot(tipr, keep_tipr, search_reverted=search_reverted)


def _run_uniq() -> str:
    """PID+uuid suffix so parallel SoftCold workers never collide on same UTC second."""
    return f"{os.getpid()}_{uuid.uuid4().hex[:8]}"


def make_run_dir(case: str, root: Path | None = None) -> Path:
    base = root if root is not None else RUNS_ROOT
    utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    d = base / f"{case}_{utc}_{_run_uniq()}"
    (d / "Train").mkdir(parents=True, exist_ok=True)
    (d / "Test").mkdir(parents=True, exist_ok=True)
    return d


def strip_runtime_artifacts(side: Path) -> None:
    """Remove flags/live/logs that must not seed a cold run."""
    for name in ("posttune_complete.flag", "posttune_tipr_live.txt"):
        p = side / name
        if p.exists():
            p.unlink()
    for dname in ("SelectivityLog", "StatisticLog", "EventsLog"):
        d = side / dname
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)


def sha256_file(path: Path | str) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_paths(paths: Sequence[Path | str]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for path in paths:
        p = Path(path)
        key = str(p)
        try:
            key = str(p.resolve().relative_to(NMSDK_ROOT))
        except ValueError:
            key = p.name
        out[key] = sha256_file(p)
    return out


def prepare_clean_case(case_name: str, archive_root: Path) -> Path:
    """Copy allowlisted inputs into a fresh workdir; archive flags/CSV stay out."""
    utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    work = RUNS_ROOT / f"{case_name}_{utc}_{_run_uniq()}_work"
    manifest: dict[str, Any] = {
        "case": case_name,
        "archive_root": str(archive_root),
        "utc": utc,
        "copied": [],
    }
    for side in ("Train", "Test"):
        src_side = archive_root / side
        dst_side = work / side
        dst_side.mkdir(parents=True, exist_ok=True)
        if not src_side.is_dir():
            continue
        for rel in ALLOWLIST_INPUTS:
            src = src_side / rel
            if src.is_file():
                shutil.copy2(src, dst_side / rel)
                manifest["copied"].append(
                    {
                        "side": side,
                        "rel": rel,
                        "sha256": sha256_file(dst_side / rel),
                    }
                )
        for pattern in ALLOWLIST_OPTIONAL_GLOBS:
            for src in src_side.glob(pattern):
                if src.is_file():
                    shutil.copy2(src, dst_side / src.name)
                    manifest["copied"].append(
                        {
                            "side": side,
                            "rel": src.name,
                            "sha256": sha256_file(dst_side / src.name),
                        }
                    )
        strip_runtime_artifacts(dst_side)
    work.mkdir(parents=True, exist_ok=True)
    (work / "inputs_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return work


def suspend_statistic_matrix_writes(model_path: Path) -> int:
    """Disable per-step file writes by UStatisticDoubleMatrix observers in a copy."""
    if not model_path.is_file():
        return 0
    text = model_path.read_text(encoding="utf-8")
    component_re = re.compile(
        r'(<StatisticDoubleMatrix\b[^>]*>.*?</StatisticDoubleMatrix>)', re.DOTALL
    )
    updated = 0
    components = component_re.findall(text)
    for component in components:
        changed = component
        for tag, value in (
            ("Activity", "0"),
            ("ManualModeEnabled", "1"),
            ("ManualModeSwitch", "0"),
        ):
            changed, count = re.subn(
                rf'(<{tag}\b[^>]*>)[^<]*(</{tag}>)',
                lambda m, v=value: m.group(1) + v + m.group(2),
                changed,
                count=1,
            )
            if count != 1:
                raise ValueError(
                    f"expected one {tag} property in UStatisticDoubleMatrix in {model_path}"
                )
        text = text.replace(component, changed, 1)
        updated += 1
    if components and updated != len(components):
        raise ValueError(
            f"updated {updated}/{len(components)} UStatisticDoubleMatrix writers in {model_path}"
        )
    model_path.write_text(text, encoding="utf-8")
    return updated


def tipr_weights_identity(
    train: Path,
    *,
    params_source: str = "none",
) -> dict[str, Any]:
    """TipR identity block for provenance (R06/A16): params vs flag + sha256."""
    tipr_params = ""
    length_params = ""
    params = train / "Parameters_00.xml"
    if params.exists():
        snap = snap_params(params)
        tipr_params = snap.get("TipSynapseResistance") or ""
        length_params = snap.get("DendriteLength") or snap.get("Length") or ""
    tipr_flag = ""
    flag = train / "posttune_complete.flag"
    if flag.exists():
        meta = parse_flag_file(flag)
        tipr_flag = (meta.get("tipr") or "").replace("+", "")
    tipr_sha = None
    if tipr_params:
        tipr_sha = hashlib.sha256(tipr_params.encode("utf-8")).hexdigest()
    match = False
    if tipr_params and tipr_flag:
        vp = parse_tipr_vec(tipr_params)
        vf = parse_tipr_vec(tipr_flag)
        match = vp is not None and vf is not None and tipr_close(vp, vf)
    elif tipr_params and not tipr_flag and params_source == "nm_save":
        match = True
    return {
        "tipr_params": tipr_params,
        "tipr_flag": tipr_flag,
        "tipr_sha256": tipr_sha,
        "length_params": length_params,
        "flag_params_tipr_match": bool(match),
        "params_source": params_source,
    }


def build_provenance(
    work: Path,
    *,
    case: str,
    run_id: str,
    config_sha_before: dict[str, str | None] | None = None,
    params_source: str = "none",
) -> dict[str, Any]:
    source_paths = [NMSDK_ROOT / rel for rel in PROVENANCE_SOURCE_REL]
    gitlinks: dict[str, str | None] = {}
    for name in ("Libraries/Nmsdk-PulseLib", "Bin", "Rdk"):
        p = NMSDK_ROOT / name
        head = None
        try:
            head = subprocess.check_output(
                ["git", "-C", str(p), "rev-parse", "HEAD"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            head = None
        gitlinks[name] = head
    root_git = None
    try:
        root_git = subprocess.check_output(
            ["git", "-C", str(NMSDK_ROOT), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        root_git = None
    train = work / "Train"
    source_sha = sha256_paths(source_paths)
    binary_sha = sha256_file(NM)
    runner_scripts = []
    for role, path in (
        ("train_runner", Path(__file__).resolve()),
        ("matrix_queue_runner", ROOT / "scripts" / "run_timelearner_matrix_queue.py"),
        ("matrix_runner", ROOT / "scripts" / "timelearner_matrix.py"),
        ("branch_test_gate", PHASE8),
        ("classic_test_gate", PHASE9),
        ("selectivity_metrics", METRICS),
    ):
        if path.is_file():
            try:
                relpath = path.resolve().relative_to(NMSDK_ROOT.resolve()).as_posix()
            except ValueError:
                relpath = str(path.resolve())
            runner_scripts.append({
                "role": role,
                "path": relpath,
                "sha256": sha256_file(path),
            })
    started_utc = datetime.now(timezone.utc).isoformat()
    return {
        "case": case,
        "run_id": run_id,
        "started_utc": started_utc,
        "experiment_started_utc": started_utc,
        "work_root": str(work),
        "nm": str(NM),
        "nm_mtime": NM.stat().st_mtime if Path(NM).exists() else None,
        "binary_sha256": binary_sha,
        "binary_sha256_at_launch": binary_sha,
        "root_git": root_git,
        "root_git_at_launch": root_git,
        "gitlinks": gitlinks,
        "gitlinks_at_launch": gitlinks,
        "source_sha256": source_sha,
        "source_sha256_at_launch": source_sha,
        "runner_scripts": runner_scripts,
        "config_sha256_before": config_sha_before or {},
        "weights_identity": tipr_weights_identity(train, params_source=params_source),
    }


def compare_run_inputs(
    provenance_at_launch: dict[str, Any],
    *,
    source_sha_after: dict[str, str | None],
    binary_sha_after: str | None,
    config_sha_before: dict[str, str | None],
    config_sha_after: dict[str, str | None],
) -> dict[str, bool]:
    """Report source/binary changes during execution and normal config writes."""
    source_before = (
        provenance_at_launch.get("source_sha256_at_launch")
        or provenance_at_launch.get("source_sha256")
        or {}
    )
    binary_before = (
        provenance_at_launch.get("binary_sha256_at_launch")
        or provenance_at_launch.get("binary_sha256")
    )
    source_changed = source_before != source_sha_after
    binary_changed = binary_before != binary_sha_after
    config_changed = (config_sha_before or {}) != config_sha_after
    return {
        "source_changed_during_run": bool(source_changed),
        "binary_changed_during_run": bool(binary_changed),
        "training_config_changed_during_run": bool(config_changed),
        "inputs_mutated_during_run": bool(source_changed or binary_changed or config_changed),
    }


def should_check_tipr_expectation(row: dict[str, Any]) -> bool:
    """Whether this run is expected to change/produce a configured TipR shape.

    Structural training with PostTrain disabled must preserve the configured
    synapse resistance; a parametric/post-train TipR target is inapplicable.
    """
    try:
        normalization_mode = int(row.get("normalization_mode"))
    except (TypeError, ValueError):
        return True  # Preserve strict legacy validation when mode is unknown.
    posttrain = str(row.get("enable_posttrain_tuning", "1")).strip().lower()
    posttrain_enabled = posttrain not in ("0", "false", "no", "off")
    return not (normalization_mode == 0 and not posttrain_enabled)


def accept_run(
    row: dict[str, Any],
    *,
    expect_fires: str,
    expect_tipr: str,
    mode: str,
    n_dendrites: int = 4,
    need: str = "0",
    child_rc: int | None = None,
    skip_train: bool = False,
) -> tuple[bool, list[str]]:
    """Strict cold-run acceptance (R06). Returns (ok, reasons)."""
    reasons: list[str] = []
    status = str(row.get("train_status", ""))
    if not skip_train:
        if row.get("training_convergence") == "cpp_training_refusal" or status.startswith(
            "cpp_training_failure_"
        ):
            refusal_detail = row.get("training_failure_reason")
            reasons.append(
                "cpp_training_refusal:"
                + (str(refusal_detail) if refusal_detail is not None else status)
            )
        if child_rc is not None and child_rc not in (0, -15, -9):
            # -15/-9 = SIGTERM/SIGKILL after Need=0 stop — allowed if Need cleared
            if need != "0" and "done" not in status:
                reasons.append(f"child_rc={child_rc}")
        # TL-04: do not treat done*_gate_FAIL as train_incomplete (gate is separate).
        incomplete = status in (
            "exited",
            "incomplete",
            "abort",
            "abort_tipr_rmax_stall",
            "incomplete_flag_need1",
        ) or (
            "FAIL" in status
            and "done" not in status
            and "flag_flush" not in status
        )
        if incomplete:
            reasons.append(f"train_incomplete:{status}")
        if need not in ("0", "") and not skip_train and "skip" not in status:
            if "done" not in status and status != "skip_train":
                reasons.append(f"Need={need}")
            elif status == "incomplete_flag_need1" or (
                need == "1" and "flag" in status
            ):
                reasons.append(f"Need={need}")
    tipr = (row.get("after") or {}).get("TipSynapseResistance") or row.get("tipr_final") or ""
    tipr_vec = parse_tipr_vec(tipr)
    if tipr and tipr_vec is not None and len(tipr_vec) != n_dendrites:
        reasons.append(f"tipr_len={len(tipr_vec)}")
    if tipr_vec is not None and any(not math.isfinite(x) for x in tipr_vec):
        reasons.append("tipr_nonfinite")
    mid_s = (row.get("after") or {}).get("FixedLTZThreshold") or ""
    try:
        mid_f = float(str(mid_s).replace(",", ".")) if mid_s else float("nan")
    except ValueError:
        mid_f = float("nan")
    if mid_s and not math.isfinite(mid_f):
        reasons.append("mid_nonfinite")
    fires = row.get("fires") or ""
    if expect_fires and row.get(
        "external_classifier_evaluated", row.get("gate_evaluated", True)
    ):
        if not fires:
            reasons.append("fires_missing")
        elif fires != expect_fires:
            reasons.append(f"fires={fires} expect={expect_fires}")
    tipr_vs = row.get("tipr_vs_snapshot") or ""
    if mode == "search":
        if tipr_vs not in ("applied_best", "same_reverted"):
            reasons.append(f"search_tipr:{tipr_vs or 'unknown'}")
        if row.get("mid_source") not in ("cpp", "cpp_nonseparable"):
            reasons.append(f"search_mid:{row.get('mid_source')}")
    if mode == "keep":
        own = row.get("own_keep_snapshot") or ""
        if own and tipr_vec is not None:
            own_vec = parse_tipr_vec(own)
            if own_vec is None or not tipr_close(tipr_vec, own_vec):
                reasons.append("keep_tipr_mismatch")
    if row.get("gate_evaluated", True) and row.get("gate_ok") is False:
        reasons.append(str(row.get("fail_notes") or row.get("gate_fail") or "gate_fail"))
    if row.get("test_mid_quality") == "nonseparable":
        reasons.append("test_mid_nonseparable")
    got_class = row.get("tipr_class") or ""
    if (
        expect_tipr
        and row.get("tipr_expectation_applicable", should_check_tipr_expectation(row))
        and tipr
        and not tipr_matches_expect(got_class, expect_tipr)
    ):
        reasons.append(f"tipr_class={got_class} expect={expect_tipr}")
    mid_src = row.get("mid_source") or ""
    if mode in ("search",) or row.get("require_cpp_mid"):
        if mid_src not in ("cpp", "cpp_nonseparable"):
            reasons.append(f"mid_source={mid_src}")
    return (len(reasons) == 0, reasons)


def classify_failure_class(
    reasons: list[str],
    row: dict[str, Any] | None = None,
) -> str:
    """Machine-readable failure bucket (TL-04)."""
    row = row or {}
    if not reasons:
        return "execution_error" if row.get("training_convergence") == "execution_error" else "ok"
    if any(r.startswith("cpp_training_refusal:") for r in reasons):
        return "trainer_refused"
    if row.get("training_convergence") == "initial_resistance_reset_mismatch" or (
        "initial_tip_resistance_reset_mismatch" in reasons
    ):
        return "invalid_run_configuration"
    try:
        child_rc = int(row.get("child_rc"))
    except (TypeError, ValueError):
        child_rc = None
    if row.get("training_convergence") == "execution_error" or child_rc in (126, 127):
        return "execution_error"
    if "test_mid_nonseparable" in reasons:
        return "quality_fail"
    if any(
        r.startswith("train_incomplete:")
        or r.startswith("Need=")
        or r.startswith("child_rc=")
        for r in reasons
    ):
        return "train_incomplete"
    if any(r.startswith("tipr_class=") or r.startswith("tipr_") or "keep_tipr" in r for r in reasons):
        # tipr mismatch alone
        if all(
            r.startswith("tipr_")
            or r.startswith("tipr_class=")
            or "keep_tipr" in r
            or r.startswith("search_tipr")
            for r in reasons
        ):
            return "tipr_mismatch"
    if any("gate_rc=" in r or "stale_csv" in r or "missing_csv" in r or "metrics_evaluation" in r for r in reasons) or (
        row.get("gate_evaluated") and row.get("gate_ok") is False
    ):
        return "gate_fail"
    if any(
        r.startswith("fires=") or r == "fires_missing" or
        r == "separation_quality_fail" or r == "target_not_detected"
        or "NonSeparable" in r or "quality" in r.lower()
        for r in reasons
    ):
        return "quality_fail"
    return "quality_fail"


def classify_training_convergence(
    need: str,
    train_meta: dict[str, str] | None = None,
    *,
    skipped: bool = False,
    cpp_failure: tuple[int, int] | None = None,
    child_rc: int | None = None,
) -> str:
    """Report trainer completion independently from post-train quality.

    The C++ FinalizePostTuneMid path sets TrainingPhase=Done and clears Need
    before writing posttune_complete.flag, including result=NonSeparable. The
    flag therefore proves that the training phase reached its terminal path;
    it does not prove that the learned response is selective.
    """
    if skipped:
        return "not_run"
    if cpp_failure is not None:
        return "cpp_training_refusal"
    # Bash uses 126/127 when a command cannot be executed or found. The
    # trainer did not reach a state that can be judged for convergence.
    try:
        execution_rc = int(child_rc)
    except (TypeError, ValueError):
        execution_rc = None
    if execution_rc in (126, 127):
        return "execution_error"
    meta = train_meta or {}
    if meta.get("result") not in (None, "", "0"):
        return "converged_posttune_finalized"
    if str(need).strip() == "0":
        return "converged_need0"
    if str(need).strip() == "1":
        return "not_converged_at_stop"
    return "insufficient_data"


def classify_posttune_quality(train_meta: dict[str, str] | None = None) -> str:
    """Map C++ PostTuneResult to a quality outcome, not a convergence verdict."""
    result = str((train_meta or {}).get("result", "")).strip()
    return {
        "1": "separable",
        "2": "nonseparable",
        "3": "posttune_setup_failure",
        "4": "posttune_timeout",
        "5": "invalid_posttune_metrics",
    }.get(result, "not_reached_or_unknown")


def classify_detection_quality(
    *,
    gate_evaluated: bool,
    gate_ok: bool | None,
    target_detected: bool | None,
    training_convergence: str,
    test_mid_quality: str = "",
    external_classifier_evaluated: bool = False,
) -> str:
    """Summarize target detection independently of evaluator execution/quality."""
    if training_convergence in (
        "not_converged_at_stop",
        "insufficient_data",
        "cpp_training_refusal",
        "initial_resistance_reset_mismatch",
    ):
        return (
            "not_evaluated_initial_resistance_reset_mismatch"
            if training_convergence == "initial_resistance_reset_mismatch"
            else "not_evaluated_training_incomplete"
        )
    if training_convergence == "execution_error":
        return "not_evaluated_execution_error"
    if not gate_evaluated:
        return "not_evaluated_training_incomplete"
    if test_mid_quality == "nonseparable" and not external_classifier_evaluated:
        return "not_evaluated_nonseparable_test_mid"
    if gate_ok is False:
        return "evaluation_error"
    if target_detected is True:
        return "detected"
    if target_detected is False:
        return "target_not_detected"
    return "insufficient_data"


def classify_separation_quality(
    *, gate_evaluated: bool, gate_ok: bool | None, quality_ok: bool | None,
    training_convergence: str, test_mid_quality: str = "",
    external_classifier_evaluated: bool = False,
) -> str:
    """Metric outcome is separate from evaluator process success."""
    if training_convergence in (
        "not_converged_at_stop", "insufficient_data", "cpp_training_refusal",
        "initial_resistance_reset_mismatch",
    ):
        return (
            "not_evaluated_initial_resistance_reset_mismatch"
            if training_convergence == "initial_resistance_reset_mismatch"
            else "not_evaluated_training_incomplete"
        )
    if training_convergence == "execution_error":
        return "not_evaluated_execution_error"
    if not gate_evaluated:
        return "not_evaluated_training_incomplete"
    if test_mid_quality == "nonseparable" and not external_classifier_evaluated:
        return "nonseparable_test_mid"
    if gate_ok is False:
        return "evaluation_error"
    if quality_ok is True:
        return "pass"
    if quality_ok is False:
        return "fail"
    return "insufficient_data"


def should_run_quality_gate(training_convergence: str) -> bool:
    """Do not test a partial model after training stopped before a terminal state."""
    return training_convergence not in (
        "not_converged_at_stop",
        "insufficient_data",
        "cpp_training_refusal",
        "execution_error",
        "initial_resistance_reset_mismatch",
    )


def classify_slog_gib(
    gib: float, *, abort_gib: float = 3.0, prune_gib: float = 2.0
) -> Literal["ok", "prune", "abort"]:
    """Abort threshold before prune; doc says abort ~3G (overridable for diagnostics)."""
    if gib > abort_gib:
        return "abort"
    if gib > prune_gib:
        return "prune"
    return "ok"


def collect_posttune_salvage(train: Path) -> PostTuneSalvage:
    s = PostTuneSalvage()
    flag = train / "posttune_complete.flag"
    if flag.exists():
        meta = parse_flag_file(flag)
        s.mid = meta.get("mid")
        s.tipr_s = meta.get("tipr")
        s.tipr_snapshot = meta.get("tipr_snapshot")
        if s.mid or s.tipr_s:
            s.source = "salvage_flag"
    live = train / "posttune_tipr_live.txt"
    if live.exists() and not s.tipr_s:
        for line in live.read_text(encoding="utf-8").splitlines():
            if line.startswith("tipr="):
                s.tipr_s = line.split("=", 1)[1].strip()
                s.source = "salvage_live"
            elif line.startswith("tipr_snapshot=") and not s.tipr_snapshot:
                s.tipr_snapshot = line.split("=", 1)[1].strip()
    stat_dir = _latest_stat_dir(train)
    tipr = _last_trace_vector(stat_dir, "TipSynapseResistanceTrace") if stat_dir else None
    lens = _last_trace_vector(stat_dir, "DendriteLengthTrace") if stat_dir else None
    if live.exists() and not lens:
        for line in live.read_text(encoding="utf-8").splitlines():
            if line.startswith("L="):
                lens = line.split("=", 1)[1].split()
                break
    if not s.tipr_s and tipr:
        s.tipr_s = " ".join(tipr[:4])
        s.source = "salvage_trace"
    s.lens_s = " ".join(str(int(float(x))) for x in lens[:4]) if lens else None
    if s.source == "none" and (s.tipr_s or s.mid or s.lens_s):
        s.source = "salvage_trace"
    return s


def apply_posttune_salvage(
    train: Path, salvage: PostTuneSalvage, *, clear_need: bool = True
) -> None:
    if not salvage.tipr_s and not salvage.mid and not salvage.lens_s:
        print("apply_posttune_salvage: nothing to flush")
        return
    print(
        f"apply_posttune_salvage src={salvage.source} mid={salvage.mid} "
        f"TipR={salvage.tipr_s} L={salvage.lens_s}"
    )
    flag = train / "posttune_complete.flag"
    for rel in ("Parameters_00.xml", "Model_00.xml"):
        p = train / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        if salvage.tipr_s:
            t = set_tag(t, "TipSynapseResistance", salvage.tipr_s, 1)
        if salvage.lens_s:
            t = set_tag(t, "DendriteLength", salvage.lens_s, 1)
        if salvage.mid:
            t = set_tag(t, "FixedLTZThreshold", salvage.mid, 1)
            t = set_tag(t, "LTZThreshold", salvage.mid, 1)
            t = set_tag(t, "UseFixedLTZThreshold", "1", 1)
            t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0", 1)
        if clear_need and (flag.exists() or salvage.mid):
            t = set_tag(t, "IsNeedToTrain", "0", 1)
        p.write_text(t, encoding="utf-8")


def flush_posttune_artifacts(train: Path) -> str:
    """Compatibility wrapper: collect then apply salvage. Returns params_source."""
    salvage = collect_posttune_salvage(train)
    if not salvage.tipr_s and not salvage.mid and not salvage.lens_s:
        print("flush_posttune_artifacts: nothing to flush")
        return "none"
    apply_posttune_salvage(train, salvage)
    return salvage.source


def _snap_tipr_live(train: Path, live: Path) -> None:
    """Best-effort TipR/L + AmpNorm traces from StatisticLog and/or Parameters (W0)."""
    stat_dir = _latest_stat_dir(train)
    tipr = _last_trace_vector(stat_dir, "TipSynapseResistanceTrace") if stat_dir else None
    lens = _last_trace_vector(stat_dir, "DendriteLengthTrace") if stat_dir else None
    amp_dt = _last_trace_vector(stat_dir, "AmpDtTrace") if stat_dir else None
    res_st = _last_trace_vector(stat_dir, "ResistanceStatusTrace") if stat_dir else None
    no_imp = _last_trace_vector(stat_dir, "NoImproveResistanceTrace") if stat_dir else None
    last_dt = _last_trace_vector(stat_dir, "LastAbsDtTrace") if stat_dir else None
    # Fallback / supplement from Parameters tags (UpdateNormTraces → XML)
    params = train / "Parameters_00.xml"
    snap = poll_params_snapshot(params) if params.exists() else {}
    if not tipr and snap.get("tipr"):
        tipr = snap["tipr"].replace(",", ".").split()
    if not lens and snap.get("L"):
        lens = snap["L"].replace(",", ".").split()
    if not amp_dt and snap.get("amp_dt"):
        amp_dt = snap["amp_dt"].replace(",", ".").split()
    if not res_st and snap.get("res_st"):
        res_st = snap["res_st"].replace(",", ".").split()
    if not no_imp and snap.get("no_imp"):
        no_imp = snap["no_imp"].replace(",", ".").split()
    if not last_dt and snap.get("last_abs_dt"):
        last_dt = snap["last_abs_dt"].replace(",", ".").split()
    parts: list[str] = []
    if tipr:
        parts.append("tipr=" + " ".join(tipr[:4]))
    if lens:
        parts.append("L=" + " ".join(str(int(float(x))) for x in lens[:4]))
    if amp_dt:
        parts.append("amp_dt=" + " ".join(amp_dt[:4]))
    if res_st:
        parts.append("res_st=" + " ".join(res_st[:4]))
    if no_imp:
        parts.append("no_imp=" + " ".join(no_imp[:4]))
    if last_dt:
        parts.append("last_abs_dt=" + " ".join(last_dt[:4]))
    if snap.get("need"):
        parts.append(f"need={snap['need']}")
    if snap.get("phase"):
        parts.append(f"phase={snap['phase']}")
    if parts:
        live.write_text("\n".join(parts) + "\n", encoding="utf-8")
        print(f"  SNAP {live.name}: {parts[0][:60]}")
        for extra in parts[1:]:
            print(f"        {extra[:100]}")

def poll_params_snapshot(
    params: Path, *, prev_mtime: float | None = None
) -> dict[str, Any]:
    """Read Need/TipR/L (+ AmpNorm traces / phase) from Parameters; autosave via mtime."""
    text = params.read_text(encoding="utf-8") if params.exists() else ""
    try:
        mtime = params.stat().st_mtime if params.exists() else 0.0
    except OSError:
        mtime = 0.0
    tipr = " ".join((get_tag(text, "TipSynapseResistance") or "").split())
    length = " ".join((get_tag(text, "DendriteLength") or "").split())
    need = (get_tag(text, "IsNeedToTrain") or "").strip()
    phase = (get_tag(text, "TrainingPhase") or "").strip()
    amp_dt = " ".join((get_tag(text, "AmpDtTrace") or "").split())
    res_st = " ".join((get_tag(text, "ResistanceStatusTrace") or "").split())
    no_imp = " ".join((get_tag(text, "NoImproveResistanceTrace") or "").split())
    last_dt = " ".join((get_tag(text, "LastAbsDtTrace") or "").split())
    autosave_seen = prev_mtime is not None and mtime > prev_mtime + 1e-6
    return {
        "need": need,
        "tipr": tipr,
        "L": length,
        "mtime": mtime,
        "autosave_seen": autosave_seen,
        "tipr_settled": tipr_looks_posttuned(tipr),
        "phase": phase,
        "amp_dt": amp_dt,
        "res_st": res_st,
        "no_imp": no_imp,
        "last_abs_dt": last_dt,
    }


def runtime_resistance_max_from_audit(train: Path) -> float | None:
    """Read the derived cap from the C++ cold-reset record, if available."""
    audit = train / "TimeLearnerTrainingAudit.log"
    if not audit.is_file():
        return None
    try:
        with audit.open("r", encoding="utf-8", errors="replace") as stream:
            for line in stream:
                fields = dict(
                    item.split("=", 1) for item in line.strip().split(";") if "=" in item
                )
                if fields.get("kind") != "reset":
                    continue
                value = float(fields.get("rmax", "0"))
                return value if math.isfinite(value) and value > 0.0 else None
    except (OSError, ValueError):
        return None
    return None


def runtime_resistance_max_by_input_from_audit(train: Path) -> list[float] | None:
    """Read per-input caps from the C++ cold-reset record.

    TimeLearner's final input is a reference/timing anchor and is intentionally
    absent from this vector. Using the scalar ResistanceMax against the whole
    TipSynapseResistance vector would mistake an anchor at Rmax for an
    adjustable synapse stalled at Rmax.
    """
    audit = train / "TimeLearnerTrainingAudit.log"
    if not audit.is_file():
        return None
    try:
        with audit.open("r", encoding="utf-8", errors="replace") as stream:
            for line in stream:
                fields = dict(
                    item.split("=", 1) for item in line.strip().split(";") if "=" in item
                )
                if fields.get("kind") != "reset":
                    continue
                values = parse_float_vec(fields.get("rmax_by_input", "") or "")
                if values and all(math.isfinite(value) and value > 0.0 for value in values):
                    return values
    except OSError:
        return None
    return None


def runtime_loaded_tip_reset_check(train: Path) -> dict[str, Any]:
    """Compare an explicit cold-reset TipR vector with the C++ reset audit."""
    contract_path = train / "cold_reset_contract.json"
    audit = train / "TimeLearnerTrainingAudit.log"
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        expected_text = contract["expected_runtime_after_reset"].get("TipSynapseResistance")
    except (OSError, ValueError, KeyError, TypeError):
        return {"enabled": True, "passed": False, "reason": "cold_reset_contract_missing"}
    if not expected_text:
        return {"enabled": True, "passed": False, "reason": "expected_vector_missing"}
    expected_reset_kind = (
        "reset_complete_untrained" if bool(contract.get("is_branch")) else "reset"
    )

    def parse_audit_vector(raw: str) -> list[float] | None:
        value = raw.strip()
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]
        try:
            parsed = [float(part) for part in value.replace(",", " ").split()]
        except ValueError:
            return None
        return parsed if parsed and all(math.isfinite(item) for item in parsed) else None

    expected_raw = parse_audit_vector(str(expected_text))
    if expected_raw is None:
        return {"enabled": True, "passed": False, "reason": "expected_vector_invalid"}
    if not audit.is_file():
        return {
            "enabled": True,
            "passed": False,
            "reason": "training_audit_missing",
            "expected_ohm": expected_raw,
        }
    try:
        for line in _training_audit_lines_reverse(audit):
            fields = dict(
                item.split("=", 1) for item in line.split(";") if "=" in item
            )
            if fields.get("kind") != expected_reset_kind:
                continue
            actual = parse_audit_vector(fields.get("tip_r", ""))
            minima = parse_audit_vector(fields.get("rmin_by_input", "") or "") or []
            maxima = parse_audit_vector(fields.get("rmax_by_input", "") or "") or []
            expected_effective = list(expected_raw)
            for index in range(min(len(expected_effective), len(minima), len(maxima))):
                if minima[index] > 0.0 and maxima[index] >= minima[index]:
                    expected_effective[index] = max(
                        minima[index], min(maxima[index], expected_effective[index])
                    )
            passed = (
                actual is not None
                and len(actual) == len(expected_effective)
                and all(
                    math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-6)
                    for got, want in zip(actual, expected_effective)
                )
            )
            return {
                "enabled": True,
                "passed": passed,
                "reason": "matched" if passed else "post_reset_vector_mismatch",
                "audit_kind": fields.get("kind"),
                "expected_audit_kind": expected_reset_kind,
                "expected_ohm": expected_raw,
                "expected_after_bounds_ohm": expected_effective,
                "actual_ohm": actual,
            }
    except OSError:
        pass
    return {
        "enabled": True,
        "passed": False,
        "reason": f"{expected_reset_kind}_audit_missing",
        "expected_audit_kind": expected_reset_kind,
        "expected_ohm": expected_raw,
    }


def _training_audit_lines_reverse(audit: Path, chunk_size: int = 65536):
    """Yield complete audit lines newest-first without truncating long records."""
    with audit.open("rb") as stream:
        stream.seek(0, 2)
        end = stream.tell()
        if end == 0:
            return

        # Ignore a record that is still being appended. The C++ audit writes
        # complete records with a newline; a partial tail must not mask the
        # last complete record while the trainer is running.
        stream.seek(end - 1)
        if stream.read(1) != b"\n":
            position = end
            while position > 0:
                start = max(0, position - chunk_size)
                stream.seek(start)
                block = stream.read(position - start)
                newline = block.rfind(b"\n")
                if newline >= 0:
                    end = start + newline + 1
                    break
                position = start
            else:
                return

        position = end
        carry = b""
        while position > 0:
            start = max(0, position - chunk_size)
            stream.seek(start)
            data = stream.read(position - start) + carry
            parts = data.split(b"\n")
            complete_lines = parts[1:]
            if start == 0:
                if parts[0]:
                    complete_lines.append(parts[0])
                carry = b""
            else:
                carry = parts[0]
            for raw_line in reversed(complete_lines):
                if raw_line:
                    yield raw_line.decode("utf-8", errors="replace").rstrip("\r")
            position = start


def runtime_training_failure_from_audit(train: Path) -> tuple[int, int] | None:
    """Read the latest C++ terminal failure from its append-only audit."""
    audit = train / "TimeLearnerTrainingAudit.log"
    if not audit.is_file():
        return None
    try:
        for line in _training_audit_lines_reverse(audit):
            if "kind=iteration" not in line:
                continue
            fields = dict(
                item.split("=", 1) for item in line.strip().split(";") if "=" in item
            )
            reason = int(fields.get("failure_reason", "0"))
            phase = int(fields.get("phase", "0"))
            return (phase, reason) if reason > 0 else None
    except (OSError, ValueError):
        return None
    return None


def _parse_audit_scalar(fields: dict[str, str], key: str) -> str | None:
    raw = fields.get(key)
    if raw in (None, ""):
        return None
    return raw


def runtime_stage0_fields_from_audit(train: Path) -> dict[str, str | int | float] | None:
    """Stage0 scalars from newest kind=done or terminal need=0 iteration audit."""
    audit = train / "TimeLearnerTrainingAudit.log"
    if not audit.is_file():
        return None
    keys = (
        "delay_residue",
        "amp_over_target",
        "sync_exit",
        "amp_be",
        "done_be",
        "done_best_effort",
        "sep_margin",
        "sep_gap",
        "sep_tgt",
        "sep_max_foil",
    )
    int_keys = ("sync_exit", "amp_be", "done_be", "done_best_effort")
    try:
        for line in _training_audit_lines_reverse(audit):
            if "kind=done" not in line and (
                "kind=iteration" not in line or ";need=0" not in line
            ):
                continue
            fields = dict(
                item.split("=", 1) for item in line.strip().split(";") if "=" in item
            )
            if "delay_residue" not in fields:
                continue
            out: dict[str, str | int | float] = {"audit_kind": fields.get("kind", "")}
            for key in keys:
                raw = _parse_audit_scalar(fields, key)
                if raw is None:
                    continue
                if key in int_keys:
                    out[key] = int(raw)
                else:
                    out[key] = float(raw.replace(",", "."))
            if "done_be" not in out and "done_best_effort" in out:
                out["done_be"] = out["done_best_effort"]
            return out
    except (OSError, ValueError):
        return None
    return None


DEFAULT_STALL_AUTOSAVE_N = 8


def parse_float_vec(s: str) -> list[float] | None:
    """Parse space-separated floats; commas as decimal sep."""
    parts = (s or "").replace(",", ".").split()
    if not parts:
        return None
    try:
        return [float(x) for x in parts]
    except ValueError:
        return None


def tipr_any_at_rmax(
    tipr: str, rmax: float | Sequence[float], *, frac: float = 0.99
) -> bool:
    """True if any trainable TipR is at/above its corresponding Rmax.

    The C++ audit's per-input cap vector is preferred because it excludes the
    reference anchor. A scalar fallback compares all TipR entries except the
    final anchor used by both TimeLearner trainers.
    """
    vec = parse_float_vec(tipr)
    if not vec:
        return False
    if isinstance(rmax, Sequence) and not isinstance(rmax, (str, bytes)):
        return any(
            math.isfinite(cap) and cap > 0.0 and value >= frac * cap
            for value, cap in zip(vec, rmax)
        )
    if not math.isfinite(float(rmax)) or float(rmax) <= 0.0:
        return False
    trainable_count = max(0, len(vec) - 1)
    return any(value >= frac * float(rmax) for value in vec[:trainable_count])


def length_vecs_equal(a: str, b: str) -> bool:
    """True when DendriteLength vectors match (int-tolerant)."""
    va = parse_float_vec(a)
    vb = parse_float_vec(b)
    if va is None or vb is None or len(va) != len(vb):
        return False
    return all(abs(x - y) < 0.5 for x, y in zip(va, vb))


def rmax_stall_tick(
    *,
    tipr: str,
    length: str,
    need: str,
    rmax: float | Sequence[float],
    prev_L: str | None,
    prev_tipr: str | None,
    streak: int,
) -> tuple[int, str | None, str | None]:
    """Update trainable TipR@Rmax stall streak; return prior autosave state.

    Require TipR@Rmax, Need!=0, and *both* L and TipR vectors unchanged vs the
    previous autosave. If TipR starts leaving Rmax (escape in progress), reset.
    """
    if need == "0" or not tipr_any_at_rmax(tipr, rmax):
        return 0, length, tipr
    if (
        prev_L is not None
        and prev_tipr is not None
        and length_vecs_equal(length, prev_L)
        and " ".join(tipr.split()) == " ".join(prev_tipr.split())
    ):
        return streak + 1, length, tipr
    return 1, length, tipr


def softcold_early_done(
    snap: dict[str, Any], *, flag_hit: bool, require_settled: bool = True
) -> bool:
    """True when autosaved XML shows Need=0 and TipR settled (or flag present).

    Cold TipR is FlatLastR (`TIPR_COLD`); do not treat cold-flat alone as settled
    for early stop — require flag, or TipR that left cold (e.g. CanonRmin).
    """
    if snap.get("need") != "0":
        return False
    if flag_hit:
        return True
    if not require_settled:
        return True
    if not snap.get("tipr_settled"):
        return False
    tipr = snap.get("tipr") or ""
    cold = " ".join(TIPR_COLD.split())
    cur = " ".join(tipr.split())
    try:
        cv = [float(x) for x in cold.split()]
        tv = [float(x) for x in cur.split()[:4]]
        still_cold = len(tv) >= 4 and all(
            abs(a - b) <= max(1.0, 0.01 * abs(b)) for a, b in zip(tv, cv)
        )
    except ValueError:
        still_cold = cur == cold
    if still_cold:
        return False
    return True


def wait_need0(
    train: Path,
    tlim: float,
    log: Path,
    *,
    max_polls: int = 401,
    allow_salvage: bool = False,
    no_prune: bool = False,
    snap_every: int = 0,
    slog_abort_gib: float = 3.0,
    early_stop_autosave: bool = True,
    stall_autosave_n: int = DEFAULT_STALL_AUTOSAVE_N,
) -> tuple[str, int | None]:
    ini = train / "Project.ini"
    assert_disk_for_train()
    slog = train / "StatisticLog"
    if slog.is_dir():
        shutil.rmtree(slog, ignore_errors=True)
    flag = train / "posttune_complete.flag"
    if flag.exists():
        flag.unlink()
    live = train / "posttune_tipr_live.txt"
    if live.exists():
        live.unlink()
    params = train / "Parameters_00.xml"
    prev_mtime = params.stat().st_mtime if params.exists() else 0.0
    rmax = 0.0
    rmax_by_input: list[float] | None = None
    if params.exists():
        try:
            rmax = float(
                (get_tag(params.read_text(encoding="utf-8"), "ResistanceMax") or "0")
                .replace(",", ".")
            )
        except ValueError:
            rmax = 0.0
    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(tlim), "-x", "-S"]
    print(
        f"TRAIN {train.parent.name} -t {tlim} Avail={free_gib():.0f}G "
        f"polls={max_polls} no_prune={int(no_prune)} snap_every={snap_every} "
        f"slog_abort={slog_abort_gib:g}G early_stop_autosave={int(early_stop_autosave)} "
        f"stall_autosave_n={stall_autosave_n} rmax_xml={rmax:g}"
    )
    proc = subprocess.Popen(cmd, cwd=str(train), stdout=log.open("w"), stderr=subprocess.STDOUT)
    need0 = False
    stall_status: str | None = None
    stall_streak = 0
    stall_prev_L: str | None = None
    stall_prev_tipr: str | None = None
    runtime_rmax_seen = False
    for i in range(1, max_polls + 1):
        time.sleep(30)
        if proc.poll() is not None:
            break
        cpp_failure = runtime_training_failure_from_audit(train)
        if cpp_failure is not None:
            phase, reason = cpp_failure
            _snap_tipr_live(train, live)
            print(
                f"  C++_TRAINING_FAILURE phase={phase} reason={reason} "
                "from TimeLearnerTrainingAudit — terminate NM"
            )
            proc.terminate()
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
            stall_status = f"cpp_training_failure_{reason}"
            break
        if not runtime_rmax_seen:
            runtime_caps = runtime_resistance_max_by_input_from_audit(train)
            runtime_rmax = runtime_resistance_max_from_audit(train)
            if runtime_caps is not None:
                rmax_by_input = runtime_caps
                rmax = max(runtime_caps)
                runtime_rmax_seen = True
                print(
                    f"  RMAX_RUNTIME_BY_INPUT={runtime_caps} from C++ cold-reset audit",
                    flush=True,
                )
            elif runtime_rmax is not None:
                rmax = runtime_rmax
                runtime_rmax_seen = True
                print(f"  RMAX_RUNTIME={rmax:g} from C++ cold-reset audit")
        snap = poll_params_snapshot(params, prev_mtime=prev_mtime)
        if snap["autosave_seen"]:
            print(
                f"  AUTOSAVE_SEEN mtime={snap['mtime']:.3f} "
                f"Need={snap['need']} TipR={snap['tipr'][:48]} L={snap['L']}"
            )
            prev_mtime = snap["mtime"]
            if stall_autosave_n > 0 and rmax > 0.0:
                stall_streak, stall_prev_L, stall_prev_tipr = rmax_stall_tick(
                    tipr=snap["tipr"],
                    length=snap["L"],
                    need=snap["need"] or "",
                    rmax=rmax_by_input if rmax_by_input is not None else rmax,
                    prev_L=stall_prev_L,
                    prev_tipr=stall_prev_tipr,
                    streak=stall_streak,
                )
                if stall_streak >= stall_autosave_n:
                    print(
                        f"  ABORT TipR@Rmax stall: {stall_streak} autosaves "
                        f"TipR+L unchanged Need={snap['need']} TipR={snap['tipr'][:48]} "
                        f"L={snap['L']} — terminate NM"
                    )
                    proc.terminate()
                    try:
                        proc.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    stall_status = "abort_tipr_rmax_stall"
                    break
        need = snap["need"]
        flag_hit = flag.exists()
        slog_bytes = 0
        if slog.is_dir():
            for p in slog.rglob("*"):
                if p.is_file():
                    try:
                        slog_bytes += p.stat().st_size
                    except OSError:
                        pass
        slog_gib = slog_bytes / (1 << 30)
        print(
            f"  poll#{i} Need={need} flag={int(flag_hit)} "
            f"tipr_settled={int(snap['tipr_settled'])} "
            f"slog={slog_gib:.2f}G et~{i * 30}s"
            + (f" rmax_stall={stall_streak}" if stall_streak else "")
        )
        if snap_every > 0 and i % snap_every == 0:
            _snap_tipr_live(train, live)
        action = classify_slog_gib(slog_gib, abort_gib=slog_abort_gib)
        if action == "abort":
            print(f"  ABORT StatisticLog>{slog_gib:.1f}G — terminate NM")
            proc.terminate()
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
            break
        if action == "prune":
            if no_prune:
                print(
                    f"  SKIP_PRUNE StatisticLog {slog_gib:.2f}G "
                    f"(--no-prune; abort still at >{slog_abort_gib:g}G)"
                )
            else:
                _snap_tipr_live(train, live)
                print(f"  PRUNE StatisticLog {slog_gib:.2f}G — keep Train running")
                shutil.rmtree(slog, ignore_errors=True)
                continue
        done = need == "0" or flag_hit
        if early_stop_autosave and softcold_early_done(snap, flag_hit=flag_hit):
            done = True
        if done:
            need0 = True
            # Console SaveProject runs only when IsCalcFinished (-t exhausted) with
            # -S/-x latch (A15). Early SIGTERM skips Save → Parameters TipR/Need
            # lag behind posttune_complete.flag (T3 H2 / audit A16-adjacent).
            # Prefer natural exit so -S can flush; terminate only after grace.
            # With model-time autosave, Need/TipR may already be flushed on disk.
            grace_s = 90.0
            t_end = time.time() + grace_s
            print(
                f"  post-flag: wait up to {grace_s:.0f}s for NM -S exit "
                f"(Need={need} flag={int(flag_hit)} tipr_settled={int(snap['tipr_settled'])})"
            )
            while proc.poll() is None and time.time() < t_end:
                time.sleep(5)
                snap = poll_params_snapshot(params, prev_mtime=prev_mtime)
                if snap["autosave_seen"]:
                    print(f"  AUTOSAVE_SEEN mtime={snap['mtime']:.3f} (grace)")
                    prev_mtime = snap["mtime"]
                need = snap["need"]
                if need == "0" and flag.exists():
                    # Likely saved; give I/O a beat then wait for quit.
                    time.sleep(3)
                    if proc.poll() is not None:
                        break
            if proc.poll() is None:
                print("  post-flag grace expired — terminate NM")
                proc.terminate()
                try:
                    proc.wait(timeout=90)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=30)
            break
    else:
        proc.terminate()
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
    child_rc = proc.poll()
    params_source = "none"
    if allow_salvage:
        params_source = flush_posttune_artifacts(train)
    else:
        # Cold path: do not lift live/stale salvage into Parameters.
        need_now = get_tag(
            (train / "Parameters_00.xml").read_text(encoding="utf-8"), "IsNeedToTrain"
        )
        if flag.exists() and need_now == "1":
            # Current-run flag flush (H2): not archive/live salvage.
            params_source = flush_current_train_flag(train)
            print(f"  flag_flush={params_source}")
        elif flag.exists() or need_now == "0":
            params_source = "nm_save"
    need = get_tag((train / "Parameters_00.xml").read_text(encoding="utf-8"), "IsNeedToTrain")
    if stall_status:
        status = stall_status
    elif need == "0" and params_source == "flag_flush":
        status = "done_flag_flush"
    elif need == "0":
        status = "done"
    elif flag.exists() and need == "1":
        status = "incomplete_flag_need1"
    elif flag.exists():
        status = "done"
    else:
        status = "incomplete" if need0 else "exited"
    if allow_salvage and params_source.startswith("salvage"):
        status = f"{status}_salvaged"
    return status, child_rc


def mid_source_of(
    flag_meta: dict[str, str],
    thr: str,
    *,
    require_landscape: bool = True,
) -> str:
    try:
        mid_f = float((flag_meta.get("mid") or thr or "1").replace(",", "."))
    except ValueError:
        mid_f = float("nan")
    if not math.isfinite(mid_f):
        return "invalid_nonfinite"
    landscape_ok = flag_meta.get("landscape_ok", "1") == "1"
    result = flag_meta.get("result", "")
    if result == "2":
        return "cpp_nonseparable"
    if result and result not in ("", "0", "1"):
        if flag_meta.get("inference") == "1" and mid_f < 0.9:
            return "invalid_result"
    if flag_meta.get("inference") == "1" and mid_f < 0.9:
        if require_landscape and not landscape_ok:
            return "invalid_landscape"
        return "cpp"
    if mid_f < 0.9 and flag_meta.get("mid"):
        return "cpp_train"
    return "missing"


def test_mid_quality_of(flag_meta: dict[str, str]) -> str:
    """Map Test-side C++ inference-mid outcome independently of classifier metrics."""
    if flag_meta.get("inference") != "1":
        return "not_available"
    return {
        "1": "separable",
        "2": "nonseparable",
        "3": "posttune_setup_failure",
        "4": "posttune_timeout",
        "5": "invalid_posttune_metrics",
    }.get(flag_meta.get("result", ""), "not_recorded")


def classifier_evaluation_status(gate: GateResult) -> str:
    """Describe whether external classification ran, independently of Test mid."""
    if gate.external_classifier_evaluated:
        return "evaluated" if gate.ok else "evaluation_error"
    if gate.test_mid_quality == "nonseparable":
        return "not_run_nonseparable_test_mid"
    if not gate.evaluated:
        return "not_run_training_incomplete"
    return "not_run"


def fires_from_csv(csv_path: Path) -> tuple[str, str]:
    if not csv_path.exists():
        return "", ""
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    if not rows:
        return "", ""
    fires = "".join(
        "1" if (r.get("neuron_fired") or "0") not in ("0", "0.0", "") else "0"
        for r in rows[:8]
    )
    try:
        out = subprocess.check_output(
            [sys.executable, str(METRICS), str(csv_path)], text=True, stderr=subprocess.STDOUT
        )
        for line in reversed(out.strip().splitlines()):
            if "acc" in line.lower() or "ok_audit" in line:
                return fires, line.strip()
        return fires, ""
    except subprocess.CalledProcessError as e:
        return fires, e.output[-200:] if e.output else "metrics_fail"


def _run_gate_once(
    case: dict,
    *,
    variant: str = "standard",
    candidate_mid: float | None = None,
) -> GateResult:
    root: Path = case["root"]
    test = root / "Test"
    span = int(case.get("span_ms", 25))
    csv_path = test / "SelectivityLog" / "results.csv"
    test_flag = test / "posttune_complete.flag"
    # Test can live on filesystems with one-second mtime granularity. Remove
    # any prior flag first so a flag present after this invocation is fresh
    # without relying on a sub-second timestamp comparison.
    test_flag.unlink(missing_ok=True)
    gate_started = time.time()
    if case["kind"] == "branch":
        cmd = [
            sys.executable,
            str(PHASE8),
            str(root),
            "--span-ms",
            str(span),
            "--pack",
            "A",
            "--test-t",
            "40",
        ]
        if variant in ("train_candidate", "test_cpp_mid") or case["skip_tipr_mid"]:
            cmd.append("--skip-tipr-mid")
        else:
            cmd.append("--force-python-hygiene")
    else:
        test_t = "40" if span < 100 else ("80" if span < 480 else "80")
        cmd = [
            sys.executable,
            str(PHASE9),
            str(root),
            "--test-t",
            test_t,
            "--span-ms",
            str(span),
            "--metric",
            "ltz_potential_max",
        ]
        if variant in ("train_candidate", "test_cpp_mid") or case["skip_tipr_mid"]:
            cmd.append("--skip-tipr-mid")
    if variant == "train_candidate":
        if candidate_mid is None or not math.isfinite(candidate_mid):
            raise ValueError("train_candidate gate requires a finite C++ candidate_mid")
        cmd.extend(("--diagnostic-threshold", format(candidate_mid, ".17g")))
    elif variant == "test_cpp_mid":
        cmd.append("--force-test-cpp-mid")
    log = test / "run_posttune_gate.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    print("GATE", " ".join(cmd))
    with log.open("w") as gate_log:
        rc = subprocess.call(cmd, stdout=gate_log, stderr=subprocess.STDOUT)
    print("gate rc", rc)
    gate_output = log.read_text(encoding="utf-8", errors="replace")
    csv_mtime = csv_path.stat().st_mtime if csv_path.exists() else None
    fires, metrics_line = fires_from_csv(csv_path)
    test_meta = parse_flag_file(test_flag)
    test_flag_fresh = test_flag.is_file()
    test_mid_quality = (
        test_mid_quality_of(test_meta) if test_flag_fresh else "not_available"
    )
    test_mid_gap = test_meta.get("gap", "") if test_flag_fresh else ""
    test_mid_result = test_meta.get("result", "") if test_flag_fresh else ""
    try:
        test_mid_value = float((test_meta.get("mid") or "1").replace(",", "."))
    except ValueError:
        test_mid_value = float("nan")
    # The C++ Test inference-mid may correctly conclude that no threshold
    # separates the target from its foils. The phase gate then exits before it
    # runs the external classifier; this is a quality result, not an evaluator
    # crash or a missing result.
    if (
        rc != 0
        and "inference mid still silent:" in gate_output
        and test_flag_fresh
        and test_meta.get("inference") == "1"
        and test_mid_quality == "nonseparable"
        and math.isfinite(test_mid_value)
        and test_mid_value >= 0.9
    ):
        return GateResult(
            fires="",
            metrics_line="not_run_nonseparable_test_mid",
            rc=rc,
            csv_mtime=csv_mtime,
            gate_started=gate_started,
            ok=None,
            fail_reason="test_mid_nonseparable",
            evaluated=True,
            quality_ok=None,
            target_detected=None,
            external_classifier_evaluated=False,
            test_mid_quality=test_mid_quality,
            test_mid_gap=test_mid_gap,
            test_mid_result=test_mid_result,
            commands=[cmd],
        )
    ok = rc == 0
    fail_reason = ""
    if rc != 0:
        fail_reason = f"gate_rc={rc}"
    elif csv_mtime is None:
        ok = False
        fail_reason = "missing_csv"
    elif csv_mtime + 1.0 < gate_started:
        ok = False
        fail_reason = "stale_csv"
        fires, metrics_line = "", "stale_csv_ignored"
    quality_metrics: dict[str, Any] = {}
    if ok:
        try:
            from selectivity_metrics import evaluate_path
            quality_metrics, metrics_rc = evaluate_path(csv_path)
            if metrics_rc != 0:
                ok = False
                fail_reason = "metrics_evaluation_failed"
                quality_metrics = {}
        except Exception as exc:
            ok = False
            fail_reason = f"metrics_evaluation_error:{type(exc).__name__}"
    quality_ok = bool(quality_metrics.get("ok_audit")) if quality_metrics else None
    target_detected = (
        bool(quality_metrics.get("target_hit_strict")) if quality_metrics else None
    )
    return GateResult(
        fires=fires,
        metrics_line=metrics_line,
        rc=rc,
        csv_mtime=csv_mtime,
        gate_started=gate_started,
        ok=ok,
        fail_reason=fail_reason,
        quality_ok=quality_ok,
        target_detected=target_detected,
        quality_metrics=quality_metrics,
        external_classifier_evaluated=bool(quality_metrics),
        test_mid_quality=test_mid_quality,
        test_mid_gap=test_mid_gap,
        test_mid_result=test_mid_result,
        commands=[cmd],
    )


def _evaluation_detail(
    gate: GateResult,
    csv_path: Path,
    artifact_dir: Path,
    *,
    threshold_source: str,
    threshold: str = "",
    flag_meta: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Persist one full Test response and a compact threshold-specific summary."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    archived_csv = artifact_dir / "results.csv"
    rows: list[dict[str, str]] = []
    if csv_path.exists():
        shutil.copy2(csv_path, archived_csv)
        with csv_path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    responses = []
    for index, row in enumerate(rows[:8]):
        responses.append({
            "trial": row.get("trial", str(index)),
            "target_class": row.get("target_class", ""),
            "neuron_fired": row.get("neuron_fired", ""),
            "late_fired": row.get("late_fired", ""),
            "ltz_potential_max": row.get("ltz_potential_max", ""),
            "soma_amp_sum": row.get("soma_amp_sum", ""),
            "neuron_spike_count": row.get("neuron_spike_count", ""),
            "error_class": row.get("error_class", ""),
        })
    fires = "".join(
        "1" if (row.get("neuron_fired") or "0") not in ("0", "0.0", "") else "0"
        for row in rows[:8]
    )
    foil_fires = sum(
        1 for row in rows[1:8]
        if (row.get("neuron_fired") or "0") not in ("0", "0.0", "")
    )
    summary = {
        "threshold_source": threshold_source,
        "threshold": threshold,
        "threshold_selection_result": (flag_meta or {}).get("result", ""),
        "threshold_selection_quality": test_mid_quality_of(flag_meta or {}),
        "threshold_selection_gap": (flag_meta or {}).get("gap", ""),
        "gate_rc": gate.rc,
        "gate_evaluated": gate.external_classifier_evaluated,
        "evaluation_error": gate.fail_reason if not gate.external_classifier_evaluated else "",
        "test_rows": len(rows),
        "fires": fires,
        "target_active": bool(fires[:1] == "1"),
        "foil_false_positives": foil_fires,
        "quality_ok": gate.quality_ok,
        "target_detected": gate.target_detected,
        "quality_metrics": gate.quality_metrics,
        "responses": responses,
        "csv_path": str(archived_csv),
        "csv_sha256": sha256_file(archived_csv) if archived_csv.exists() else "",
    }
    return summary


def run_gate(case: dict, *, run_dir: Path | None = None) -> GateResult:
    """Run normal gate, plus paired threshold diagnostics after Train NonSeparable.

    The paired diagnostics evaluate the same Test inputs two ways: at the
    candidate threshold computed from Train probes, and after the C++ trainer
    performs its inference-mid calibration on Test. Each CSV and C++ flag is
    archived separately; strict C++ Train/Test NonSeparable labels are kept.
    """
    train_flag = case["root"] / "Train" / "posttune_complete.flag"
    train_meta = parse_flag_file(train_flag)
    if train_meta.get("result") not in ("1", "2"):
        return _run_gate_once(case)

    run_dir = run_dir or case["root"] / "diagnostics"
    candidate_text = train_meta.get("candidate_mid", "")
    try:
        candidate_mid = float(candidate_text.replace(",", "."))
    except (AttributeError, ValueError):
        candidate_mid = float("nan")
    try:
        applied_train_mid = float(train_meta.get("mid", "nan").replace(",", "."))
    except (AttributeError, ValueError):
        applied_train_mid = float("nan")
    candidate_available = math.isfinite(candidate_mid) and 0.0 <= candidate_mid < 1.0
    if candidate_available:
        train_eval_threshold = candidate_mid
        train_eval_source = "C++_Train_candidate_mid"
    elif math.isfinite(applied_train_mid) and 0.0 <= applied_train_mid <= 1.0:
        train_eval_threshold = applied_train_mid
        train_eval_source = "C++_Train_applied_mid"
    else:
        train_eval_threshold = float("nan")
        train_eval_source = "unavailable"

    test = case["root"] / "Test"
    diagnostics: dict[str, Any] = {
        "train_result": "separable" if train_meta.get("result") == "1" else "nonseparable",
        "train_candidate_mid": candidate_text,
        "train_candidate_available": candidate_available,
        "train_evaluation_threshold": (
            format(train_eval_threshold, ".17g")
            if math.isfinite(train_eval_threshold) else ""
        ),
        "train_evaluation_threshold_source": train_eval_source,
        "test_threshold_comparison": "train_threshold_vs_cpp_test_calibration",
    }

    with tempfile.TemporaryDirectory(prefix="timelearner-nonseparable-") as tmp:
        baseline_test = Path(tmp) / "Test"
        shutil.copytree(test, baseline_test)

        candidate_gate: GateResult | None = None
        if math.isfinite(train_eval_threshold):
            shutil.rmtree(test)
            shutil.copytree(baseline_test, test)
            candidate_case = dict(case)
            candidate_case["skip_tipr_mid"] = True
            candidate_gate = _run_gate_once(
                candidate_case,
                variant="train_candidate",
                candidate_mid=train_eval_threshold,
            )
            candidate_flag = parse_flag_file(test / "posttune_complete.flag")
            candidate_detail = _evaluation_detail(
                candidate_gate,
                test / "SelectivityLog" / "results.csv",
                run_dir / "Test" / "diagnostics" / "train_candidate",
                threshold_source=train_eval_source,
                threshold=format(train_eval_threshold, ".17g"),
                flag_meta=candidate_flag,
            )
            _copy_if_exists(
                test / "run_posttune_gate.log",
                run_dir / "Test" / "diagnostics" / "train_candidate" / "gate.log",
            )
            diagnostics["train_threshold_test"] = candidate_detail
        else:
            diagnostics["train_threshold_test"] = {
                "threshold_source": "unavailable",
                "threshold": "",
                "gate_evaluated": False,
                "evaluation_error": "train_candidate_and_applied_mid_missing_or_out_of_range",
                "responses": [],
            }

        shutil.rmtree(test)
        shutil.copytree(baseline_test, test)
        cpp_case = dict(case)
        cpp_case["skip_tipr_mid"] = True
        cpp_gate = _run_gate_once(cpp_case, variant="test_cpp_mid")
        cpp_flag_meta = parse_flag_file(test / "posttune_complete.flag")
        try:
            cpp_threshold = format(float(cpp_flag_meta.get("mid", "1")), ".17g")
        except ValueError:
            cpp_threshold = ""
        cpp_detail = _evaluation_detail(
            cpp_gate,
            test / "SelectivityLog" / "results.csv",
            run_dir / "Test" / "diagnostics" / "cpp_test_threshold",
            threshold_source="C++_Test_inference_mid",
            threshold=cpp_threshold,
            flag_meta=cpp_flag_meta,
        )
        _copy_if_exists(
            test / "posttune_complete.flag",
            run_dir / "Test" / "diagnostics" / "cpp_test_threshold" / "posttune_complete.flag",
        )
        _copy_if_exists(
            test / "run_infer_mid.log",
            run_dir / "Test" / "diagnostics" / "cpp_test_threshold" / "infer_mid.log",
        )
        _copy_if_exists(
            test / "run_posttune_gate.log",
            run_dir / "Test" / "diagnostics" / "cpp_test_threshold" / "gate.log",
        )
        diagnostics["cpp_test_threshold"] = cpp_detail
        cpp_gate.diagnostic_evaluations = diagnostics
        cpp_gate.commands = (
            (candidate_gate.commands if candidate_gate is not None else [])
            + cpp_gate.commands
        )
        return cpp_gate


def tipr_class(tipr: str, expect: str = "") -> str:
    """Classify TipR from the vector shape only (never from case/expect name alone)."""
    _ = expect  # call-site compat; classification ignores expect name
    if not tipr or not tipr.strip():
        return "other"
    try:
        nums = [float(x) for x in tipr.replace(",", " ").split()[:4]]
    except ValueError:
        return "other"
    if len(nums) < 4 or any(not math.isfinite(x) for x in nums):
        return "other"
    if tipr_looks_posttuned(tipr):
        if abs(nums[0] - 8.6e7) < 1e5:
            return "flat"
        return "canon"
    return "other"


def tipr_matches_expect(got: str, expect: str) -> bool:
    """True when classified TipR matches case expect_tipr."""
    if expect == "legacy":
        return got in ("legacy", "other")
    if expect in ("keep", "search"):
        # Class comes from vector shape; keep/search are TipR *modes*, not shapes.
        return got in ("canon", "flat", "other")
    return got == expect


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def copy_training_audit(train: Path, run_dir: Path, provenance: dict[str, Any], run_id: str) -> int:
    """Copy the C++ trainer trace into its immutable run bundle and hash it."""
    audit_src = train / "TimeLearnerTrainingAudit.log"
    if not audit_src.is_file():
        return 0
    audit_dst = run_dir / "Train" / audit_src.name
    _copy_if_exists(audit_src, audit_dst)
    with audit_src.open("r", encoding="utf-8", errors="replace") as audit_file:
        audit_records = sum(1 for line in audit_file if line.strip())
    relative_path = f"Train/{audit_dst.name}"
    provenance["training_audit"] = {
        "path": relative_path,
        "schema": 1,
        "records": audit_records,
        "sha256": sha256_file(audit_dst),
    }
    provenance.setdefault("artifacts", []).append(
        {
            "path": relative_path,
            "sha256": sha256_file(audit_dst),
            "run_id": run_id,
            "phase": "train-diagnostics",
        }
    )
    return audit_records


def snapshot_prelaunch_train_configs(
    train: Path, run_dir: Path, branch_rm_profile: dict | None
) -> dict[str, Any]:
    """Preserve and validate the final Train XML immediately before Console starts."""
    snapshot_dir = run_dir / "prelaunch-inputs" / "Train"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, Any] = {}
    profile = {
        int(segment): float(resistance)
        for segment, resistance in (branch_rm_profile or {}).items()
    }
    for filename in ("Model_00.xml", "Parameters_00.xml", "Project.ini", "Interface.xml"):
        source = train / filename
        if not source.is_file() and filename in ("Model_00.xml", "Parameters_00.xml"):
            raise FileNotFoundError(source)
        if not source.is_file():
            continue
        destination = snapshot_dir / filename
        shutil.copy2(source, destination)
        if filename not in ("Model_00.xml", "Parameters_00.xml"):
            files[filename] = {"sha256": sha256_file(destination)}
            continue
        text = source.read_text(encoding="utf-8")
        modes = [value.strip() for value in re.findall(
            r"<StructureBuildMode\b[^>]*>(.*?)</StructureBuildMode>", text, re.S
        )]
        reset_values = [value.strip() for value in re.findall(
            r"<ResetToUntrainedState\b[^>]*>(.*?)</ResetToUntrainedState>", text, re.S
        )]
        if profile and (not modes or any(value != "2" for value in modes)):
            raise ValueError(
                f"Branch Rm profile must skip all StructureBuildMode rebuilds in {source}: {modes}"
            )
        if profile and (not reset_values or any(value != "0" for value in reset_values)):
            raise ValueError(
                f"Branch Rm profile must skip ResetToUntrainedState in {source}: {reset_values}"
            )
        profile_values: dict[str, Any] = {}
        for segment, expected in sorted(profile.items()):
            segment_name = f"Dendrite1_{segment}"
            segment_match = re.search(
                rf"(<{re.escape(segment_name)}\b[^>]*>.*?</{re.escape(segment_name)}\s*>)",
                text,
                re.S,
            )
            if not segment_match:
                raise ValueError(f"{source} has no {segment_name} for requested Rm profile")
            channel_values: dict[str, Any] = {}
            for channel_name in ("ExcChannel", "InhChannel"):
                channel_match = re.search(
                    rf"<{re.escape(channel_name)}\b[^>]*>.*?</{re.escape(channel_name)}\s*>",
                    segment_match.group(1),
                    re.S,
                )
                if not channel_match:
                    raise ValueError(f"{source} has no {segment_name}.{channel_name}")
                values: dict[str, float] = {}
                for field_name in ("Resistance", "FBResistance", "RestingResistance"):
                    matches = re.findall(
                        rf"<{field_name}\b[^>]*>(.*?)</{field_name}>",
                        channel_match.group(0),
                        re.S,
                    )
                    if len(matches) != 1:
                        raise ValueError(
                            f"{source} expected one {field_name} in {segment_name}.{channel_name}"
                        )
                    actual = float(matches[0].strip())
                    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9):
                        raise ValueError(
                            f"{source} {segment_name}.{channel_name}.{field_name}={actual}; "
                            f"requested {expected}"
                        )
                    values[field_name] = actual
                channel_values[channel_name] = values
            profile_values[str(segment)] = channel_values
        files[filename] = {
            "sha256": sha256_file(destination),
            "structure_build_mode": modes,
            "reset_to_untrained_state": reset_values,
            "profile_values": profile_values,
        }
    manifest = {"files": files, "snapshot_dir": str(snapshot_dir)}
    (run_dir / "prelaunch_train_configs.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def snapshot_test_configs(
    test: Path, run_dir: Path, *, label: str = "post-gate"
) -> dict[str, Any]:
    """Save exact Test XML for one point in the evaluation lifecycle."""
    snapshot_dir = run_dir / "effective-inputs" / "Test" / label
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, Any] = {}
    for filename in ("Model_00.xml", "Parameters_00.xml", "Project.ini", "Interface.xml"):
        source = test / filename
        if not source.is_file():
            continue
        destination = snapshot_dir / filename
        shutil.copy2(source, destination)
        files[filename] = {
            "path": f"effective-inputs/Test/{label}/{filename}",
            "sha256": sha256_file(destination),
        }
    return {"files": files, "snapshot_dir": str(snapshot_dir)}


def run_case(
    name: str,
    *,
    skip_train: bool = False,
    run_dir: Path | None = None,
    allow_salvage: bool = False,
    use_archive_inplace: bool = False,
    train_t: float | None = None,
    max_polls: int | None = None,
    no_prune: bool = False,
    snap_every: int = 0,
    slog_abort_gib: float | None = None,
    keep_slog: bool = False,
    autosave_model_s: int = DEFAULT_AUTOSAVE_MODEL_S,
    stall_autosave_n: int = DEFAULT_STALL_AUTOSAVE_N,
    max_rs_rm: float | None = None,
    synapse_resistance_step_ohm: float | None = None,
    tip_synapse_resistance_ohm: float | None = None,
    tip_synapse_resistance_values_ohm: Sequence[float] | None = None,
    disable_train_statistic_logs: bool = False,
) -> dict:
    case = dict(CASES[name])
    if max_rs_rm is not None and (not math.isfinite(max_rs_rm) or max_rs_rm <= 0.0):
        raise ValueError("max_rs_rm must be a finite positive number")
    if synapse_resistance_step_ohm is not None:
        if not math.isfinite(synapse_resistance_step_ohm) or synapse_resistance_step_ohm <= 0.0:
            raise ValueError("synapse_resistance_step_ohm must be a finite positive number")
        if case.get("normalization_mode") != 0:
            raise ValueError(
                "SynapseResistanceStep override is only valid for structural NormalizationMode=0"
            )
    if tip_synapse_resistance_ohm is not None:
        if not math.isfinite(tip_synapse_resistance_ohm) or tip_synapse_resistance_ohm <= 0.0:
            raise ValueError("tip_synapse_resistance_ohm must be a finite positive number")
        if case.get("normalization_mode") != 1:
            raise ValueError(
                "TipSynapseResistance override is only valid for parametric NormalizationMode=1"
            )
    if tip_synapse_resistance_values_ohm is not None:
        if tip_synapse_resistance_ohm is not None:
            raise ValueError("choose either scalar or per-input TipSynapseResistance override")
        if case.get("normalization_mode") != 1:
            raise ValueError(
                "per-input TipSynapseResistance override is only valid for parametric NormalizationMode=1"
            )
        if not tip_synapse_resistance_values_ohm or any(
            not math.isfinite(float(value)) or float(value) <= 0.0
            for value in tip_synapse_resistance_values_ohm
        ):
            raise ValueError("per-input TipSynapseResistance values must be finite and positive")
    if train_t is not None:
        case["train_t"] = float(train_t)
    archive_root: Path = case["root"]
    gold: Path = case["gold"]
    if use_archive_inplace:
        root = archive_root
        work = archive_root
    else:
        work = prepare_clean_case(name, archive_root)
        root = work
        case["root"] = work
    train = root / "Train"
    print(f"\n=== CASE {name} archive={archive_root.name} work={root} ===")
    if train_t is not None or max_polls is not None:
        print(
            f"  override train_t={case['train_t']} max_polls="
            f"{max_polls if max_polls is not None else 'default'}"
        )
    if name == "br100_search" and skip_train:
        raise SystemExit(
            "br100_search: --skip-train forbidden — SearchSynthetic requires Train mode=4"
        )
    if run_dir is None:
        run_dir = make_run_dir(name)
    run_id = run_dir.name
    child_rc: int | None = None
    training_failure: tuple[int, int] | None = None
    params_source = "nm_save"
    provenance_at_launch: dict[str, Any] | None = None
    prepared_train_config_snapshot: dict[str, Any] | None = None
    train_execution: dict[str, Any] = {
        "status": "skipped" if skip_train else "not_started",
        "command": [],
        "cwd": str(train),
        "log": "Train/run_posttune_verify.log",
    }
    tip_mode = str(case.get("posttrain_tip_resistance_mode", {
        "br25_on": "1",
        "br25_off": "0",
        "asym25": "2",
        "br100_keep": "3",
        "br100_search": "4",
        "asym50": "1",
        "phase6_480": "1",
    }.get(name, "1")))
    accept_mode = {
        "br100_search": "search",
        "br100_keep": "keep",
    }.get(name, "cold")
    polls_used: int | None = None
    if not skip_train:
        if case.get("skip_softcold_reset"):
            if (
                case.get("kind") != "branch"
                or not case.get("branch_segment_rm_profile")
                or not case.get("branch_initial_lengths")
            ):
                raise ValueError(
                    "SoftCold reset may only be skipped for an explicit prebuilt Branch Rm diagnostic state"
                )
            print(
                "prebuilt Branch Rm diagnostic state: SoftCold reset skipped; "
                f"lengths={case['branch_initial_lengths']} "
                f"profile={case['branch_segment_rm_profile']}"
            )
        else:
            soft_cold_reset_train(train, autosave_model_s=autosave_model_s)
            profile = case.get("branch_segment_rm_profile")
            if profile and case.get("branch_initial_lengths") is None:
                if {int(segment) for segment in profile} != {1}:
                    raise ValueError(
                        "only a segment-1 Rm profile can be reapplied after standard SoftCold reset"
                    )
                updated = apply_branch_segment_rm_profile_to_train(train, profile)
                print(
                    "Applied Branch segment-1 Rm profile after SoftCold reset to "
                    + ", ".join(updated)
                    + "; ResetToUntrainedState=0 and StructureBuildMode=2 suppress trainer reset/build paths; verify live Rm in C++ audit"
                )
        from repro_cold_lib import ensure_tag_after, sync_estdelay_from_gold

        statistic_components_updated = 0
        if disable_train_statistic_logs:
            for rel in ("Parameters_00.xml", "Model_00.xml"):
                statistic_components_updated += suspend_statistic_matrix_writes(
                    train / rel
                )
            print(
                f"  Suspended file writes for {statistic_components_updated} "
                "UStatisticDoubleMatrix train observer definitions; "
                "C++ iteration audit remains enabled"
            )

        gold_train = case.get("gold")
        if gold_train is not None:
            sync_estdelay_from_gold(train, Path(gold_train) / "Train")

        enable = str(case.get("enable_posttrain_tuning", "0" if name == "br25_off" else "1"))
        for rel in ("Parameters_00.xml", "Model_00.xml"):
            p = train / rel
            if not p.exists():
                continue
            t = p.read_text(encoding="utf-8")
            requested_normalization_mode = case.get("normalization_mode")
            if requested_normalization_mode is not None:
                t = set_tag(t, "NormalizationMode", str(int(requested_normalization_mode)), 1)
            if synapse_resistance_step_ohm is not None:
                step_tag = get_tag(t, "SynapseResistanceStep")
                if step_tag is None:
                    raise ValueError(f"SynapseResistanceStep is missing from {rel}")
                step_text = format(synapse_resistance_step_ohm, ".17g")
                t = set_tag(t, "SynapseResistanceStep", step_text)
            if tip_synapse_resistance_ohm is not None:
                tip_tag = get_tag(t, "TipSynapseResistance")
                if tip_tag is None:
                    raise ValueError(f"TipSynapseResistance is missing from {rel}")
                tip_count = len(tip_tag.replace(",", " ").split())
                if tip_count < 1:
                    raise ValueError(f"TipSynapseResistance is empty in {rel}")
                tip_value = format(tip_synapse_resistance_ohm, ".17g")
                t = set_tag(t, "TipSynapseResistance", " ".join([tip_value] * tip_count))
                # ResetToUntrained seeds the cold tip vector from its saved
                # untrained snapshot, or from SynapseResistanceBase when no
                # snapshot exists. Setting only TipSynapseResistance in XML
                # is therefore overwritten by the C++ reset path. Keep the
                # reference resistance and tip vector aligned for explicit
                # cold-start diagnostics; training logic remains in C++.
                if get_tag(t, "SynapseResistanceBase") is None:
                    raise ValueError(f"SynapseResistanceBase is missing from {rel}")
                t = set_tag(t, "SynapseResistanceBase", tip_value)
            if tip_synapse_resistance_values_ohm is not None:
                tip_tag = get_tag(t, "TipSynapseResistance")
                if tip_tag is None:
                    raise ValueError(f"TipSynapseResistance is missing from {rel}")
                values = [float(value) for value in tip_synapse_resistance_values_ohm]
                tip_count = len(tip_tag.replace(",", " ").split())
                if tip_count != len(values):
                    raise ValueError(
                        f"per-input TipSynapseResistance has {len(values)} values, expected {tip_count} in {rel}"
                    )
                # Preserve SynapseResistanceBase: this diagnostic intentionally
                # varies only trainable input tips and holds the final reference
                # anchor at its historical value. Opt in to the C++ cold-reset
                # contract for this explicit vector; the default reset keeps its
                # saved snapshot or scalar-base behavior.
                t = set_tag(
                    t,
                    "TipSynapseResistance",
                    " ".join(format(value, ".17g") for value in values),
                )
                t = ensure_tag_after(
                    t,
                    "TipSynapseResistance",
                    "UseLoadedTipResistanceOnUntrainedReset",
                    "1",
                    attrs=' Type="b" PType="257" IoType="17"',
                )
                t = set_tag(t, "UseLoadedTipResistanceOnUntrainedReset", "1", 1)
            if max_rs_rm is not None:
                mode = get_tag(t, "NormalizationMode")
                if mode is None or mode.strip() != "1":
                    raise ValueError(
                        f"Rs/Rm diagnostic overrides require parametric NormalizationMode=1: {rel}"
                    )
            if max_rs_rm is not None:
                ratio_text = format(max_rs_rm, ".17g")
                t = ensure_tag_after(
                    t, "NormalizationMode", "MaxSynapseToMembraneResistanceRatio",
                    ratio_text, attrs=' Type="d" PType="257" IoType="17"',
                )
                t = set_tag(t, "MaxSynapseToMembraneResistanceRatio", ratio_text, 1)
            t = ensure_tag_after(t, "IsNeedToTrain", "EnablePostTrainTuning", enable)
            t = set_tag(t, "EnablePostTrainTuning", enable, 1)
            t = ensure_tag_after(
                t, "IterationGap", "AutoScaleIterationGap", "1",
                attrs=' Type="b" PType="257" IoType="17"',
            )
            t = set_tag(t, "AutoScaleIterationGap", "1", 1)
            if enable == "1":
                t = ensure_tag_after(
                    t, "EnablePostTrainTuning", "EnablePostTrainMidThreshold", "1",
                    attrs=' Type="b" PType="257" IoType="17"',
                )
                t = set_tag(t, "EnablePostTrainMidThreshold", "1", 1)
                t = ensure_tag_after(
                    t, "EnablePostTrainMidThreshold", "PostTrainTipResistanceMode", tip_mode,
                    attrs=' Type="i" PType="257" IoType="17"',
                )
                t = set_tag(t, "PostTrainTipResistanceMode", tip_mode, 1)
                t = ensure_tag_after(
                    t, "PostTrainTipResistanceMode", "PostTrainSilentThreshold", "1",
                    attrs=' Type="d" PType="257" IoType="17"',
                )
                t = set_tag(t, "PostTrainSilentThreshold", "1", 1)
                if tip_mode == "4":
                    t = ensure_tag_after(
                        t, "PostTrainSilentThreshold", "PostTrainTipSearchIters", "12",
                        attrs=' Type="i" PType="257" IoType="17"',
                    )
                    t = set_tag(t, "PostTrainTipSearchIters", "12", 1)
            p.write_text(t, encoding="utf-8")
            if max_rs_rm is not None:
                print(
                    f"  Rs/Rm max override {rel}: max={max_rs_rm}"
                )
            if synapse_resistance_step_ohm is not None:
                print(
                    f"  structural SynapseResistanceStep override {rel}: "
                    f"{format(synapse_resistance_step_ohm, '.17g')} Ohm"
                )
            if tip_synapse_resistance_ohm is not None:
                print(
                    f"  parametric cold-start Rs override {rel}: "
                    f"SynapseResistanceBase and every TipSynapseResistance="
                    f"{format(tip_synapse_resistance_ohm, '.17g')} Ohm"
                )
            if tip_synapse_resistance_values_ohm is not None:
                print(
                    f"  parametric per-input cold-start Rs override {rel}: "
                    f"TipSynapseResistance={' '.join(format(float(value), '.17g') for value in tip_synapse_resistance_values_ohm)} Ohm; "
                    "SynapseResistanceBase preserved"
                )
            print(
                f"  PostTune tags {rel}: enable={enable} mode="
                f"{get_tag(p.read_text(encoding='utf-8'), 'PostTrainTipResistanceMode')} "
                f"auto_gap="
                f"{get_tag(p.read_text(encoding='utf-8'), 'AutoScaleIterationGap')}"
            )
        # SoftCold emits this contract before experiment-only overrides.
        # Refresh it now so it describes the exact XML that C++ will load.
        write_cold_reset_contract(train, mode="soft")
        config_sha_before = {
            "Train/Parameters_00.xml": sha256_file(train / "Parameters_00.xml"),
            "Train/Model_00.xml": sha256_file(train / "Model_00.xml"),
            "Test/Parameters_00.xml": sha256_file(root / "Test" / "Parameters_00.xml"),
            "Test/Model_00.xml": sha256_file(root / "Test" / "Model_00.xml"),
        }
        config_sha256 = config_sha_before["Train/Parameters_00.xml"]
        prepared_train_config_snapshot = snapshot_prelaunch_train_configs(
            train,
            run_dir,
            case.get("branch_segment_rm_profile"),
        )
        # Capture executable, source, gitlinks, and effective XML immediately
        # before launching C++. Computing these only after the run would hide
        # source or binary changes that happened during a long experiment.
        provenance_at_launch = build_provenance(
            root,
            case=name,
            run_id=run_id,
            config_sha_before=config_sha_before,
            params_source=params_source,
        )
        if prepared_train_config_snapshot is not None:
            provenance_at_launch["prelaunch_train_config_snapshot"] = (
                prepared_train_config_snapshot
            )
        polls = (
            int(max_polls)
            if max_polls is not None
            else (800 if name == "br100_search" else 401)
        )
        polls_used = polls
        abort_gib = (
            float(slog_abort_gib)
            if slog_abort_gib is not None
            else (8.0 if no_prune else 3.0)
        )
        train_execution.update(
            {
                "command": [
                    str(NM), "-c", str(train / "Project.ini"), "-s", "-t",
                    str(case["train_t"]), "-x", "-S",
                ],
                "cwd": str(train),
                "started_utc": datetime.now(timezone.utc).isoformat(),
                "time_limit_sim_s": float(case["train_t"]),
                "max_polls": polls,
                "poll_interval_s": 30,
                "statistic_log_abort_gib": abort_gib,
                "autosave_model_s": autosave_model_s,
                "stall_autosave_n": stall_autosave_n,
            }
        )
        status, child_rc = wait_need0(
            train,
            case["train_t"],
            train / "run_posttune_verify.log",
            max_polls=polls,
            allow_salvage=allow_salvage,
            no_prune=no_prune,
            snap_every=snap_every,
            slog_abort_gib=abort_gib,
            early_stop_autosave=autosave_model_s > 0,
            stall_autosave_n=stall_autosave_n,
        )
        train_execution.update(
            {
                "finished_utc": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "return_code": child_rc,
            }
        )
        if status.startswith("cpp_training_failure_"):
            training_failure = runtime_training_failure_from_audit(train)
            if training_failure is None:
                try:
                    training_failure = (-1, int(status.rsplit("_", 1)[1]))
                except ValueError:
                    training_failure = (-1, -1)
        if allow_salvage:
            params_source = flush_posttune_artifacts(train)
            if params_source == "none":
                params_source = "nm_save"
        elif status == "done_flag_flush":
            params_source = "flag_flush"
        else:
            params_source = "nm_save"
    else:
        status = "skip_train"
        train_execution.update(
            {
                "finished_utc": datetime.now(timezone.utc).isoformat(),
                "reason": "--skip-train",
            }
        )
        config_sha256 = sha256_file(train / "Parameters_00.xml")
        config_sha_before = {"Train/Parameters_00.xml": config_sha256}

    if prepared_train_config_snapshot is None:
        prepared_train_config_snapshot = snapshot_prelaunch_train_configs(
            train,
            run_dir,
            case.get("branch_segment_rm_profile"),
        )

    initial_tip_reset_check = None
    if not skip_train and tip_synapse_resistance_values_ohm is not None:
        initial_tip_reset_check = runtime_loaded_tip_reset_check(train)
        if not initial_tip_reset_check.get("passed"):
            status = "initial_tip_resistance_reset_mismatch"
            print(
                "  INVALID_INITIAL_TIPR_RESET "
                + json.dumps(initial_tip_reset_check, ensure_ascii=False)
            )

    after = snap_params(train / "Parameters_00.xml")
    train_flag = train / "posttune_complete.flag"
    test_flag = root / "Test" / "posttune_complete.flag"
    # Never seed Test mid from archive; workdir should already lack Test flag.
    if test_flag.exists() and not skip_train:
        # Only keep if produced by this run's gate/inference later.
        pass
    phase = load_phase_meta(train_flag, test_flag)

    if phase.test.get("mid"):
        after["FixedLTZThreshold"] = phase.test["mid"].split()[0]
    elif phase.train.get("mid"):
        after["FixedLTZThreshold"] = phase.train["mid"].split()[0]

    gold_test = snap_params(gold / "Test" / "Parameters_00.xml")
    stage0_audit = runtime_stage0_fields_from_audit(train)
    training_convergence = classify_training_convergence(
        after.get("IsNeedToTrain", ""),
        phase.train,
        skipped=(status == "skip_train"),
        cpp_failure=training_failure,
        child_rc=child_rc,
    )
    if initial_tip_reset_check is not None and not initial_tip_reset_check.get("passed"):
        training_convergence = "initial_resistance_reset_mismatch"
    test_pre_gate_snapshot = snapshot_test_configs(
        root / "Test", run_dir, label="pre-gate"
    )
    test_gate_invoked_utc = datetime.now(timezone.utc).isoformat()
    if should_run_quality_gate(training_convergence):
        gate = run_gate(case, run_dir=run_dir)
    else:
        skip_gate_reason = (
            "not_evaluated_execution_error"
            if training_convergence == "execution_error"
            else "not_evaluated_initial_resistance_reset_mismatch"
            if training_convergence == "initial_resistance_reset_mismatch"
            else "not_evaluated_training_incomplete"
        )
        gate = GateResult(
            fires="",
            metrics_line=skip_gate_reason,
            rc=None,
            csv_mtime=None,
            gate_started=time.time(),
            ok=None,
            fail_reason=skip_gate_reason,
            evaluated=False,
            external_classifier_evaluated=False,
        )
        print(
            f"  SKIP_GATE training_convergence={training_convergence}; "
            "model is not in a terminal training state"
        )
    test_gate_finished_utc = datetime.now(timezone.utc).isoformat()
    test_post_gate_snapshot = snapshot_test_configs(
        root / "Test", run_dir, label="post-gate"
    )
    phase = load_phase_meta(train_flag, test_flag)
    if phase.test.get("mid"):
        after["FixedLTZThreshold"] = phase.test["mid"].split()[0]
    tp = snap_params(root / "Test" / "Parameters_00.xml")
    try:
        thr_f = float((tp.get("FixedLTZThreshold") or "1").replace(",", "."))
    except ValueError:
        thr_f = 1.0
    if math.isfinite(thr_f) and thr_f < 0.9:
        after["FixedLTZThreshold"] = tp["FixedLTZThreshold"]

    mid_meta = dict(phase.test) if phase.test else dict(phase.train)
    mid_src = mid_source_of(mid_meta, after.get("FixedLTZThreshold", ""))
    posttune_quality = classify_posttune_quality(phase.train)
    detection_quality = classify_detection_quality(
        gate_evaluated=gate.evaluated,
        gate_ok=gate.ok,
        target_detected=gate.target_detected,
        training_convergence=training_convergence,
        test_mid_quality=gate.test_mid_quality,
        external_classifier_evaluated=gate.external_classifier_evaluated,
    )
    separation_quality = classify_separation_quality(
        gate_evaluated=gate.evaluated,
        gate_ok=gate.ok,
        quality_ok=gate.quality_ok,
        training_convergence=training_convergence,
        test_mid_quality=gate.test_mid_quality,
        external_classifier_evaluated=gate.external_classifier_evaluated,
    )
    search_reverted = phase.search_reverted
    mode4_n = count_events_mode4(train) + count_events_mode4(root / "Test")

    tipr_snapshot = (
        phase.train.get("tipr_snapshot")
        or collect_posttune_salvage(train).tipr_snapshot
        or ""
    )
    tipr_final = after.get("TipSynapseResistance", "") or phase.train.get("tipr", "")
    tipr_vs = ""
    tipr_vs_keep_info = ""
    own_keep_snapshot = ""
    if name == "br100_search":
        tipr_vs = tipr_vs_snapshot(
            tipr_final, tipr_snapshot, search_reverted=search_reverted
        )
        keep_root = ROOT / "SelectivityBranch" / "EXP_br_span100_packA_gen_C1e9_posttune_keep"
        tipr_keep = snap_params(keep_root / "Train" / "Parameters_00.xml").get(
            "TipSynapseResistance", ""
        ) or snap_params(keep_root / "Test" / "Parameters_00.xml").get(
            "TipSynapseResistance", ""
        )
        tipr_vs_keep_info = tipr_vs_keep(tipr_final, tipr_keep, search_reverted)
        if mode4_n < 1 and status != "skip_train":
            print(f"  WARN mode4 EventsLog count={mode4_n}")
        if tipr_vs == "same_FAIL":
            status = "search_same_as_snapshot_FAIL"
        elif tipr_vs == "same_reverted":
            status = "done_search_reverted"
        elif tipr_vs == "applied_best":
            status = "done_search_applied"
        elif tipr_vs in ("diff_after_revert", "unknown"):
            status = f"search_{tipr_vs}_FAIL"
        elif tipr_vs == "diff":
            status = "done_search_diff"
        if mid_src != "cpp":
            status = f"{status}_no_cpp_mid"
    elif name == "br100_keep":
        own_keep_snapshot = tipr_final
        tipr_vs = tipr_vs_snapshot(tipr_final, tipr_final, search_reverted=False)

    if gate.evaluated and gate.fail_reason == "test_mid_nonseparable":
        status = f"{status}_test_mid_nonseparable"
    elif gate.evaluated and not gate.ok:
        status = f"{status}_gate_FAIL_{gate.fail_reason}"

    fires = gate.fires if gate.evaluated and gate.ok else ""
    metrics_line = (
        gate.metrics_line
        if gate.evaluated and (gate.ok or gate.fail_reason == "test_mid_nonseparable")
        else gate.fail_reason or gate.metrics_line
    )

    _copy_if_exists(train_flag, run_dir / "Train" / "posttune_complete.flag")
    _copy_if_exists(test_flag, run_dir / "Test" / "posttune_complete.flag")
    csv_src = root / "Test" / "SelectivityLog" / "results.csv"
    _copy_if_exists(csv_src, run_dir / "Test" / "results.csv")
    (run_dir / "Train").mkdir(parents=True, exist_ok=True)
    (run_dir / "Test").mkdir(parents=True, exist_ok=True)
    test_trace_src = root / "Test" / "SelectivityLog" / "test_trace.csv"
    test_trace_dst = run_dir / "Test" / "test_trace.csv"
    _copy_if_exists(test_trace_src, test_trace_dst)
    test_model_snapshot = run_dir / "effective-inputs" / "Test" / "post-gate" / "Model_00.xml"
    trace_enabled_in_test_config = (
        get_tag(test_model_snapshot.read_text(encoding="utf-8"), "TraceLogEnabled") == "1"
        if test_model_snapshot.is_file() else False
    )
    execution_logs: list[dict[str, Any]] = []
    for source in (
        train / "run_posttune_verify.log",
        *sorted((root / "Test").glob("run_*.log")),
    ):
        if not source.is_file():
            continue
        phase_name = "Train" if source.parent == train else "Test"
        destination = run_dir / phase_name / "script-logs" / source.name
        _copy_if_exists(source, destination)
        execution_logs.append(
            {
                "path": destination.relative_to(run_dir).as_posix(),
                "source_path": str(source),
                "sha256": sha256_file(destination),
            }
        )
    if tipr_snapshot:
        (run_dir / "Train" / "tipr_snapshot.txt").write_text(
            tipr_snapshot + "\n", encoding="utf-8"
        )
    if tipr_final:
        (run_dir / "Train" / "tipr_final.txt").write_text(tipr_final + "\n", encoding="utf-8")
    expect_tipr_applicable = should_check_tipr_expectation(
        {
            "normalization_mode": case.get("normalization_mode"),
            "enable_posttrain_tuning": enable if not skip_train else None,
        }
    )
    expect_tipr = case["expect_tipr"] if expect_tipr_applicable else "not_applicable"
    got_tipr_class = tipr_class(tipr_final, expect_tipr)
    provenance = provenance_at_launch or build_provenance(
        root,
        case=name,
        run_id=run_id,
        config_sha_before=config_sha_before,
        params_source=params_source,
    )
    source_paths = [NMSDK_ROOT / rel for rel in PROVENANCE_SOURCE_REL]
    source_sha_after = sha256_paths(source_paths)
    binary_sha_after = sha256_file(NM)
    config_sha_after = {
        "Train/Parameters_00.xml": sha256_file(train / "Parameters_00.xml"),
        "Train/Model_00.xml": sha256_file(train / "Model_00.xml"),
        "Test/Parameters_00.xml": sha256_file(root / "Test" / "Parameters_00.xml"),
        "Test/Model_00.xml": sha256_file(root / "Test" / "Model_00.xml"),
    }
    run_input_changes = compare_run_inputs(
        provenance,
        source_sha_after=source_sha_after,
        binary_sha_after=binary_sha_after,
        config_sha_before=config_sha_before,
        config_sha_after=config_sha_after,
    )
    provenance.update(
        {
            "config_sha256": config_sha256,
            "config_sha256_after": config_sha_after,
            "source_sha256_after": source_sha_after,
            "binary_sha256_after": binary_sha_after,
            **run_input_changes,
            "params_source": params_source,
            "weights_identity": tipr_weights_identity(train, params_source=params_source),

            "train_status": status,
            "trainer": case.get("kind"),
            "experiment_spec": {
                "trainer": case.get("kind"),
                "span_ms": case.get("span_ms"),
                "normalization_mode": case.get("normalization_mode"),
                "presynaptic_inhibition": case.get("presynaptic_inhibition"),
                "presynaptic_coefficient": case.get("presynaptic_coefficient"),
                "enable_posttrain_tuning": enable if not skip_train else None,
            },
            "training_convergence": training_convergence,
            "training_failure_phase": (
                training_failure[0]
                if training_failure is not None and training_failure[0] >= 0
                else None
            ),
            "training_failure_reason": (
                training_failure[1] if training_failure is not None else None
            ),
            "posttune_quality": posttune_quality,
            "detection_quality": detection_quality,
            "posttune_result": phase.train.get("result", ""),
            "train_candidate_mid": phase.train.get("candidate_mid", ""),
            "diagnostic_test_evaluations": gate.diagnostic_evaluations,
            "child_rc": child_rc,
            "train_t_effective": float(case["train_t"]),
            "max_polls": polls_used,
            "train_statistic_logs_disabled": disable_train_statistic_logs,
            "retest_class": (
                "extended_time"
                if (train_t is not None or max_polls is not None)
                else "standard"
            ),
            "search_reverted_train": int(search_reverted),
            "tipr_vs_snapshot": tipr_vs,
            "tipr_class": got_tipr_class,
            "expect_tipr": expect_tipr,
            "mid_source": mid_src,
            "gate_rc": gate.rc,
            "gate_ok": gate.ok,
            "gate_evaluated": gate.evaluated,
            "quality_class": "salvaged" if allow_salvage else "calibration-quality",
            "work_root": str(root),
            "archive_root": str(archive_root),
            "artifacts": [
                {
                    "path": "Train/posttune_complete.flag",
                    "sha256": sha256_file(train_flag),
                    "run_id": run_id,
                    "phase": "train",
                },
                {
                    "path": "Test/posttune_complete.flag",
                    "sha256": sha256_file(test_flag),
                    "run_id": run_id,
                    "phase": "test",
                },
                {
                    "path": "Test/results.csv",
                    "sha256": sha256_file(csv_src),
                    "run_id": run_id,
                    "phase": "gate",
                },
            ],
        }
    )
    provenance.update(
        {
            "experiment_started_utc": provenance.get("started_utc"),
            "test_gate_started_utc": test_gate_invoked_utc,
            "test_gate_finished_utc": test_gate_finished_utc,
            "experiment_finished_utc": datetime.now(timezone.utc).isoformat(),
            "test_config_snapshots": {
                "pre_gate": test_pre_gate_snapshot,
                "post_gate": test_post_gate_snapshot,
            },
            "script_execution": {
                "orchestrator": {
                    "script": str(Path(__file__).resolve()),
                    "interpreter": sys.executable,
                    "argv": list(sys.argv),
                    "cwd": os.getcwd(),
                },
                "training": train_execution,
                "test_gate": {
                    "commands": gate.commands,
                    "started_utc": test_gate_invoked_utc,
                    "finished_utc": test_gate_finished_utc,
                    "evaluated": gate.evaluated,
                    "return_code": gate.rc,
                    "ok": gate.ok,
                    "fail_reason": gate.fail_reason,
                    "classifier_evaluated": gate.external_classifier_evaluated,
                    "metrics_line": gate.metrics_line,
                    "metrics": gate.quality_metrics,
                },
                "logs": execution_logs,
            },
            "test_trace": {
                "enabled_in_test_config": trace_enabled_in_test_config,
                "path": "Test/test_trace.csv" if test_trace_dst.is_file() else None,
                "rows": max(0, sum(1 for _ in test_trace_dst.open(encoding="utf-8", errors="replace")) - 1)
                if test_trace_dst.is_file() else 0,
                "sha256": sha256_file(test_trace_dst),
                "missing_reason": None if test_trace_dst.is_file() else "trace_not_emitted_by_test_console",
            },
        }
    )
    if test_trace_dst.is_file():
        provenance.setdefault("artifacts", []).append(
            {
                "path": "Test/test_trace.csv",
                "sha256": sha256_file(test_trace_dst),
                "run_id": run_id,
                "phase": "test-waveform",
            }
        )
    provenance.setdefault("artifacts", []).extend(
        {
            "path": item["path"],
            "sha256": item["sha256"],
            "run_id": run_id,
            "phase": "script-log",
        }
        for item in execution_logs
    )
    for snapshot in (test_pre_gate_snapshot, test_post_gate_snapshot):
        for item in snapshot.get("files", {}).values():
            provenance.setdefault("artifacts", []).append(
                {
                    "path": item["path"],
                    "sha256": item["sha256"],
                    "run_id": run_id,
                    "phase": "test-config",
                }
            )
    copy_training_audit(train, run_dir, provenance, run_id)
    # Placeholder; overwritten after accept_run with failure_class.
    provenance["failure_class"] = "pending"
    (run_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    if (root / "inputs_manifest.json").exists():
        _copy_if_exists(root / "inputs_manifest.json", run_dir / "inputs_manifest.json")
    _copy_if_exists(train / "cold_reset_contract.json", run_dir / "Train" / "cold_reset_contract.json")

    for side in (train, root / "Test"):
        for dname in ("StatisticLog", "EventsLog"):
            d = side / dname
            if d.is_dir():
                if keep_slog and dname == "StatisticLog" and side == train:
                    print(f"  KEEP_SLOG {d} (--keep-slog)")
                    continue
                shutil.rmtree(d, ignore_errors=True)

    expect_fires = case.get("expect_fires", "10000000")
    need = after.get("IsNeedToTrain", "0")
    row = {
        "case": name,
        "trainer": case.get("kind"),
        "experiment_spec": {
            "trainer": case.get("kind"),
            "span_ms": case.get("span_ms"),
            "normalization_mode": case.get("normalization_mode"),
            "presynaptic_inhibition": case.get("presynaptic_inhibition"),
            "presynaptic_coefficient": case.get("presynaptic_coefficient"),
        },
        "normalization_mode": case.get("normalization_mode"),
        "enable_posttrain_tuning": enable if not skip_train else None,
        "posttrain_tip_resistance_mode": tip_mode,
        "presynaptic_inhibition": case.get("presynaptic_inhibition"),
        "presynaptic_coefficient": case.get("presynaptic_coefficient"),
        "train_status": status,
        "training_convergence": training_convergence,
        "training_failure_phase": (
            training_failure[0]
            if training_failure is not None and training_failure[0] >= 0
            else None
        ),
        "training_failure_reason": (
            training_failure[1] if training_failure is not None else None
        ),
        "initial_tip_resistance_reset_check": initial_tip_reset_check,
        "posttune_quality": posttune_quality,
        "train_candidate_mid": phase.train.get("candidate_mid", ""),
        "diagnostic_test_evaluations": gate.diagnostic_evaluations,
        "separation_quality": separation_quality,
        "detection_quality": detection_quality,
        "after": after,
        "gold_thr": gold_test.get("FixedLTZThreshold", ""),
        "gold_tipr": gold_test.get("TipSynapseResistance", ""),
        "tipr_class": got_tipr_class,
        "fires": fires,
        "metrics": metrics_line,
        "expect_tipr": expect_tipr,
        "tipr_expectation_applicable": expect_tipr_applicable,
        "expect_fires": expect_fires,
        "mid_source": mid_src,
        "tipr_vs_snapshot": tipr_vs,
        "tipr_vs_keep": tipr_vs_keep_info,
        "search_reverted": int(search_reverted),
        "mode4_events": mode4_n,
        "params_source": params_source,
        "run_dir": str(run_dir),
        "gate_rc": gate.rc,
        "gate_ok": gate.ok,
        "gate_evaluated": gate.evaluated,
        "quality_gate_ok": gate.quality_ok,
        "target_detected": gate.target_detected,
        "quality_metrics": gate.quality_metrics,
        "external_classifier_evaluated": gate.external_classifier_evaluated,
        "classifier_evaluation": classifier_evaluation_status(gate),
        "test_mid_quality": gate.test_mid_quality,
        "test_mid_gap": gate.test_mid_gap,
        "test_mid_result": gate.test_mid_result,
        "own_keep_snapshot": own_keep_snapshot,
        "require_cpp_mid": name in ("asym50", "phase6_480", "br100_search"),
        "child_rc": child_rc,
    }
    if stage0_audit:
        for key in (
            "delay_residue",
            "amp_over_target",
            "sync_exit",
            "amp_be",
            "done_be",
            "sep_margin",
            "sep_gap",
            "sep_tgt",
            "sep_max_foil",
        ):
            if key in stage0_audit:
                row[key] = stage0_audit[key]
        row["training_audit_stage0"] = stage0_audit
    ok, fail_notes = accept_run(
        row,
        expect_fires=expect_fires,
        expect_tipr=expect_tipr,
        mode=accept_mode,
        need=need or "0",
        child_rc=child_rc,
        skip_train=skip_train,
    )
    if initial_tip_reset_check is not None and not initial_tip_reset_check.get("passed"):
        ok = False
        note = "initial_tip_resistance_reset_mismatch"
        if note not in fail_notes:
            fail_notes.append(note)
    if gate.evaluated and not gate.ok and gate.fail_reason not in fail_notes:
        fail_notes.append(gate.fail_reason)
    if gate.evaluated and gate.ok and gate.quality_ok is False:
        fail_notes.append("separation_quality_fail")
    if gate.evaluated and gate.ok and gate.target_detected is False:
        fail_notes.append("target_not_detected")
    failure_class = classify_failure_class(fail_notes, row)
    row["row_fail"] = not ok
    row["fail_notes"] = fail_notes
    row["failure_class"] = failure_class
    # Refresh provenance with final failure_class (file already written earlier).
    try:
        prov_path = run_dir / "provenance.json"
        if prov_path.exists():
            prov = json.loads(prov_path.read_text(encoding="utf-8"))
            prov["failure_class"] = failure_class
            prov["fail_notes"] = fail_notes
            # Parallel workers skip the shared markdown summary; keep their
            # complete convergence/quality row beside the immutable run data.
            prov["result"] = row
            prov_path.write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    return row


def count_events_mode4(side: Path) -> int:
    elog = side / "EventsLog"
    if not elog.is_dir():
        return 0
    n = 0
    for p in elog.rglob("*"):
        if not p.is_file():
            continue
        try:
            # Event logs can grow to many GiB during a long Branch run. Stream
            # them so post-processing cannot OOM by materializing one log.
            with p.open("r", encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    n += len(re.findall(r"phase\s*->\s*PostTune\s+mode=4", line))
                    n += len(re.findall(r"PostTune mode=4", line))
        except OSError:
            continue
    return n


def verdict_rows(rows: list[dict]) -> int:
    """Return 0 if all ok, 1 if any FAIL."""
    for r in rows:
        if r.get("row_fail"):
            return 1
        if "FAIL" in str(r.get("train_status", "")):
            return 1
        if "gold_mid" in str(r.get("train_status", "")):
            return 1
    return 0


def append_result(rows: list[dict]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PostTune verify result",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"Console: `{NM}`",
        "",
        "For terminal C++ Train PostTune results, Test diagnostics report both the frozen Train-derived threshold and the threshold selected by the C++ inference calibration on Test. These are separate measurements; neither changes Train convergence or the strict C++ `NonSeparable` result. Full per-pattern responses, metrics, CSV paths, and hashes are stored in each run's `provenance.json` and diagnostic artifacts.",
        "",
        "| case | training convergence | Train PostTune | Test mid | external classifier | target detection | Need | TipR class | mid_source | fires | Test threshold diagnostics | metrics |",
        "|------|-----------------------|----------------|----------|---------------------|------------------|------|------------|------------|-------|----------------------------|---------|",
    ]
    for r in rows:
        a = r["after"]
        diagnostic = r.get("diagnostic_test_evaluations") or {}
        diagnostic_parts = []
        for key, label in (
            ("train_threshold_test", "Train-frozen"),
            ("cpp_test_threshold", "C++-Test"),
        ):
            detail = diagnostic.get(key) or {}
            if not detail:
                continue
            if detail.get("threshold_source") == "unavailable":
                diagnostic_parts.append(f"{label}: unavailable")
                continue
            target = detail.get("target_active")
            target_text = "yes" if target is True else "no" if target is False else "n/a"
            quality = detail.get("quality_ok")
            quality_text = "PASS" if quality is True else "FAIL" if quality is False else "n/a"
            diagnostic_parts.append(
                f"{label} thr={detail.get('threshold', '')}; fires={detail.get('fires', '')}; "
                f"target={target_text}; foilFP={detail.get('foil_false_positives', 'n/a')}; "
                f"quality={quality_text}"
            )
        diagnostic_text = " / ".join(diagnostic_parts) or "not_run"
        lines.append(
            "| {case} | {conv} | {post} | {test_mid} | {classifier} | {detect} | {need} | {tc} | {ms} | `{fires}` | {test_diagnostics} | {met} |".format(
                case=r["case"],
                conv=r.get("training_convergence", "insufficient_data"),
                post=r.get("posttune_quality", "not_reached_or_unknown"),
                test_mid=r.get("test_mid_quality", "not_available"),
                classifier=r.get("classifier_evaluation", "not_run"),
                detect=r.get("detection_quality", "insufficient_data"),
                need=a.get("IsNeedToTrain", ""),
                tc=r["tipr_class"],
                ms=r.get("mid_source", ""),
                fires=r["fires"],
                test_diagnostics=diagnostic_text.replace("|", "/"),
                met=(r["metrics"] or "")[:80].replace("|", "/"),
            )
        )
        for note in r.get("fail_notes") or []:
            lines.append("")
            lines.append(f"**FAIL**: `{r['case']}` — {note}.")
        if "gold_mid" in str(r.get("train_status", "")):
            lines.append("")
            lines.append(f"**FAIL**: `{r['case']}` used gold_mid fallback — not allowed.")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("WROTE", OUT)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", choices=list(CASES) + ["all"], default="all")
    ap.add_argument("--skip-train", action="store_true")
    ap.add_argument(
        "--allow-salvage",
        action="store_true",
        help="Controlled salvage of live/flag into Parameters (not cold PASS)",
    )
    ap.add_argument(
        "--use-archive-inplace",
        action="store_true",
        help="Debug only: mutate EXP_* archive instead of clean workdir",
    )
    ap.add_argument(
        "--train-t",
        type=float,
        default=None,
        help="Override CASES[].train_t for SoftCold Train -t (extended-time)",
    )
    ap.add_argument(
        "--max-polls",
        type=int,
        default=None,
        help="Override wait_need0 max_polls (raise with --train-t)",
    )
    ap.add_argument(
        "--no-prune",
        action="store_true",
        help="Keep StatisticLog when >2G (abort still >3G); for AmpDt diagnostics",
    )
    ap.add_argument(
        "--snap-every",
        type=int,
        default=0,
        help="Every N polls SNAP tipr/L from traces into posttune_tipr_live.txt",
    )
    ap.add_argument(
        "--slog-abort-gib",
        type=float,
        default=None,
        help="StatisticLog abort threshold GiB (default 3; with --no-prune default 8)",
    )
    ap.add_argument(
        "--keep-slog",
        action="store_true",
        help="Do not rmtree Train/StatisticLog after case (AmpNorm diagnostics)",
    )
    ap.add_argument(
        "--autosave-model-s",
        type=int,
        default=DEFAULT_AUTOSAVE_MODEL_S,
        help=(
            "ProjectAutoSaveModelTimeInterval for SoftCold Train Project.ini "
            f"(model-seconds; default {DEFAULT_AUTOSAVE_MODEL_S}; 0=off)"
        ),
    )
    ap.add_argument(
        "--stall-autosave-n",
        type=int,
        default=DEFAULT_STALL_AUTOSAVE_N,
        help=(
            "Abort Train after N consecutive autosaves with TipR@ResistanceMax "
            f"and unchanged L while Need!=0 (default {DEFAULT_STALL_AUTOSAVE_N}; 0=off)"
        ),
    )
    ap.add_argument(
        "--max-rs-rm",
        type=float,
        default=None,
        help="Diagnostic override for MaxSynapseToMembraneResistanceRatio",
    )
    ap.add_argument(
        "--no-result-md",
        action="store_true",
        help="Skip writing POSTTUNE_VERIFY_RESULT.md (parallel SoftCold workers)",
    )
    args = ap.parse_args()
    names = list(CASES) if args.case == "all" else [args.case]
    rows = [
        run_case(
            n,
            skip_train=args.skip_train,
            allow_salvage=args.allow_salvage,
            use_archive_inplace=args.use_archive_inplace,
            train_t=args.train_t,
            max_polls=args.max_polls,
            no_prune=args.no_prune,
            snap_every=args.snap_every,
            slog_abort_gib=args.slog_abort_gib,
            keep_slog=args.keep_slog,
            autosave_model_s=args.autosave_model_s,
            stall_autosave_n=args.stall_autosave_n,
            max_rs_rm=args.max_rs_rm,
        )
        for n in names
    ]
    if not args.no_result_md:
        append_result(rows)
    sys.exit(verdict_rows(rows))


if __name__ == "__main__":
    main()

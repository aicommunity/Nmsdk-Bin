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
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Sequence

ROOT = Path(__file__).resolve().parents[1]
NMSDK_ROOT = Path(__file__).resolve().parents[5]
PROVENANCE_SOURCE_REL = (
    "Libraries/Nmsdk-PulseLib/Core/NPatternResponseAnalyzer.cpp",
    "Libraries/Nmsdk-PulseLib/Core/NNeuronPostTrainTune.cpp",
    "Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearnerBranch.cpp",
    "Rdk/GUI/Qt/UModernDiagramLinkRouter.cpp",
    "App/NeuroModelerConsole/main.cpp",
)
sys.path.insert(0, str(ROOT / "scripts"))
from repro_cold_lib import (  # noqa: E402
    NM,
    assert_disk_for_train,
    free_gib,
    get_tag,
    set_tag,
    soft_cold_reset_train,
    tipr_looks_posttuned,
)

PHASE8 = ROOT / "SelectivityBranch" / "scripts" / "phase8_tiprmin_gate.py"
PHASE9 = ROOT / "SelectivityAsymRm" / "scripts" / "phase9_preinh_bc_gate.py"
METRICS = ROOT / "scripts" / "selectivity_metrics.py"
OUT = ROOT / "_repro" / "POSTTUNE_VERIFY_RESULT.md"
RUNS_ROOT = ROOT / "_repro" / "runs"

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
        "train_t": 320.0,
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
    rc: int
    csv_mtime: float | None
    gate_started: float
    ok: bool
    fail_reason: str = ""


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


def make_run_dir(case: str, root: Path | None = None) -> Path:
    base = root if root is not None else RUNS_ROOT
    utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    d = base / f"{case}_{utc}"
    (d / "Train").mkdir(parents=True, exist_ok=True)
    (d / "Test").mkdir(parents=True, exist_ok=True)
    return d


def classify_slog_gib(gib: float) -> Literal["ok", "prune", "abort"]:
    """Abort threshold before prune; doc says abort ~3G."""
    if gib > 3.0:
        return "abort"
    if gib > 2.0:
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
            t = set_tag(t, "ResistanceMin", "20000000", 1)
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


def wait_need0(train: Path, tlim: float, log: Path, *, max_polls: int = 401) -> str:
    ini = train / "Project.ini"
    assert_disk_for_train()
    slog = train / "StatisticLog"
    if slog.is_dir():
        shutil.rmtree(slog, ignore_errors=True)
    flag = train / "posttune_complete.flag"
    if flag.exists():
        flag.unlink()
    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(tlim), "-x", "-S"]
    print(f"TRAIN {train.parent.name} -t {tlim} Avail={free_gib():.0f}G polls={max_polls}")
    proc = subprocess.Popen(cmd, cwd=str(train), stdout=log.open("w"), stderr=subprocess.STDOUT)
    need0 = False
    for i in range(1, max_polls + 1):
        time.sleep(30)
        if proc.poll() is not None:
            break
        need = get_tag((train / "Parameters_00.xml").read_text(encoding="utf-8"), "IsNeedToTrain")
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
            f"slog={slog_gib:.2f}G et~{i * 30}s"
        )
        action = classify_slog_gib(slog_gib)
        if action == "abort":
            print(f"  ABORT StatisticLog>{slog_gib:.1f}G — terminate NM")
            proc.terminate()
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
            break
        if action == "prune":
            stat_dir = _latest_stat_dir(train)
            tipr = _last_trace_vector(stat_dir, "TipSynapseResistanceTrace") if stat_dir else None
            lens = _last_trace_vector(stat_dir, "DendriteLengthTrace") if stat_dir else None
            live = train / "posttune_tipr_live.txt"
            parts = []
            if tipr:
                parts.append("tipr=" + " ".join(tipr[:4]))
            if lens:
                parts.append("L=" + " ".join(str(int(float(x))) for x in lens[:4]))
            if parts:
                live.write_text("\n".join(parts) + "\n", encoding="utf-8")
                print(f"  SNAP {live.name}: {parts[0][:60]}")
            print(f"  PRUNE StatisticLog {slog_gib:.2f}G — keep Train running")
            shutil.rmtree(slog, ignore_errors=True)
            continue
        if need == "0" or flag_hit:
            need0 = True
            time.sleep(20)
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
    flush_posttune_artifacts(train)
    need = get_tag((train / "Parameters_00.xml").read_text(encoding="utf-8"), "IsNeedToTrain")
    if need == "0" or flag.exists():
        return "done"
    return "incomplete" if need0 else "exited"


def mid_source_of(
    flag_meta: dict[str, str],
    thr: str,
    *,
    require_landscape: bool = True,
) -> str:
    try:
        mid_f = float((flag_meta.get("mid") or thr or "1").replace(",", "."))
    except ValueError:
        mid_f = 1.0
    landscape_ok = flag_meta.get("landscape_ok", "1") == "1"
    result = flag_meta.get("result", "")
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


def run_gate(case: dict) -> GateResult:
    root: Path = case["root"]
    test = root / "Test"
    span = int(case.get("span_ms", 25))
    csv_path = test / "SelectivityLog" / "results.csv"
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
        if case["skip_tipr_mid"]:
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
        if case["skip_tipr_mid"]:
            cmd.append("--skip-tipr-mid")
    log = test / "run_posttune_gate.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    print("GATE", " ".join(cmd))
    rc = subprocess.call(cmd, stdout=log.open("w"), stderr=subprocess.STDOUT)
    print("gate rc", rc)
    csv_mtime = csv_path.stat().st_mtime if csv_path.exists() else None
    fires, metrics_line = fires_from_csv(csv_path)
    ok = True
    fail_reason = ""
    if rc != 0:
        ok = False
        fail_reason = f"gate_rc={rc}"
    elif csv_mtime is not None and csv_mtime + 1.0 < gate_started:
        ok = False
        fail_reason = "stale_csv"
        fires, metrics_line = "", "stale_csv_ignored"
    return GateResult(
        fires=fires,
        metrics_line=metrics_line,
        rc=rc,
        csv_mtime=csv_mtime,
        gate_started=gate_started,
        ok=ok,
        fail_reason=fail_reason,
    )


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


def tipr_class(tipr: str, expect: str = "") -> str:
    if expect in ("keep", "search", "legacy"):
        if tipr_looks_posttuned(tipr):
            nums = [float(x) for x in tipr.replace(",", " ").split()[:4]]
            return "flat" if abs(nums[0] - 8.6e7) < 1e5 else "canon"
        return expect if expect != "legacy" else "other"
    if tipr_looks_posttuned(tipr):
        nums = [float(x) for x in tipr.replace(",", " ").split()[:4]]
        if abs(nums[0] - 8.6e7) < 1e5:
            return "flat"
        return "canon"
    return "other"


def tipr_matches_expect(got: str, expect: str) -> bool:
    """True when classified TipR matches case expect_tipr."""
    if expect == "legacy":
        return got in ("legacy", "other")
    return got == expect


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def run_case(name: str, *, skip_train: bool = False, run_dir: Path | None = None) -> dict:
    case = CASES[name]
    root: Path = case["root"]
    gold: Path = case["gold"]
    train = root / "Train"
    print(f"\n=== CASE {name} root={root.name} ===")
    if name == "br100_search" and skip_train:
        raise SystemExit(
            "br100_search: --skip-train forbidden — SearchSynthetic requires Train mode=4"
        )
    if run_dir is None:
        run_dir = make_run_dir(name)
    params_source = "nm_save"
    if not skip_train:
        soft_cold_reset_train(train)
        from repro_cold_lib import ensure_tag_after

        mode = {
            "br25_on": "1",
            "br25_off": "0",
            "asym25": "2",
            "br100_keep": "3",
            "br100_search": "4",
            "asym50": "1",
            "phase6_480": "1",
        }.get(name, "1")
        enable = "0" if name == "br25_off" else "1"
        for rel in ("Parameters_00.xml", "Model_00.xml"):
            p = train / rel
            if not p.exists():
                continue
            t = p.read_text(encoding="utf-8")
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
                    t, "EnablePostTrainMidThreshold", "PostTrainTipResistanceMode", mode,
                    attrs=' Type="i" PType="257" IoType="17"',
                )
                t = set_tag(t, "PostTrainTipResistanceMode", mode, 1)
                t = ensure_tag_after(
                    t, "PostTrainTipResistanceMode", "PostTrainSilentThreshold", "1",
                    attrs=' Type="d" PType="257" IoType="17"',
                )
                t = set_tag(t, "PostTrainSilentThreshold", "1", 1)
                if mode == "4":
                    t = ensure_tag_after(
                        t, "PostTrainSilentThreshold", "PostTrainTipSearchIters", "12",
                        attrs=' Type="i" PType="257" IoType="17"',
                    )
                    t = set_tag(t, "PostTrainTipSearchIters", "12", 1)
            p.write_text(t, encoding="utf-8")
            print(
                f"  PostTune tags {rel}: enable={enable} mode="
                f"{get_tag(p.read_text(encoding='utf-8'), 'PostTrainTipResistanceMode')} "
                f"auto_gap="
                f"{get_tag(p.read_text(encoding='utf-8'), 'AutoScaleIterationGap')}"
            )
        # A16: config SHA after soft_cold+inject, before Train wait.
        config_sha256 = sha256_file(train / "Parameters_00.xml")
        polls = 800 if name == "br100_search" else 401
        status = wait_need0(
            train, case["train_t"], train / "run_posttune_verify.log", max_polls=polls
        )
        params_source = flush_posttune_artifacts(train)
        if params_source == "none":
            params_source = "nm_save"
    else:
        status = "skip_train"
        config_sha256 = sha256_file(train / "Parameters_00.xml")

    after = snap_params(train / "Parameters_00.xml")
    train_flag = train / "posttune_complete.flag"
    test_flag = root / "Test" / "posttune_complete.flag"
    phase = load_phase_meta(train_flag, test_flag)

    # Prefer Test mid for display when present; do not overwrite Train provenance.
    if phase.test.get("mid"):
        after["FixedLTZThreshold"] = phase.test["mid"].split()[0]
    elif phase.train.get("mid"):
        after["FixedLTZThreshold"] = phase.train["mid"].split()[0]

    gold_test = snap_params(gold / "Test" / "Parameters_00.xml")
    gate = run_gate(case)
    phase = load_phase_meta(train_flag, test_flag)
    if phase.test.get("mid"):
        after["FixedLTZThreshold"] = phase.test["mid"].split()[0]
    tp = snap_params(root / "Test" / "Parameters_00.xml")
    if tp.get("FixedLTZThreshold") and float(
        tp["FixedLTZThreshold"].replace(",", ".") or "1"
    ) < 0.9:
        after["FixedLTZThreshold"] = tp["FixedLTZThreshold"]

    # Mid provenance from Test after gate; Train for search_reverted / snapshot.
    mid_meta = dict(phase.test) if phase.test else dict(phase.train)
    mid_src = mid_source_of(mid_meta, after.get("FixedLTZThreshold", ""))
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
        elif tipr_vs in ("applied_best", "diff", "diff_after_revert"):
            status = "done_search_diff"
        if mid_src != "cpp":
            status = f"{status}_no_cpp_mid"

    if not gate.ok:
        status = f"{status}_gate_FAIL_{gate.fail_reason}"

    fires = gate.fires if gate.ok else ""
    metrics_line = gate.metrics_line if gate.ok else gate.fail_reason

    # Persist run artifacts
    _copy_if_exists(train_flag, run_dir / "Train" / "posttune_complete.flag")
    _copy_if_exists(test_flag, run_dir / "Test" / "posttune_complete.flag")
    csv_src = root / "Test" / "SelectivityLog" / "results.csv"
    _copy_if_exists(csv_src, run_dir / "Test" / "results.csv")
    if tipr_snapshot:
        (run_dir / "Train" / "tipr_snapshot.txt").write_text(
            tipr_snapshot + "\n", encoding="utf-8"
        )
    if tipr_final:
        (run_dir / "Train" / "tipr_final.txt").write_text(tipr_final + "\n", encoding="utf-8")
    expect_tipr = case["expect_tipr"]
    got_tipr_class = tipr_class(tipr_final, expect_tipr)
    source_paths = [NMSDK_ROOT / rel for rel in PROVENANCE_SOURCE_REL]
    provenance = {
        "case": name,
        "nm": str(NM),
        "nm_mtime": NM.stat().st_mtime if Path(NM).exists() else None,
        "binary_sha256": sha256_file(NM),
        "source_sha256": sha256_paths(source_paths),
        "config_sha256": config_sha256,
        "params_source": params_source,
        "train_status": status,
        "search_reverted_train": int(search_reverted),
        "tipr_vs_snapshot": tipr_vs,
        "tipr_class": got_tipr_class,
        "expect_tipr": expect_tipr,
        "mid_source": mid_src,
        "gate_rc": gate.rc,
        "gate_ok": gate.ok,
        "quality_class": "calibration-quality",
    }
    (run_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )

    for side in (train, root / "Test"):
        for dname in ("StatisticLog", "EventsLog"):
            d = side / dname
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)

    expect_fires = case.get("expect_fires", "10000000")
    row_fail = False
    fail_notes: list[str] = []
    if not gate.ok:
        row_fail = True
        fail_notes.append(gate.fail_reason)
    if name in ("asym50", "phase6_480", "br100_search") and mid_src != "cpp":
        row_fail = True
        fail_notes.append(f"mid_source={mid_src}")
    if name == "br100_search" and tipr_vs == "same_FAIL":
        row_fail = True
        fail_notes.append("tipr_same_as_snapshot_without_reverted")
    if expect_fires and fires and fires != expect_fires:
        row_fail = True
        fail_notes.append(f"fires={fires} expect={expect_fires}")
    if tipr_final and not tipr_matches_expect(got_tipr_class, expect_tipr):
        row_fail = True
        fail_notes.append(f"tipr_class={got_tipr_class} expect={expect_tipr}")

    return {
        "case": name,
        "train_status": status,
        "after": after,
        "gold_thr": gold_test.get("FixedLTZThreshold", ""),
        "gold_tipr": gold_test.get("TipSynapseResistance", ""),
        "tipr_class": got_tipr_class,
        "fires": fires,
        "metrics": metrics_line,
        "expect_tipr": expect_tipr,
        "expect_fires": expect_fires,
        "mid_source": mid_src,
        "tipr_vs_snapshot": tipr_vs,
        "tipr_vs_keep": tipr_vs_keep_info,
        "search_reverted": int(search_reverted),
        "mode4_events": mode4_n,
        "params_source": params_source,
        "run_dir": str(run_dir),
        "gate_rc": gate.rc,
        "row_fail": row_fail,
        "fail_notes": fail_notes,
    }


def count_events_mode4(side: Path) -> int:
    elog = side / "EventsLog"
    if not elog.is_dir():
        return 0
    n = 0
    for p in elog.rglob("*"):
        if not p.is_file():
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        n += len(re.findall(r"phase\s*->\s*PostTune\s+mode=4", txt))
        n += len(re.findall(r"PostTune mode=4", txt))
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
        "| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |",
        "|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|",
    ]
    for r in rows:
        a = r["after"]
        lines.append(
            "| {case} | {st} | {need} | {tc} | `{tipr}` | {thr} | {gthr} | `{fires}` | {ms} | {tv} | {sr} | {met} |".format(
                case=r["case"],
                st=r["train_status"],
                need=a.get("IsNeedToTrain", ""),
                tc=r["tipr_class"],
                tipr=(a.get("TipSynapseResistance") or "")[:48],
                thr=a.get("FixedLTZThreshold", ""),
                gthr=r["gold_thr"],
                fires=r["fires"],
                ms=r.get("mid_source", ""),
                tv=r.get("tipr_vs_snapshot", "") or "—",
                sr=r.get("search_reverted", ""),
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
    args = ap.parse_args()
    names = list(CASES) if args.case == "all" else [args.case]
    rows = [run_case(n, skip_train=args.skip_train) for n in names]
    append_result(rows)
    sys.exit(verdict_rows(rows))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Shared helpers for AsymRm train stall / timing feasibility diagnostics."""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

K_MAX_LENGTH_STEP = 8
K_DELAY_PER_SEG_DEFAULT = 0.005
K_NUM_DENDRITES = 4
REF_DENDRITE = 3
RESISTANCE_MIN_DEFAULT = 1e6
REF_INITIAL_ANOMALY = 1.0e6


def initials_ready(initial: list[float]) -> bool:
    """Non-ref dendrites need Initial>0 before L-floor or amp-continue."""
    for i in range(3):
        if i >= len(initial) or initial[i] <= 0.0:
            return False
    return True


def ref_initial_anomalous(initial: list[float]) -> bool:
    if REF_DENDRITE >= len(initial):
        return False
    v = initial[REF_DENDRITE]
    return v <= 0.0 or v > REF_INITIAL_ANOMALY


def read_tag(text: str, tag: str) -> str | None:
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)
    return m.group(1).strip() if m else None


def parse_floats(s: str) -> list[float]:
    s = s.replace(",", ".")
    return [float(x) for x in re.split(r"\s+", s.strip()) if x]


def parse_ints(s: str) -> list[int]:
    return [int(float(x.replace(",", "."))) for x in re.split(r"\s+", s.strip()) if x]


def parse_input_pattern(text: str) -> list[float]:
    m = re.search(r"<InputPattern\b[^>]*>([^<]*)</InputPattern>", text, re.DOTALL)
    if not m:
        return []
    vals = re.split(r"[\s\n]+", m.group(1).strip())
    return [float(v.replace(",", ".")) for v in vals if v]


def load_train_params(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    pattern = parse_input_pattern(text)
    expected = []
    acc = 0.0
    for v in pattern:
        acc += v
        expected.append(acc)

    l_s = read_tag(text, "DendriteLength") or "1 1 1 1"
    tip_s = read_tag(text, "TipSynapseResistance") or ""
    init_s = read_tag(text, "InitialSomaPotential") or ""

    return {
        "path": str(path),
        "text": text,
        "InputPattern": pattern,
        "Expected": expected,
        "DendriteLength": parse_ints(l_s),
        "SyncTolerance": float(read_tag(text, "SyncTolerance") or "0.02"),
        "PeakMeasureMargin": float(read_tag(text, "PeakMeasureMargin") or "0.06"),
        "DelayAgreeMarginMin": float(read_tag(text, "DelayAgreeMarginMin") or "0.03"),
        "ResistanceAdjustGain": float(read_tag(text, "ResistanceAdjustGain") or "0.4"),
        "IterationGap": float(read_tag(text, "IterationGap") or "1.5"),
        "ResistanceMin": float(read_tag(text, "ResistanceMin") or str(RESISTANCE_MIN_DEFAULT)),
        "ResistanceMax": float(read_tag(text, "ResistanceMax") or "1e11"),
        "IsNeedToTrain": read_tag(text, "IsNeedToTrain"),
        "TrainingPhase": read_tag(text, "TrainingPhase"),
        "FixedLTZThreshold": read_tag(text, "FixedLTZThreshold"),
        "CalibratedFixedLTZThreshold": read_tag(text, "CalibratedFixedLTZThreshold"),
        "AutoCalibrateFixedLTZThreshold": read_tag(text, "AutoCalibrateFixedLTZThreshold"),
        "MembraneCapacity": read_tag(text, "MembraneCapacity"),
        "SynapseDissociationTC": read_tag(text, "SynapseDissociationTC"),
        "SynapseSecretionTC": read_tag(text, "SynapseSecretionTC"),
        "ExcMembraneResistance": read_tag(text, "ExcMembraneResistance"),
        "ExcSynapseResistance": read_tag(text, "ExcSynapseResistance"),
        "TipSynapseResistance": parse_floats(tip_s) if tip_s else [],
        "InitialSomaPotential": parse_floats(init_s) if init_s else [],
        "NeuronClassName": read_tag(text, "NeuronClassName"),
    }


def compute_needed_delays(expected: list[float], ref_peak: float | None = None) -> list[float]:
    if not expected:
        return []
    ref = ref_peak if ref_peak is not None else expected[-1]
    return [ref - e for e in expected]


def compute_l_target(
    expected: list[float],
    est_delay_per_seg: float = K_DELAY_PER_SEG_DEFAULT,
    ref_peak: float | None = None,
) -> list[int]:
    if not expected:
        return [1] * K_NUM_DENDRITES
    needed = compute_needed_delays(expected, ref_peak)
    out: list[int] = []
    for i, nd in enumerate(needed):
        if i == REF_DENDRITE:
            out.append(1)
        else:
            out.append(1 + round(abs(nd) / est_delay_per_seg))
    return out


def estimate_est_delay_from_l(
    expected: list[float], l_actual: list[int], ref_peak: float | None = None
) -> float | None:
    needed = compute_needed_delays(expected, ref_peak)
    samples: list[float] = []
    for i, (nd, la) in enumerate(zip(needed, l_actual)):
        if i == REF_DENDRITE or la <= 1:
            continue
        samples.append(abs(nd) / (la - 1))
    if not samples:
        return None
    samples.sort()
    return samples[len(samples) // 2]


def compute_iter_budget(
    l_target: list[int],
    *,
    k_max_step: int = K_MAX_LENGTH_STEP,
    n_non_ref: int = K_NUM_DENDRITES - 1,
) -> int:
    total_steps = sum(max(0, la - 1) for la in l_target)
    length_iters = math.ceil(total_steps / k_max_step) if total_steps else 0
    return 1 + length_iters * n_non_ref


def effective_iteration_gap_sec(
    iteration_gap: float = 1.5,
    max_l: int = 1,
    pattern_span: float | None = None,
) -> float:
    settle = max(0.08, K_DELAY_PER_SEG_DEFAULT * max_l)
    span = pattern_span if pattern_span is not None else 0.025
    return max(iteration_gap, span + settle + 0.05)


def iter_count_from_train_t(
    train_t: float,
    iteration_gap: float = 1.5,
    max_l: int = 1,
    pattern_span: float | None = None,
) -> int:
    gap = effective_iteration_gap_sec(iteration_gap, max_l, pattern_span)
    return max(1, int(train_t / gap))


def pattern_span_sec(params: dict[str, Any]) -> float:
    pat = params.get("InputPattern") or []
    return sum(pat) if pat else 0.025


def find_latest_statistic_dir(train_dir: Path) -> Path | None:
    subs = list_statistic_dirs(train_dir)
    return subs[-1] if subs else None


def list_statistic_dirs(train_dir: Path) -> list[Path]:
    stat_root = train_dir / "StatisticLog"
    if not stat_root.is_dir():
        return []
    return sorted([p for p in stat_root.iterdir() if p.is_dir()], key=lambda p: p.name)


def parse_trace_last_row(trace_path: Path) -> tuple[float, list[float]] | None:
    if not trace_path.is_file():
        return None
    try:
        with trace_path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return None
            chunk = min(size, 65536)
            f.seek(-chunk, 2)
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    last_line = ""
    for line in tail.splitlines():
        if line.strip():
            last_line = line.strip()
    if not last_line:
        return None
    parts = re.split(r"\s+", last_line)
    if len(parts) < 3:
        return None
    try:
        t = float(parts[1].replace(",", "."))
        vals = [float(x.replace(",", ".")) for x in parts[2:]]
        return (t, vals)
    except ValueError:
        return None


TRACE_NAMES = [
    "DendriteLengthTrace",
    "LastAbsDtTrace",
    "ResistanceStatusTrace",
    "NoImproveResistanceTrace",
    "AmpDtTrace",
    "TipSynapseResistanceTrace",
    "SomaNeuronAmplitude",
    "StimulusIterTrace",
    "EffectiveGainTrace",
]


def resolve_trace_path(stat_dir: Path, name: str, prefix: str = "NeuronTimeLearner") -> Path | None:
    for cand in (stat_dir / f"{prefix}.{name}.txt", stat_dir / f"{name}.txt"):
        if cand.is_file():
            return cand
    return None


def parse_trace_tail_rows(trace_path: Path, *, tail_rows: int = 500) -> list[tuple[float, list[float]]]:
    if not trace_path.is_file():
        return []
    try:
        with trace_path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return []
            chunk = min(size, max(65536, tail_rows * 256))
            f.seek(-chunk, 2)
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
    if tail_rows > 0:
        lines = lines[-tail_rows:]
    rows: list[tuple[float, list[float]]] = []
    for line in lines:
        parts = re.split(r"\s+", line)
        if len(parts) < 3:
            continue
        try:
            t = float(parts[1].replace(",", "."))
            vals = [float(x.replace(",", ".")) for x in parts[2:]]
            rows.append((t, vals))
        except ValueError:
            continue
    return rows


def load_trace_vectors(
    train_dir: Path,
    prefix: str = "NeuronTimeLearner",
    *,
    stat_dir: Path | None = None,
) -> dict[str, list[float]]:
    stat = stat_dir or find_latest_statistic_dir(train_dir)
    if not stat:
        return {}
    out: dict[str, list[float]] = {}
    for name in TRACE_NAMES:
        cand = resolve_trace_path(stat, name, prefix)
        if cand:
            row = parse_trace_last_row(cand)
            if row:
                out[name] = row[1]
    return out


def load_trace_vectors_at(
    train_dir: Path,
    stat_dir: Path,
    prefix: str = "NeuronTimeLearner",
) -> dict[str, list[float]]:
    return load_trace_vectors(train_dir, prefix, stat_dir=stat_dir)


def delay_len_of(l_seg: int, est_delay: float) -> float:
    return max(0.0, (l_seg - 1) * est_delay)


def delay_agree_margin(sync_tol: float, agree_min: float) -> float:
    return max(sync_tol, agree_min)


def compute_l_sync_peak(
    expected: list[float],
    est_delay: float,
    ref_peak: float | None = None,
) -> list[int]:
    return compute_l_target(expected, est_delay, ref_peak)


def all_non_ref_sync_ok(
    last_abs_dt: list[float],
    sync_tol: float,
    *,
    n_dend: int = K_NUM_DENDRITES,
    ref: int = REF_DENDRITE,
) -> bool:
    if not last_abs_dt:
        return False
    for i in range(min(n_dend - 1, len(last_abs_dt))):
        if i == ref:
            continue
        if not length_sync_ok(last_abs_dt[i], sync_tol):
            return False
    return True


def analyze_peak_shape(
    rows: list[tuple[float, list[float]]],
    *,
    n_dend: int = K_NUM_DENDRITES,
) -> list[dict[str, Any]]:
    """Per-dendrite peak shape from SomaNeuronAmplitude tail samples."""
    if not rows:
        return [{"peak_shape": "invalid", "max_amp": 0.0, "plateau_ratio": 0.0} for _ in range(n_dend)]

    out: list[dict[str, Any]] = []
    for d in range(n_dend):
        amps = [vals[d] for _, vals in rows if len(vals) > d]
        if not amps:
            out.append({"peak_shape": "invalid", "max_amp": 0.0, "plateau_ratio": 0.0})
            continue
        mx = max(amps)
        if mx <= 1e-12:
            out.append({"peak_shape": "invalid", "max_amp": mx, "plateau_ratio": 0.0})
            continue
        thresh = 0.5 * mx
        above = sum(1 for a in amps if a >= thresh)
        plateau_ratio = above / len(amps)
        mean_a = sum(amps) / len(amps)
        sharpness = mx / mean_a if mean_a > 1e-12 else 0.0
        if plateau_ratio > 0.3:
            shape = "plateau"
        elif sharpness > 3.0:
            shape = "sharp"
        else:
            shape = "moderate"
        out.append(
            {
                "peak_shape": shape,
                "max_amp": mx,
                "plateau_ratio": plateau_ratio,
                "sharpness": sharpness,
            }
        )
    return out


def parse_console_iterations(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.is_file():
        return []
    text = log_path.read_text(encoding="utf-8", errors="replace")
    iters: list[dict[str, Any]] = []
    pat = re.compile(
        r"FinishTrainingIteration: iter=(\d+).*?"
        r"amp=\[([^\]]+)\].*?"
        r"len=\[([^\]]+)\].*?"
        r"lastAbsDt=\[([^\]]+)\].*?"
        r"peakValid=\[([^\]]+)\]",
        re.DOTALL,
    )
    for m in pat.finditer(text):
        iters.append(
            {
                "iter": int(m.group(1)),
                "amp": parse_floats(m.group(2).replace(",", " ")),
                "len": parse_ints(m.group(3).replace(",", " ")),
                "last_abs_dt": parse_floats(m.group(4).replace(",", " ")),
                "peak_valid": parse_ints(m.group(5).replace(",", " ")),
            }
        )
    return iters


def diagnose_console_log(log_path: Path) -> str:
    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    if "phase -> Done" in text:
        return "ok"
    iters = parse_console_iterations(log_path)
    if not iters:
        return "unknown"
    near = [x for x in iters if 3 <= x["iter"] <= 8] or iters[:8]
    if all(max(x["amp"] or [0]) < 1e-9 for x in near):
        return "amp0"
    if all(sum(x["peak_valid"] or [0]) == 0 for x in near):
        return "peak0"
    early = [x for x in iters if x["iter"] <= 1]
    late = [x for x in iters if 4 <= x["iter"] <= 8]
    if early and late:
        eL = max(early[0]["len"] or [1])
        lL = max(max(x["len"] or [1]) for x in late)
        eDt = min(min(x["last_abs_dt"][:3] or [1.0]) for x in early)
        lDt = min(min(x["last_abs_dt"][:3] or [1.0]) for x in late)
        if lL <= eL + 1 and lDt >= eDt * 0.95:
            return "stall"
    return "nodone"


def length_sync_ok(last_abs_dt: float, sync_tol: float) -> bool:
    return last_abs_dt <= sync_tol + 1e-12


def l_vectors_match(l_actual: list[int], l_target: list[int], tol: int = 0) -> bool:
    if len(l_actual) != len(l_target):
        return False
    return all(abs(a - t) <= tol for a, t in zip(l_actual, l_target))


def read_gts_from_ini(train_dir: Path) -> int | None:
    for name in ("Project.ini", "project.ini"):
        ini = train_dir / name
        if not ini.is_file():
            continue
        m = re.search(r"<GlobalTimeStep>(\d+)</GlobalTimeStep>", ini.read_text(encoding="utf-8"))
        if m:
            return int(m.group(1))
    return None


def load_meta_exps(meta_path: Path, grid: Path) -> list[dict[str, str]]:
    lines = meta_path.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    rows: list[dict[str, str]] = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        vals = ln.split("\t")
        row = {header[i]: vals[i] if i < len(vals) else "" for i in range(len(header))}
        row["train_dir"] = str(grid / row["exp"] / "Train")
        row["params"] = str(grid / row["exp"] / "Train" / "Parameters_00.xml")
        rows.append(row)
    return rows

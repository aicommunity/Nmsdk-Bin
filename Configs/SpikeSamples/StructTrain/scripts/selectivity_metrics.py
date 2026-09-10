#!/usr/bin/env python3
"""Canonical selectivity metrics: legacy gate, strict (late), response_quality."""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path
from typing import Any


BURST_ISI_MAX = 0.005  # 5 ms
PER_STIM_MIN_FRAC = 0.75
PER_STIM_WINDOW_FLOOR = 0.003  # 3 ms


def _i(v: str | None, default: int = 0) -> int:
    if v is None or v == "":
        return default
    try:
        return int(float(v))
    except ValueError:
        return default


def _f(v: str | None, default: float = 0.0) -> float:
    if v is None or v == "":
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _parse_spike_times(row: dict[str, str]) -> list[float]:
    raw = row.get("neuron_spike_times") or ""
    if not raw.strip():
        # Fallback: single in-window or late time
        times: list[float] = []
        if row.get("neuron_fired") == "1":
            t = _f(row.get("neuron_t_rel"), -1.0)
            if t >= 0:
                times.append(t)
        if row.get("late_fired") == "1":
            t = _f(row.get("late_t_rel"), -1.0)
            if t >= 0:
                times.append(t)
        return times
    out: list[float] = []
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(float(part))
        except ValueError:
            continue
    return out


def _stim_abs_times(row: dict[str, str]) -> list[float]:
    """Stimulus times relative to first stim (0, isi0, isi0+isi1, ...)."""
    n = _i(row.get("stim_count"), 0)
    if n <= 0:
        return []
    times = [0.0]
    acc = 0.0
    for i in range(max(0, n - 1)):
        isi = _f(row.get(f"isi{i}"), 0.0)
        acc += isi
        times.append(acc)
    return times[:n]


def classify_trial_morphology(
    row: dict[str, str],
    *,
    burst_isi_max: float = BURST_ISI_MAX,
) -> dict[str, Any]:
    times = _parse_spike_times(row)
    spike_count = _i(row.get("neuron_spike_count"), len(times))
    if spike_count <= 0 and times:
        spike_count = len(times)
    if "neuron_spike_count" not in row and "neuron_spike_times" not in row:
        # Pre-morphology CSV: unknown
        return {
            "spike_count": spike_count if spike_count else (_i(row.get("neuron_fired")) + _i(row.get("late_fired"))),
            "burst": False,
            "per_stim": False,
            "ok_single": None,
            "unknown": True,
        }

    burst = False
    if spike_count >= 2 and len(times) >= 2:
        for a, b in zip(times, times[1:]):
            if b - a <= burst_isi_max + 1e-12:
                burst = True
                break

    stim_times = _stim_abs_times(row)
    stim_count = len(stim_times)
    per_stim = False
    if stim_count >= 3 and spike_count >= stim_count:
        per_stim = True
    elif stim_count >= 1 and times:
        isis = [stim_times[i + 1] - stim_times[i] for i in range(len(stim_times) - 1)]
        min_isi = min(isis) if isis else PER_STIM_WINDOW_FLOOR
        win = max(2.0 * min_isi, PER_STIM_WINDOW_FLOOR)
        covered = 0
        for st in stim_times:
            if any(st <= sp <= st + win for sp in times):
                covered += 1
        need = int(math.ceil(PER_STIM_MIN_FRAC * stim_count))
        per_stim = covered >= need

    ok_single = spike_count == 1 and not burst and not per_stim
    return {
        "spike_count": spike_count,
        "burst": burst,
        "per_stim": per_stim,
        "ok_single": ok_single,
        "unknown": False,
    }


def _legacy_mode(fires: list[int], matches: list[int], target_hit: int, fire_all: int, fa: int, acc: int) -> str:
    n = len(fires)
    silent = sum(fires) == 0
    if silent:
        return "silent"
    if fires and fires[0] == 0:
        return "miss_target"
    if fire_all:
        return "fire_all"
    if target_hit and fa <= 2 and acc >= 4:
        return "selective"
    if target_hit and not fire_all:
        return "partial_FA"
    return "miss_target"


def classify(rows: list[dict[str, str]], *, burst_isi_max: float = BURST_ISI_MAX) -> dict[str, Any]:
    n = len(rows)
    empty = {
        "ok": 0,
        "ok_legacy": 0,
        "ok_strict": 0,
        "ok_audit": 0,
        "n": 0,
        "acc": 0,
        "acc_legacy": 0,
        "acc_strict": 0,
        "target_hit": 0,
        "target_hit_legacy": 0,
        "target_hit_strict": 0,
        "fire_all": 0,
        "fire_all_legacy": 0,
        "fire_all_strict": 0,
        "mode": "silent",
        "mode_legacy": "silent",
        "mode_strict": "silent",
        "fires": "",
        "matches": "",
        "fa": 0,
        "fa_legacy": 0,
        "fa_strict": 0,
        "late_fp": 0,
        "late_fn": 0,
        "complete": 0,
        "response_quality": "unknown",
        "n_burst_trials": 0,
        "n_per_stim_trials": 0,
        "max_spike_count": 0,
        "median_spike_count": 0,
    }
    if n == 0:
        return empty

    fires_legacy = [1 if r.get("neuron_fired") == "1" else 0 for r in rows]
    matches_legacy = [1 if r.get("match") == "1" else 0 for r in rows]
    acc_legacy = sum(matches_legacy)
    fa_legacy = sum(fires_legacy[1:]) if n > 1 else 0
    target_hit_legacy = 1 if (fires_legacy[0] == 1 and matches_legacy[0] == 1) else 0
    fire_all_legacy = 1 if sum(fires_legacy) == n else 0
    mode_legacy = _legacy_mode(
        fires_legacy, matches_legacy, target_hit_legacy, fire_all_legacy, fa_legacy, acc_legacy
    )
    ok_legacy = 1 if (n == 8 and target_hit_legacy == 1 and fire_all_legacy == 0 and acc_legacy >= 4) else 0

    # Strict: late_fp on nontarget = FA; late_fn / late-only on target = miss
    fires_eff: list[int] = []
    matches_strict: list[int] = []
    late_fp = late_fn = 0
    for r in rows:
        fired = 1 if r.get("neuron_fired") == "1" else 0
        late = 1 if r.get("late_fired") == "1" else 0
        target = _i(r.get("target_class"))
        err = (r.get("error_class") or "").strip()
        if err == "late_fp" or (target == 0 and late and not fired):
            late_fp += 1
        if err == "late_fn" or (target != 0 and late and not fired):
            late_fn += 1
        effective_fire = 1 if (fired or late) else 0
        fires_eff.append(effective_fire)
        if target != 0:
            # need in-window fire for target_hit_strict
            matches_strict.append(1 if fired else 0)
        else:
            # nontarget ok only if no in-window and no late
            matches_strict.append(1 if (not fired and not late) else 0)

    acc_strict = sum(matches_strict)
    fa_strict = sum(1 for i in range(1, n) if fires_eff[i] == 1) if n > 1 else 0
    target_hit_strict = 1 if (fires_legacy[0] == 1 and matches_strict[0] == 1) else 0
    fire_all_strict = 1 if sum(fires_eff) == n and n > 0 else 0
    mode_strict = _legacy_mode(
        fires_eff, matches_strict, target_hit_strict, fire_all_strict, fa_strict, acc_strict
    )
    ok_strict = 1 if (
        n == 8 and target_hit_strict == 1 and fire_all_strict == 0 and acc_strict >= 4
    ) else 0

    morphs = [classify_trial_morphology(r, burst_isi_max=burst_isi_max) for r in rows]
    unknown = any(m["unknown"] for m in morphs)
    n_burst = sum(1 for m in morphs if m["burst"])
    n_per = sum(1 for m in morphs if m["per_stim"])
    counts = [int(m["spike_count"]) for m in morphs]
    max_spikes = max(counts) if counts else 0
    med_spikes = int(statistics.median(counts)) if counts else 0

    if unknown:
        response_quality = "unknown"
    elif n_burst == 0 and n_per == 0 and all(m.get("ok_single") for m in morphs if m["spike_count"] > 0 or True):
        # ok_single for all trials that fired; silent trials are fine
        bad = any(m["spike_count"] > 1 or m["burst"] or m["per_stim"] for m in morphs)
        # also: if any trial has spike_count!=1 when fired in-window or late
        for m, r in zip(morphs, rows):
            eff = (r.get("neuron_fired") == "1") or (r.get("late_fired") == "1")
            if eff and m["spike_count"] != 1:
                bad = True
            if m["burst"] or m["per_stim"]:
                bad = True
        response_quality = "ok_single" if not bad else ("mixed" if (n_burst and n_per) else ("burst" if n_burst else "per_stim"))
        if not bad:
            response_quality = "ok_single"
        elif n_burst and n_per:
            response_quality = "mixed"
        elif n_burst:
            response_quality = "burst"
        elif n_per:
            response_quality = "per_stim"
        else:
            response_quality = "mixed"
    else:
        if n_burst and n_per:
            response_quality = "mixed"
        elif n_burst:
            response_quality = "burst"
        elif n_per:
            response_quality = "per_stim"
        else:
            # multi without burst/per_stim flags
            if any(m["spike_count"] > 1 for m in morphs):
                response_quality = "mixed"
            else:
                response_quality = "ok_single"

    complete = 1 if n == 8 else 0
    ok_audit = 1 if (
        ok_strict == 1 and response_quality == "ok_single" and complete == 1
    ) else 0

    return {
        "ok": ok_legacy,  # backward compat
        "ok_legacy": ok_legacy,
        "ok_strict": ok_strict,
        "ok_audit": ok_audit,
        "n": n,
        "acc": acc_legacy,
        "acc_legacy": acc_legacy,
        "acc_strict": acc_strict,
        "target_hit": target_hit_legacy,
        "target_hit_legacy": target_hit_legacy,
        "target_hit_strict": target_hit_strict,
        "fire_all": fire_all_legacy,
        "fire_all_legacy": fire_all_legacy,
        "fire_all_strict": fire_all_strict,
        "mode": mode_legacy,
        "mode_legacy": mode_legacy,
        "mode_strict": mode_strict,
        "fires": "".join(str(x) for x in fires_legacy),
        "matches": "".join(str(x) for x in matches_legacy),
        "fa": fa_legacy,
        "fa_legacy": fa_legacy,
        "fa_strict": fa_strict,
        "late_fp": late_fp,
        "late_fn": late_fn,
        "complete": complete,
        "response_quality": response_quality,
        "n_burst_trials": n_burst,
        "n_per_stim_trials": n_per,
        "max_spike_count": max_spikes,
        "median_spike_count": med_spikes,
        "effective_fires": "".join(str(x) for x in fires_eff),
    }


def format_line(q: dict[str, Any], *, verbose: bool = False) -> str:
    base = (
        f"ok={q['ok_legacy']} n={q['n']} acc={q['acc_legacy']} "
        f"target_hit={q['target_hit_legacy']} fire_all={q['fire_all_legacy']} "
        f"mode={q['mode_legacy']} fires={q['fires']} matches={q['matches']} fa={q['fa_legacy']}"
    )
    if not verbose:
        return base
    return (
        f"{base} ok_strict={q['ok_strict']} ok_audit={q['ok_audit']} "
        f"acc_strict={q['acc_strict']} fire_all_strict={q['fire_all_strict']} "
        f"late_fp={q['late_fp']} late_fn={q['late_fn']} "
        f"response_quality={q['response_quality']} "
        f"n_burst={q['n_burst_trials']} n_per_stim={q['n_per_stim_trials']} "
        f"max_spikes={q['max_spike_count']}"
    )


def evaluate_path(csv_path: Path, *, verbose: bool = False) -> tuple[dict[str, Any], int]:
    if not csv_path.exists():
        q = classify([])
        q["mode"] = q["mode_legacy"] = "missing"
        return q, 2
    try:
        rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    except OSError:
        q = classify([])
        q["mode"] = q["mode_legacy"] = "missing"
        return q, 2
    return classify(rows), 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=Path)
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()
    q, code = evaluate_path(args.csv_path, verbose=args.verbose)
    if code == 2:
        line = format_line(q, verbose=args.verbose)
        print(line, file=sys.stderr)
        print(line)
        raise SystemExit(2)
    print(format_line(q, verbose=args.verbose))


if __name__ == "__main__":
    main()

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
    except (ValueError, TypeError, OverflowError):
        return default


def _f(v: str | None, default: float = 0.0) -> float:
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (ValueError, TypeError, OverflowError):
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
            # Preserve corruption as invalid evidence; never silently drop it.
            out.append(float("nan"))
    return out


def _stim_abs_times(row: dict[str, str]) -> list[float]:
    """Stimulus times relative to first stim (0, isi0, isi0+isi1, ...)."""
    n = _i(row.get("stim_count"), 0)
    if n <= 0:
        return []
    if str(row.get("stim_times") or "").strip():
        return [float(part) if part.strip() else float("nan")
                for part in row["stim_times"].split(";")]
    if str(row.get("isis") or "").strip():
        isis = [float(part) for part in row["isis"].split(";")]
        times = [0.0]
        for isi in isis:
            times.append(times[-1] + isi)
        return times
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
    # N=1: never classify as per_stim (R07).
    if stim_count >= 2:
        if stim_count >= 3 and spike_count >= stim_count:
            per_stim = True
        elif stim_count >= 1 and times:
            isis = [stim_times[i + 1] - stim_times[i] for i in range(len(stim_times) - 1)]
            min_isi = min(isis) if isis else PER_STIM_WINDOW_FLOOR
            win = max(2.0 * min_isi, PER_STIM_WINDOW_FLOOR)
            # Injective: each spike matches at most one stim.
            used = [False] * len(times)
            matched = 0
            for st in stim_times:
                for i, sp in enumerate(times):
                    if used[i]:
                        continue
                    if st - 1e-12 <= sp <= st + win + 1e-12:
                        used[i] = True
                        matched += 1
                        break
            need = int(math.ceil(PER_STIM_MIN_FRAC * stim_count))
            per_stim = matched >= need

    ok_single = spike_count == 1 and not burst and not per_stim
    return {
        "spike_count": spike_count,
        "burst": burst,
        "per_stim": per_stim,
        "ok_single": ok_single,
        "unknown": False,
        "censored": _i(row.get("censored")) == 1,
    }


def _legacy_mode(fires: list[int], matches: list[int], target_hit: int, fire_all: int, fa: int, acc: int) -> str:
    n = len(fires)
    silent = sum(fires) == 0
    if silent:
        return "silent"
    if not target_hit:
        return "miss_target"
    if fire_all:
        return "fire_all"
    if target_hit and fa <= 2 and acc >= 4:
        return "selective"
    if target_hit and not fire_all:
        return "partial_FA"
    return "miss_target"


def _validate_rows(rows: list[dict[str, str]], expected_trial_ids: set[str]) -> list[str]:
    """Validate evidence before scoring. Historical fields cannot prove completeness."""
    errors: list[str] = []
    seen: set[str] = set()
    sample_ids: set[str] = set()
    versions: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"row[{index}]"
        trial = str(row.get("trial_id", row.get("trial", ""))).strip()
        if not trial or trial in seen:
            errors.append(f"{prefix}:missing_or_duplicate_trial")
        seen.add(trial)
        version = str(row.get("schema_version", ""))
        versions.add(version)
        if version not in {"3", "4"}:
            errors.append(f"{prefix}:unsupported_schema")
        for field in ("target_class", "neuron_fired", "late_fired", "complete", "censored"):
            if str(row.get(field, "")) not in {"0", "1"}:
                errors.append(f"{prefix}:invalid_{field}")
        if str(row.get("complete", "")) != "1":
            errors.append(f"{prefix}:incomplete")
        if str(row.get("censored", "")) != "0":
            errors.append(f"{prefix}:censored_or_unknown")
        if row.get("error_class") in {"incomplete", "censored", "nonfinite", "overflow"}:
            errors.append(f"{prefix}:observation_error")
        if "sample_id" in row:
            sample = str(row["sample_id"]).strip()
            if not sample or sample in sample_ids:
                errors.append(f"{prefix}:missing_or_duplicate_sample")
            sample_ids.add(sample)
        try:
            count = int(row["neuron_spike_count"])
            raw_times = str(row["neuron_spike_times"] or "").strip()
            times = [float(part) for part in raw_times.split(";")] if raw_times else []
            if count < 0 or count != len(times) or any(not math.isfinite(t) or t < 0 for t in times):
                raise ValueError("count/timestamps")
            if any(b <= a for a, b in zip(times, times[1:])):
                raise ValueError("unordered timestamps")
            if (row.get("neuron_fired") == "1" or row.get("late_fired") == "1") and not times:
                raise ValueError("fire without spike")
            n_stim = int(row["stim_count"])
            stims = _stim_abs_times(row)
            if n_stim < 1 or len(stims) != n_stim or not stims or abs(stims[0]) > 1e-9:
                raise ValueError("stimulus count")
            if any(not math.isfinite(t) for t in stims) or any(b <= a for a, b in zip(stims, stims[1:])):
                raise ValueError("stimulus timestamps")
            for field in ("neuron_t_rel", "late_t_rel", "actual_observe_end", "ltz_potential_max", "soma_amp_sum"):
                if field in row and row[field] != "" and not math.isfinite(float(row[field])):
                    raise ValueError(field)
            for field in ("neuron_t_rel", "late_t_rel"):
                flag = "neuron_fired" if field == "neuron_t_rel" else "late_fired"
                if row.get(flag) == "1":
                    value = float(row[field])
                    if not math.isfinite(value) or not any(abs(value - t) <= 1e-6 for t in times):
                        raise ValueError("inconsistent fire time")
            for field, value in row.items():
                if not isinstance(field, str):
                    raise ValueError("unexpected CSV columns")
                if field.startswith("soma_amp_") and value != "" and not math.isfinite(float(value)):
                    raise ValueError(field)
            if version == "4":
                for field in ("run_id", "trial_id", "sample_id", "pattern_hash", "model_revision"):
                    if not str(row.get(field, "")).strip():
                        raise ValueError(f"missing {field}")
                if row.get("measurement_valid") != "1":
                    raise ValueError("invalid measurement")
                amplitudes = [float(v) for v in row["soma_amplitudes"].split(";")]
                if not amplitudes or any(not math.isfinite(v) for v in amplitudes):
                    raise ValueError("amplitudes")
                onset = float(row["onset_abs"])
                required_end = float(row["required_observe_end"])
                actual_end = float(row["actual_observe_end"])
                if not all(math.isfinite(v) for v in (onset, required_end, actual_end)):
                    raise ValueError("observation bounds")
                if required_end < onset + stims[-1] or actual_end + 1e-9 < required_end:
                    raise ValueError("truncated observation")
        except (KeyError, TypeError, ValueError, OverflowError):
            errors.append(f"{prefix}:invalid_measurement_data")
    if seen != expected_trial_ids:
        errors.append("unexpected_trial_set")
    if len(versions) != 1:
        errors.append("mixed_schemas")
    if not any(row.get("target_class") == "1" for row in rows):
        errors.append("missing_target")
    if not any(row.get("target_class") == "0" for row in rows):
        errors.append("missing_foils")
    return errors


def classify(rows: list[dict[str, str]], *, burst_isi_max: float = BURST_ISI_MAX,
             expected_trial_ids: set[str] | None = None) -> dict[str, Any]:
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
        "metrics_version": 4,
        "schema_ok": 0,
        "validation_errors": ["missing_observations"],
        "ok_audit_legacy": 0,
        "ok_audit_strict_shape": 0,
        "ok_audit_v2": 0,
        "censored_any": 0,
        "last_pulse_ok": "0",
        "fa_strict_v2": 0,
    }
    if n == 0:
        return empty

    expected_trial_ids = {str(v) for v in (expected_trial_ids if expected_trial_ids is not None else range(8))}
    validation_errors = _validate_rows(rows, expected_trial_ids)
    targets = [i for i, row in enumerate(rows) if _i(row.get("target_class")) != 0]
    foils = [i for i in range(n) if i not in targets]

    fires_legacy = [1 if r.get("neuron_fired") == "1" else 0 for r in rows]
    matches_legacy = [1 if r.get("match") == "1" else 0 for r in rows]
    acc_legacy = sum(matches_legacy)
    fa_legacy = sum(fires_legacy[i] for i in foils)
    target_hit_legacy = int(bool(targets) and all(fires_legacy[i] and matches_legacy[i] for i in targets))
    fire_all_legacy = 1 if sum(fires_legacy) == n else 0
    mode_legacy = _legacy_mode(
        fires_legacy, matches_legacy, target_hit_legacy, fire_all_legacy, fa_legacy, acc_legacy
    )
    ok_legacy = 1 if (n == 8 and target_hit_legacy == 1 and fire_all_legacy == 0 and acc_legacy >= 4) else 0

    # Strict v2: any foil spike in the observation window is FP (not only flags).
    fires_eff: list[int] = []
    matches_strict: list[int] = []
    late_fp = late_fn = 0
    schema_ok = 1
    censored_any = 0
    for r in rows:
        fired = 1 if r.get("neuron_fired") == "1" else 0
        late = 1 if r.get("late_fired") == "1" else 0
        target = _i(r.get("target_class"))
        err = (r.get("error_class") or "").strip()
        times = _parse_spike_times(r)
        spike_count = _i(r.get("neuron_spike_count"), len(times))
        if _i(r.get("censored")) == 1 or err in ("censored", "incomplete"):
            censored_any = 1
        # Contradictory / nonfinite schema (R07).
        t_rel_s = r.get("neuron_t_rel") or "-1"
        try:
            t_rel = float(t_rel_s)
        except ValueError:
            t_rel = float("nan")
            schema_ok = 0
        if fired == 1 and spike_count == 0 and (t_rel < 0 or not math.isfinite(t_rel)):
            schema_ok = 0
        if any(not math.isfinite(t) for t in times):
            schema_ok = 0
        if times and times != sorted(times):
            schema_ok = 0
        if "neuron_spike_count" in r and "neuron_spike_times" in r:
            if spike_count != len(times) and (spike_count > 0 or times):
                # Allow empty times with count 0; otherwise require consistency.
                if not (spike_count == 0 and not times):
                    if abs(spike_count - len(times)) > 0 and times:
                        schema_ok = 0
        has_spike = spike_count > 0 or bool(times)
        if err == "late_fp" or (target == 0 and late and not fired):
            late_fp += 1
        if err == "late_fn" or (target != 0 and late and not fired):
            late_fn += 1
        # v2 effective fire: flags OR any recorded spike
        effective_fire = 1 if (fired or late or has_spike) else 0
        # Censored foil rows must not confirm full silence.
        if censored_any and target == 0 and effective_fire == 0:
            # Treat as unknown for FA purposes — force schema/quality fail later.
            pass
        fires_eff.append(effective_fire)
        if target != 0:
            matches_strict.append(1 if fired else 0)
        else:
            matches_strict.append(1 if not effective_fire else 0)

    acc_strict = sum(matches_strict)
    fa_strict = sum(fires_eff[i] for i in foils)
    target_hit_strict = int(bool(targets) and all(fires_legacy[i] and matches_strict[i] for i in targets))
    fire_all_strict = 1 if sum(fires_eff) == n and n > 0 else 0
    mode_strict = _legacy_mode(
        fires_eff, matches_strict, target_hit_strict, fire_all_strict, fa_strict, acc_strict
    )
    ok_strict = 1 if (
        n == len(expected_trial_ids) and target_hit_strict == 1 and fire_all_strict == 0 and acc_strict >= min(4, n)
        and schema_ok == 1
    ) else 0

    morphs = []
    for row in rows:
        try:
            morphs.append(classify_trial_morphology(row, burst_isi_max=burst_isi_max))
        except (TypeError, ValueError, OverflowError):
            morphs.append({"unknown": True, "burst": False, "per_stim": False, "spike_count": 0})
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

    complete = int(n == len(expected_trial_ids) and not validation_errors)
    schema_ok = int(schema_ok == 1 and not validation_errors)
    ok_strict = int(ok_strict == 1 and schema_ok == 1)
    # Renamed: NOT historical A05 scorer (uses strict shape). See metrics_version.
    ok_audit_strict_shape = 1 if (
        ok_strict == 1 and response_quality == "ok_single" and complete == 1
    ) else 0
    # v2 audit gate: same shape but uses spike-aware FA; reject bad schema / censored.
    ok_audit_v2 = 1 if (
        schema_ok == 1
        and censored_any == 0
        and ok_strict == 1
        and response_quality == "ok_single"
        and complete == 1
        and fa_strict == 0
    ) else 0
    # Default ok_audit follows v2 (hidden foil spikes count as FP).
    ok_audit = ok_audit_v2

    # Evaluate every labelled target, independently of CSV presentation order.
    last_pulse = "0"
    if targets:
        try:
            target_after_last = []
            for target in targets:
                stims = _stim_abs_times(rows[target])
                target_after_last.append(bool(stims) and float(rows[target].get("neuron_t_rel", -1)) + 1e-9 >= stims[-1])
            last_pulse = "1" if all(target_after_last) else "0"
        except (TypeError, ValueError, OverflowError):
            last_pulse = "0"
    if last_pulse != "1" and ok_audit == 1:
        ok_audit = 0
    ok_audit_v2 = ok_audit

    return {
        "ok": ok_legacy,  # backward compat
        "ok_legacy": ok_legacy,
        "ok_strict": ok_strict,
        "ok_audit": ok_audit,
        "ok_audit_legacy": ok_audit_strict_shape,  # compat alias — NOT historical A05
        "ok_audit_strict_shape": ok_audit_strict_shape,
        "ok_audit_v2": ok_audit_v2,
        "metrics_version": 4,
        "validation_errors": validation_errors,
        "schema_ok": schema_ok,
        "censored_any": censored_any,
        "last_pulse_ok": last_pulse,
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
        "fa_strict_v2": fa_strict,
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

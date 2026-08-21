#!/usr/bin/env python3
"""Extract EPSP timing metrics from UStatisticDoubleMatrix CSV logs.

Supports:
  - single pulse: t_peak, FWHM, rise10_90, t_tail10
  - dual pulse: separability between two peaks

Usage:
  extract_metrics.py <cell_dir> [--col COL] [--dt DT] [--dual-isi ISI]
  extract_metrics.py --batch <parent_cells_dir> --out metrics.csv [--meta META.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path


def find_stat_csv(cell: Path) -> Path | None:
    slog = cell / "StatisticLog"
    if not slog.is_dir():
        return None
    cands = sorted(slog.rglob("*.csv")) + sorted(slog.rglob("*.CSV"))
    # also plain text dumps
    cands += sorted(slog.rglob("*.txt"))
    return cands[0] if cands else None


def load_series(path: Path, col: int) -> tuple[list[float], list[float]]:
    """Return (times, values). Handles comma/semicolon, optional time column."""
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return [], []
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    times: list[float] = []
    vals: list[float] = []
    for i, ln in enumerate(lines):
        # skip header-ish
        if re.search(r"[A-Za-z_]", ln) and i == 0:
            continue
        parts = re.split(r"[,;\s]+", ln.strip())
        parts = [p for p in parts if p != ""]
        if not parts:
            continue
        try:
            nums = [float(p.replace(",", ".")) for p in parts]
        except ValueError:
            continue
        if len(nums) == 1:
            times.append(float(i))
            vals.append(nums[0])
        elif col + 1 < len(nums) and len(nums) >= 2:
            # assume first col is time if WriteModelTimeStampFlag
            times.append(nums[0])
            vals.append(nums[col + 1] if col + 1 < len(nums) else nums[-1])
        else:
            times.append(nums[0] if len(nums) > 1 else float(i))
            vals.append(nums[min(col, len(nums) - 1)])
    # If times look like indices (0,1,2,...) and dt known later — caller may rescale
    return times, vals


def _peak_idx(vals: list[float], start: int = 0, end: int | None = None) -> int:
    end = end if end is not None else len(vals)
    if start >= end:
        return start
    return max(range(start, end), key=lambda i: vals[i])


def pulse_metrics(
    times: list[float],
    vals: list[float],
    *,
    dt_hint: float | None = None,
    window: tuple[float, float] | None = None,
) -> dict:
    if not vals:
        return {"ok": 0, "error": "empty"}
    t = list(times)
    v = list(vals)
    # rescale index-times
    if len(t) >= 2 and abs(t[1] - t[0] - 1.0) < 1e-9 and dt_hint:
        t = [i * dt_hint for i in range(len(v))]
    if window:
        t0, t1 = window
        idx = [i for i, ti in enumerate(t) if t0 <= ti <= t1]
        if not idx:
            return {"ok": 0, "error": "window_empty"}
        t = [t[i] for i in idx]
        v = [v[i] for i in idx]
    peak_i = _peak_idx(v)
    peak = v[peak_i]
    t_peak = t[peak_i]
    if abs(peak) < 1e-15:
        return {"ok": 0, "error": "zero_peak", "peak": 0.0}

    half = peak * 0.5
    # FWHM: left and right crossings
    left = peak_i
    while left > 0 and v[left] >= half:
        left -= 1
    right = peak_i
    while right < len(v) - 1 and v[right] >= half:
        right += 1
    fwhm = t[right] - t[left]

    # rise 10-90
    lo, hi = peak * 0.1, peak * 0.9
    i10 = next((i for i in range(peak_i + 1) if v[i] >= lo), 0)
    i90 = next((i for i in range(i10, peak_i + 1) if v[i] >= hi), peak_i)
    rise = t[i90] - t[i10]

    # tail to 10% after peak
    i_tail = next((i for i in range(peak_i, len(v)) if v[i] <= lo), len(v) - 1)
    t_tail10 = t[i_tail] - t_peak

    return {
        "ok": 1,
        "peak": peak,
        "t_peak": t_peak,
        "fwhm": fwhm,
        "rise10_90": rise,
        "t_tail10": t_tail10,
        "t0": t[0],
        "t_end": t[-1],
        "n": len(v),
    }


def dual_separability(
    times: list[float],
    vals: list[float],
    isi: float,
    *,
    dt_hint: float | None = None,
    t_first: float | None = None,
) -> dict:
    m1 = pulse_metrics(times, vals, dt_hint=dt_hint)
    if not m1.get("ok"):
        return {**m1, "sep": 0.0, "gate_pass": 0}
    # find two peaks around expected onsets
    t = list(times)
    v = list(vals)
    if len(t) >= 2 and abs(t[1] - t[0] - 1.0) < 1e-9 and dt_hint:
        t = [i * dt_hint for i in range(len(v))]
    # locate first peak near max in first third after activity starts
    peak1_i = _peak_idx(v)
    # search second peak after isi*0.6 from peak1
    t_p1 = t[peak1_i]
    start2 = next((i for i, ti in enumerate(t) if ti >= t_p1 + isi * 0.5), peak1_i)
    # local minimum (trough) between
    if start2 <= peak1_i:
        return {"ok": 0, "error": "no_second_window", "sep": 0.0, "gate_pass": 0}
    trough_i = min(range(peak1_i, start2 + 1), key=lambda i: v[i])
    end2 = next((i for i, ti in enumerate(t) if ti >= t_p1 + isi * 1.8), len(v) - 1)
    peak2_i = _peak_idx(v, start2, end2 + 1)
    p1, p2 = v[peak1_i], v[peak2_i]
    trough = v[trough_i]
    mn = min(p1, p2)
    sep = (mn - trough) / mn if abs(mn) > 1e-15 else 0.0
    gate = 1 if sep >= 0.30 and p2 > abs(p1) * 0.2 else 0
    return {
        "ok": 1,
        "peak1": p1,
        "peak2": p2,
        "t_peak1": t[peak1_i],
        "t_peak2": t[peak2_i],
        "trough": trough,
        "sep": sep,
        "gate_pass": gate,
        "fwhm_est": m1.get("fwhm"),
    }


def metrics_for_cell(
    cell: Path,
    *,
    col: int = 0,
    dt: float = 0.0005,
    dual_isi: float | None = None,
) -> dict:
    path = find_stat_csv(cell)
    row = {"cell": cell.name, "path": str(cell), "stat_csv": str(path) if path else ""}
    if not path:
        row.update({"ok": 0, "error": "no_stat_csv"})
        return row
    times, vals = load_series(path, col)
    if dual_isi is not None:
        row.update(dual_separability(times, vals, dual_isi, dt_hint=dt))
    else:
        row.update(pulse_metrics(times, vals, dt_hint=dt))
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cell", nargs="?", type=Path)
    ap.add_argument("--batch", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--col", type=int, default=0)
    ap.add_argument("--dt", type=float, default=0.0005)
    ap.add_argument("--dual-isi", type=float, default=None)
    ap.add_argument("--meta", type=Path, help="JSON map cell_name -> {dissoc, capacity, ...}")
    args = ap.parse_args()

    meta = {}
    if args.meta and args.meta.exists():
        meta = json.loads(args.meta.read_text(encoding="utf-8"))

    rows = []
    if args.batch:
        for cell in sorted(p for p in args.batch.iterdir() if p.is_dir()):
            if not (cell / "project.ini").exists() and not (cell / "Project.ini").exists():
                continue
            r = metrics_for_cell(cell, col=args.col, dt=args.dt, dual_isi=args.dual_isi)
            if cell.name in meta:
                r.update(meta[cell.name])
            rows.append(r)
    elif args.cell:
        r = metrics_for_cell(args.cell, col=args.col, dt=args.dt, dual_isi=args.dual_isi)
        if args.cell.name in meta:
            r.update(meta[args.cell.name])
        rows.append(r)
    else:
        ap.error("cell or --batch required")

    if args.out:
        keys: list[str] = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with args.out.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
        print(f"Wrote {args.out} ({len(rows)} rows)")
    else:
        print(json.dumps(rows, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Offline sweep SyncTolerance / PeakMeasureMargin / EstDelay on current L and traces."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from asymrm_train_common import (
    K_DELAY_PER_SEG_DEFAULT,
    K_NUM_DENDRITES,
    REF_DENDRITE,
    all_non_ref_sync_ok,
    compute_needed_delays,
    delay_len_of,
    estimate_est_delay_from_l,
    length_sync_ok,
    load_meta_exps,
    load_train_params,
    load_trace_vectors,
)

TOL_MULTIPLIERS = (1.0, 1.25, 1.5, 2.0)
MARGIN_MULTIPLIERS = (0.75, 1.0, 1.5)
EST_DELAYS = (0.005, 0.0052)


def would_sync_at_l(
    needed: float,
    L: int,
    est_delay: float,
    sync_tol: float,
) -> bool:
    return abs(needed - delay_len_of(L, est_delay)) <= sync_tol + 1e-12


def offline_all_sync_ok(
    l_actual: list[int],
    needed: list[float],
    est_delay: float,
    sync_tol: float,
    last_abs_dt: list[float],
    *,
    use_trace: bool = True,
) -> bool:
    """Check sync: use trace dt if available, else cable model residual."""
    for i in range(K_NUM_DENDRITES):
        if i == REF_DENDRITE:
            continue
        L = l_actual[i] if i < len(l_actual) else 1
        nd = needed[i] if i < len(needed) else 0.0
        if use_trace and i < len(last_abs_dt) and last_abs_dt[i] > 0:
            if not length_sync_ok(last_abs_dt[i], sync_tol):
                return False
        elif not would_sync_at_l(nd, L, est_delay, sync_tol):
            return False
    return True


def sweep_one(train_dir: Path) -> list[dict[str, Any]]:
    p = load_train_params(train_dir / "Parameters_00.xml")
    l_actual = p["DendriteLength"]
    expected = p["Expected"]
    base_tol = p["SyncTolerance"]
    base_margin = p["PeakMeasureMargin"]
    est_post = estimate_est_delay_from_l(expected, l_actual) or K_DELAY_PER_SEG_DEFAULT
    needed = compute_needed_delays(expected)
    traces = load_trace_vectors(train_dir)
    last_dt = traces.get("LastAbsDtTrace", [])

    rows: list[dict[str, Any]] = []

    for tol_mult in TOL_MULTIPLIERS:
        tol = base_tol * tol_mult
        ok_trace = offline_all_sync_ok(
            l_actual, needed, est_post, tol, last_dt, use_trace=True
        )
        ok_model = offline_all_sync_ok(
            l_actual, needed, est_post, tol, last_dt, use_trace=False
        )
        rows.append(
            {
                "exp": train_dir.parent.name,
                "case": f"tol_x{tol_mult:g}",
                "SyncTolerance": tol,
                "PeakMeasureMargin": base_margin,
                "EstDelayPerSeg": est_post,
                "all_sync_ok_trace": ok_trace,
                "all_sync_ok_model": ok_model,
            }
        )

    for marg_mult in MARGIN_MULTIPLIERS:
        margin = base_margin * marg_mult
        rows.append(
            {
                "exp": train_dir.parent.name,
                "case": f"margin_x{marg_mult:g}",
                "SyncTolerance": base_tol,
                "PeakMeasureMargin": margin,
                "EstDelayPerSeg": est_post,
                "all_sync_ok_trace": all_non_ref_sync_ok(last_dt, base_tol),
                "all_sync_ok_model": offline_all_sync_ok(
                    l_actual, needed, est_post, base_tol, last_dt, use_trace=False
                ),
            }
        )

    for est in EST_DELAYS:
        rows.append(
            {
                "exp": train_dir.parent.name,
                "case": f"est_{est:g}",
                "SyncTolerance": base_tol,
                "PeakMeasureMargin": base_margin,
                "EstDelayPerSeg": est,
                "all_sync_ok_trace": all_non_ref_sync_ok(last_dt, base_tol),
                "all_sync_ok_model": offline_all_sync_ok(
                    l_actual, needed, est, base_tol, last_dt, use_trace=False
                ),
            }
        )

    # L sweep: try L_ref candidates for dend2
    for l2 in (3, 4, 5):
        l_try = list(l_actual)
        if len(l_try) > 2:
            l_try[2] = l2
        for est in (est_post, K_DELAY_PER_SEG_DEFAULT):
            ok_model = offline_all_sync_ok(
                l_try, needed, est, base_tol, last_dt, use_trace=False
            )
            rows.append(
                {
                    "exp": train_dir.parent.name,
                    "case": f"L_dend2={l2}_est_{est:g}",
                    "SyncTolerance": base_tol,
                    "PeakMeasureMargin": base_margin,
                    "EstDelayPerSeg": est,
                    "L_hypothesis": l_try,
                    "all_sync_ok_trace": None,
                    "all_sync_ok_model": ok_model,
                }
            )

    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("train_dirs", nargs="*", type=Path)
    ap.add_argument("--meta", type=Path)
    ap.add_argument("--grid", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    dirs: list[Path] = list(args.train_dirs)
    if args.meta and args.grid:
        for row in load_meta_exps(args.meta, args.grid):
            dirs.append(Path(row["train_dir"]))

    if not dirs:
        ap.error("provide train dirs")

    all_rows: list[dict[str, Any]] = []
    for d in dirs:
        if (d / "Parameters_00.xml").exists():
            all_rows.extend(sweep_one(d))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.suffix == ".json":
            args.output.write_text(json.dumps(all_rows, indent=2), encoding="utf-8")
        else:
            fields = [
                "exp", "case", "SyncTolerance", "PeakMeasureMargin", "EstDelayPerSeg",
                "all_sync_ok_trace", "all_sync_ok_model", "L_hypothesis",
            ]
            with args.output.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
                w.writeheader()
                for row in all_rows:
                    r = dict(row)
                    if isinstance(r.get("L_hypothesis"), list):
                        r["L_hypothesis"] = " ".join(str(x) for x in r["L_hypothesis"])
                    w.writerow(r)

    if args.json:
        print(json.dumps(all_rows, indent=2))
    else:
        for row in all_rows:
            print(
                f"{row['exp']} {row['case']}: trace={row.get('all_sync_ok_trace')} "
                f"model={row.get('all_sync_ok_model')}"
            )


if __name__ == "__main__":
    main()

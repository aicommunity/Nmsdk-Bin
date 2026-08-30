#!/usr/bin/env python3
"""Per-dendrite stall diagnosis from Parameters, StatisticLog traces, run_console.log."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from asymrm_train_common import (
    K_NUM_DENDRITES,
    REF_DENDRITE,
    compute_iter_budget,
    compute_l_target,
    diagnose_console_log,
    estimate_est_delay_from_l,
    length_sync_ok,
    load_meta_exps,
    load_train_params,
    load_trace_vectors,
    parse_console_iterations,
    l_vectors_match,
)
from check_timing_feasibility import analyze_one


def classify_dendrite(
    i: int,
    *,
    L: int,
    l_target: int,
    last_abs_dt: float,
    sync_tol: float,
    res_status: float,
    no_improve: float,
    amp_dt: float,
    tip_r: float,
    r_min: float,
    peak_valid: int | None,
    iter_count: int | None,
    iter_budget: int,
    length_plateau: bool,
) -> str:
    if peak_valid is not None and peak_valid == 0 and L <= 1 and i != REF_DENDRITE:
        return "PEAK_INVALID"
    if not length_sync_ok(last_abs_dt, sync_tol) and L < l_target:
        if length_plateau and iter_count is not None and iter_count < iter_budget:
            return "TIME_BUDGET"
        return "LENGTH_STALL"
    if L >= l_target and not length_sync_ok(last_abs_dt, sync_tol):
        return "LENGTH_STALL"
    if L >= l_target and length_sync_ok(last_abs_dt, sync_tol):
        if tip_r <= r_min * (1 + 1e-6) and no_improve >= 3:
            return "AMP_AT_RMIN"
        if no_improve >= 3 and abs(amp_dt) < 0.005:
            return "AMP_OSCILLATION"
        if res_status != 0:
            return "AMP_PENDING"
        if abs(amp_dt) > 1e-5:
            return "AMP_PENDING"
        return "DONE"
    if length_plateau and iter_count is not None and iter_count < iter_budget and i > 0:
        return "TIME_BUDGET"
    return "LENGTH_STALL"


def overall_blocker(dend_blockers: list[str], need_train: str | None, log_status: str) -> str:
    if need_train == "0" and all(b == "DONE" for b in dend_blockers):
        return "DONE"
    priority = [
        "PEAK_INVALID",
        "LENGTH_STALL",
        "TIME_BUDGET",
        "AMP_AT_RMIN",
        "AMP_OSCILLATION",
        "AMP_PENDING",
        "DONE",
        "DONE_LENGTH_ONLY",
    ]
    for p in priority:
        if p in dend_blockers:
            return p
    if log_status in ("peak0", "amp0"):
        return "PEAK_INVALID"
    if log_status == "stall":
        return "TIME_BUDGET"
    return dend_blockers[0] if dend_blockers else "UNKNOWN"


def detect_length_plateau(iters: list[dict[str, Any]], dend: int) -> bool:
    if len(iters) < 2:
        return False
    lens = [x["len"][dend] for x in iters[-8:] if x.get("len") and len(x["len"]) > dend]
    if len(lens) < 2:
        return False
    return lens[-1] == lens[0] and lens[0] <= 1 and dend > 0


def analyze_exp(train_dir: Path, *, train_t: float | None = None) -> dict[str, Any]:
    params_path = train_dir / "Parameters_00.xml"
    p = load_train_params(params_path)
    feas = analyze_one(params_path, mode="post", est_delay=None, train_t=train_t)
    l_target = feas["L_target"]
    l_actual = p["DendriteLength"]
    iter_budget = feas["iter_budget_required"]

    traces = load_trace_vectors(train_dir)
    log_path = train_dir / "run_console.log"
    iters = parse_console_iterations(log_path)
    iter_count = iters[-1]["iter"] + 1 if iters else feas.get("iter_count")
    log_status = diagnose_console_log(log_path)

    est = estimate_est_delay_from_l(p["Expected"], l_actual) or feas["EstDelayPerSeg"]
    l_target_cold = compute_l_target(p["Expected"], est)

    dend_rows: list[dict[str, Any]] = []
    dend_blockers: list[str] = []

    for i in range(K_NUM_DENDRITES):
        L = l_actual[i] if i < len(l_actual) else 1
        lt = l_target[i] if i < len(l_target) else 1

        last_abs_dt = 0.0
        if "LastAbsDtTrace" in traces and i < len(traces["LastAbsDtTrace"]):
            last_abs_dt = traces["LastAbsDtTrace"][i]
        elif iters:
            last_abs_dt = iters[-1]["last_abs_dt"][i] if i < len(iters[-1]["last_abs_dt"]) else 0.0

        res_status = traces.get("ResistanceStatusTrace", [0] * 4)[i] if traces else 0.0
        no_improve = traces.get("NoImproveResistanceTrace", [0] * 4)[i] if traces else 0.0
        amp_dt = traces.get("AmpDtTrace", [0] * 4)[i] if traces else 0.0
        tip_r = p["TipSynapseResistance"][i] if i < len(p["TipSynapseResistance"]) else 0.0

        peak_valid = None
        if iters and i < len(iters[-1].get("peak_valid", [])):
            peak_valid = iters[-1]["peak_valid"][i]

        plateau = detect_length_plateau(iters, i)

        blocker = classify_dendrite(
            i,
            L=L,
            l_target=lt,
            last_abs_dt=last_abs_dt,
            sync_tol=p["SyncTolerance"],
            res_status=res_status,
            no_improve=no_improve,
            amp_dt=amp_dt,
            tip_r=tip_r,
            r_min=p["ResistanceMin"],
            peak_valid=peak_valid,
            iter_count=iter_count,
            iter_budget=iter_budget,
            length_plateau=plateau,
        )
        if i == REF_DENDRITE and blocker not in ("DONE",):
            blocker = "DONE" if L == 1 else blocker
        dend_blockers.append(blocker)
        dend_rows.append(
            {
                "dend": i,
                "L": L,
                "L_target": lt,
                "last_abs_dt": last_abs_dt,
                "sync_ok": length_sync_ok(last_abs_dt, p["SyncTolerance"]),
                "res_status": res_status,
                "no_improve": no_improve,
                "amp_dt": amp_dt,
                "tip_R": tip_r,
                "blocker": blocker,
            }
        )

    overall = overall_blocker(dend_blockers, p["IsNeedToTrain"], log_status)
    if p["IsNeedToTrain"] == "0" and l_vectors_match(l_actual, l_target_cold):
        overall = "DONE"

    return {
        "exp": train_dir.parent.name,
        "train_dir": str(train_dir),
        "blocker": overall,
        "log_status": log_status,
        "L_actual": l_actual,
        "L_target": l_target,
        "EstDelayPerSeg": est,
        "iter_count": iter_count,
        "iter_budget_required": iter_budget,
        "feasibility_verdict": feas["verdict"],
        "IsNeedToTrain": p["IsNeedToTrain"],
        "FixedLTZ": p["FixedLTZThreshold"],
        "dendrites": dend_rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("train_dirs", nargs="*", type=Path)
    ap.add_argument("--meta", type=Path)
    ap.add_argument("--grid", type=Path)
    ap.add_argument("--train-t", type=float, default=None)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    dirs: list[Path] = list(args.train_dirs)
    if args.meta and args.grid:
        for row in load_meta_exps(args.meta, args.grid):
            dirs.append(Path(row["train_dir"]))

    if not dirs:
        ap.error("provide train dirs or --meta + --grid")

    results = []
    for d in dirs:
        if not (d / "Parameters_00.xml").exists():
            results.append({"train_dir": str(d), "blocker": "MISSING", "error": "no Parameters"})
            continue
        results.append(analyze_exp(d, train_t=args.train_t))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        flat_rows = []
        for r in results:
            base = {k: v for k, v in r.items() if k != "dendrites"}
            for k in ("L_actual", "L_target"):
                if isinstance(base.get(k), list):
                    base[k] = " ".join(str(x) for x in base[k])
            flat_rows.append(base)
        with args.output.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "exp", "blocker", "feasibility_verdict", "L_actual", "L_target",
                    "EstDelayPerSeg", "iter_count", "iter_budget_required",
                    "IsNeedToTrain", "FixedLTZ", "log_status",
                ],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(flat_rows)
        if args.output.with_suffix(".json").name != args.output.name:
            args.output.with_suffix(".json").write_text(
                json.dumps(results, indent=2), encoding="utf-8"
            )

    if not args.json:
        for r in results:
            print(
                f"{r.get('exp','?')}: blocker={r.get('blocker')} "
                f"feas={r.get('feasibility_verdict')} L={r.get('L_actual')} "
                f"target={r.get('L_target')} NeedTrain={r.get('IsNeedToTrain')}"
            )
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

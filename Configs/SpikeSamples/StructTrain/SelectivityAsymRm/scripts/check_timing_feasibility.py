#!/usr/bin/env python3
"""L_target and iteration budget from InputPattern + timing params."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from asymrm_train_common import (
    K_DELAY_PER_SEG_DEFAULT,
    K_MAX_LENGTH_STEP,
    REF_DENDRITE,
    compute_iter_budget,
    compute_l_target,
    estimate_est_delay_from_l,
    iter_count_from_train_t,
    load_meta_exps,
    load_train_params,
    l_vectors_match,
    read_gts_from_ini,
)


def verdict(
    l_actual: list[int],
    l_target: list[int],
    *,
    need_train: str | None,
    iter_count: int | None,
    iter_budget: int,
    sync_tol: float,
    last_abs_dt: list[float] | None,
    l_reference: list[int] | None = None,
) -> str:
    if l_reference and len(l_reference) == len(l_actual):
        for i, (la, lr) in enumerate(zip(l_actual, l_reference)):
            if i == REF_DENDRITE:
                continue
            if la < lr and la == l_target[i]:
                return "L_BELOW_REFERENCE"
        if l_vectors_match(l_actual, l_reference):
            if need_train == "0":
                return "SYNC_OK"
            if last_abs_dt and any(
                d > sync_tol + 1e-12 for i, d in enumerate(last_abs_dt) if i != REF_DENDRITE
            ):
                return "AMP_PENDING"
            return "AMP_PENDING"
    if l_vectors_match(l_actual, l_target):
        if need_train == "0":
            return "SYNC_OK"
        if last_abs_dt and any(d > sync_tol + 1e-12 for i, d in enumerate(last_abs_dt) if i != REF_DENDRITE):
            return "AMP_PENDING"
        return "AMP_PENDING"
    if iter_count is not None and iter_count < iter_budget:
        if any(la < lt for la, lt in zip(l_actual, l_target)):
            return "NEEDS_MORE_TIME"
    mism = sum(1 for la, lt in zip(l_actual, l_target) if la != lt)
    if mism >= 2 and all(la <= 1 for la, lt in zip(l_actual[1:], l_target[1:]) if lt > 1):
        return "NEEDS_MORE_TIME"
    if mism > 0:
        return "TIMING_MISMATCH"
    return "INFEASIBLE"


def analyze_one(
    params_path: Path,
    *,
    mode: str,
    est_delay: float | None,
    train_t: float | None,
) -> dict:
    p = load_train_params(params_path)
    train_dir = params_path.parent
    l_actual = p["DendriteLength"]
    expected = p["Expected"]

    if mode == "post":
        est = estimate_est_delay_from_l(expected, l_actual) or est_delay or K_DELAY_PER_SEG_DEFAULT
    else:
        est = est_delay or K_DELAY_PER_SEG_DEFAULT

    l_target = compute_l_target(expected, est)
    iter_budget = compute_iter_budget(l_target)
    iter_count = None
    if train_t is not None:
        max_l = max(l_actual) if l_actual else 1
        iter_count = iter_count_from_train_t(train_t, p["IterationGap"], max_l)
    elif (train_dir / "run_console.log").is_file():
        from asymrm_train_common import parse_console_iterations

        iters = parse_console_iterations(train_dir / "run_console.log")
        iter_count = iters[-1]["iter"] + 1 if iters else None

    traces: dict = {}
    try:
        from asymrm_train_common import load_trace_vectors

        tv = load_trace_vectors(train_dir)
        if "LastAbsDtTrace" in tv:
            traces["last_abs_dt"] = tv["LastAbsDtTrace"]
    except Exception:
        pass

    l_reference = None
    try:
        from patch_l_reference import get_reference_l

        l_reference = get_reference_l(params_path.parent.parent.name)
    except Exception:
        pass

    v = verdict(
        l_actual,
        l_target,
        need_train=p["IsNeedToTrain"],
        iter_count=iter_count,
        iter_budget=iter_budget,
        sync_tol=p["SyncTolerance"],
        last_abs_dt=traces.get("last_abs_dt"),
        l_reference=l_reference,
    )

    delta = [a - t for a, t in zip(l_actual, l_target)]
    gts = read_gts_from_ini(train_dir)

    l_sync_peak = l_target
    try:
        from asymrm_train_common import compute_l_target as clt

        l_sync_peak = clt(expected, est, ref_peak=expected[-1] if expected else None)
    except Exception:
        pass

    return {
        "exp": params_path.parent.parent.name,
        "params": str(params_path),
        "mode": mode,
        "EstDelayPerSeg": est,
        "Expected": expected,
        "L_target": l_target,
        "L_sync_peak": l_sync_peak,
        "L_actual": l_actual,
        "delta_L": delta,
        "iter_budget_required": iter_budget,
        "iter_count": iter_count,
        "verdict": v,
        "SyncTolerance": p["SyncTolerance"],
        "GTS": gts,
        "IsNeedToTrain": p["IsNeedToTrain"],
        "L_reference": l_reference,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("params", nargs="*", type=Path)
    ap.add_argument("--meta", type=Path)
    ap.add_argument("--grid", type=Path)
    ap.add_argument("--cold", action="store_true", help="Use default EstDelayPerSeg")
    ap.add_argument("--post", action="store_true", help="Estimate EstDelayPerSeg from L_actual")
    ap.add_argument("--est-delay", type=float, default=None)
    ap.add_argument("--train-t", type=float, default=None)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    mode = "post" if args.post else "cold"
    paths: list[Path] = list(args.params)
    if args.meta and args.grid:
        for row in load_meta_exps(args.meta, args.grid):
            paths.append(Path(row["params"]))

    if not paths:
        ap.error("provide params paths or --meta + --grid")

    results = []
    for p in paths:
        if not p.exists():
            results.append({"params": str(p), "verdict": "MISSING", "error": "file not found"})
            continue
        results.append(
            analyze_one(p, mode=mode, est_delay=args.est_delay, train_t=args.train_t)
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.suffix == ".json":
            args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
        else:
            fields = [
                "exp", "verdict", "EstDelayPerSeg", "L_target", "L_actual", "delta_L",
                "iter_budget_required", "iter_count", "GTS", "IsNeedToTrain",
            ]
            with args.output.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
                w.writeheader()
                for r in results:
                    row = dict(r)
                    for k in ("L_target", "L_actual", "delta_L"):
                        if k in row and isinstance(row[k], list):
                            row[k] = " ".join(str(x) for x in row[k])
                    w.writerow(row)

    for r in results:
        exp = r.get("exp", r.get("params", "?"))
        lt = r.get("L_target", [])
        la = r.get("L_actual", [])
        print(
            f"{exp}: {r.get('verdict','?')} est={r.get('EstDelayPerSeg','?')} "
            f"L_target={' '.join(map(str, lt))} L_actual={' '.join(map(str, la))} "
            f"budget={r.get('iter_budget_required','?')} iter={r.get('iter_count','?')}"
        )

    if args.json:
        print(json.dumps(results, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()

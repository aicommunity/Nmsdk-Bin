#!/usr/bin/env python3
"""Decide whether to run the next adaptive length step (skip hopeless / plateau cases)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asymrm_train_common import (
    K_NUM_DENDRITES,
    REF_DENDRITE,
    compute_needed_delays,
    delay_len_of,
    estimate_est_delay_from_l,
    length_sync_ok,
    load_train_params,
    load_trace_vectors,
    parse_console_iterations,
)
from patch_l_reference import at_l_reference, effective_l_target, get_reference_l

try:
    from check_timing_feasibility import analyze_one
except ImportError:
    analyze_one = None  # type: ignore


HOPELESS_TOL_MULT = 5.0
L_REF_SENTINEL_DT = 1.0


def worst_under_gap_tol(
    l_actual: list[int],
    needed: list[float],
    est: float,
    sync_tol: float,
) -> tuple[int, float]:
    """Return (dend, gap/tol) for largest cable under-shoot on non-ref dendrites."""
    worst_i = -1
    worst_ratio = 0.0
    for i in range(min(K_NUM_DENDRITES - 1, len(l_actual))):
        if i == REF_DENDRITE:
            continue
        cable = delay_len_of(l_actual[i], est)
        gap = needed[i] - cable
        if gap > sync_tol * 0.5:
            ratio = gap / sync_tol
            if ratio > worst_ratio:
                worst_ratio = ratio
                worst_i = i
    return worst_i, worst_ratio


def length_plateau(train_dir: Path) -> bool:
    iters = parse_console_iterations(train_dir / "run_console.log")
    if len(iters) < 2:
        return False
    tail = iters[-6:]
    lens = [x.get("len") for x in tail if x.get("len")]
    if len(lens) < 2:
        return False
    flat = all(a == b for a, b in zip(lens[:-1], lens[1:]))
    return flat


def valid_peak_dt(last_abs_dt: list[float]) -> bool:
    if not last_abs_dt:
        return False
    for i in range(min(3, len(last_abs_dt))):
        if i == REF_DENDRITE:
            continue
        if last_abs_dt[i] >= L_REF_SENTINEL_DT:
            return False
    return True


def decide(
    train_dir: Path,
    *,
    next_step: float,
    cumulative: float,
    max_length_step: float | None,
    hopeless_tol_mult: float,
) -> dict:
    params_path = train_dir / "Parameters_00.xml"
    p = load_train_params(params_path)
    exp = train_dir.parent.name
    l_actual = p["DendriteLength"]
    sync_tol = p["SyncTolerance"]
    traces = load_trace_vectors(train_dir)
    last_dt = traces.get("LastAbsDtTrace", [])

    l_formula = None
    if analyze_one is not None:
        feas = analyze_one(params_path, mode="post", est_delay=None, train_t=None)
        l_formula = feas.get("L_target")
    l_ref = get_reference_l(exp)
    l_target = effective_l_target(l_formula or l_actual, l_ref)

    est = estimate_est_delay_from_l(p["Expected"], l_actual) or 0.005
    needed = compute_needed_delays(p["Expected"])
    _, gap_ratio = worst_under_gap_tol(l_actual, needed, est, sync_tol)

    at_ref = at_l_reference(l_actual, l_ref)
    plateau = length_plateau(train_dir)
    sync_ok = valid_peak_dt(last_dt) and all(
        length_sync_ok(last_dt[i], sync_tol)
        for i in range(min(3, len(last_dt)))
        if i != REF_DENDRITE
    )

    action = "proceed"
    reason = ""

    if max_length_step is not None and next_step > max_length_step:
        action = "skip_step"
        reason = f"next_step {next_step} > LENGTH_MAX_STEP {max_length_step}"

    elif at_ref and not sync_ok:
        action = "abort_length"
        reason = "L at reference; further length steps unlikely to help — use L-ref refresh + amp"

    elif at_ref and sync_ok:
        action = "abort_length"
        reason = "L at reference and sync_ok — proceed to amp"

    elif gap_ratio >= hopeless_tol_mult and plateau:
        action = "abort_length"
        reason = (
            f"LENGTH_UNDER hopeless: worst gap {gap_ratio:.1f}× tol, L plateau "
            f"{l_actual} (target {l_target})"
        )

    elif plateau and next_step >= 2560:
        action = "skip_step"
        reason = f"L plateau {l_actual} after T={cumulative}; skip large step {next_step}"

    elif gap_ratio >= hopeless_tol_mult and next_step >= 1280:
        action = "skip_step"
        reason = f"LENGTH_UNDER {gap_ratio:.1f}× tol; skip step {next_step}"

    return {
        "exp": exp,
        "action": action,
        "reason": reason,
        "next_step": next_step,
        "cumulative": cumulative,
        "L_actual": l_actual,
        "L_target": l_target,
        "L_reference": l_ref,
        "at_l_reference": at_ref,
        "length_plateau": plateau,
        "sync_ok": sync_ok,
        "worst_gap_tol": gap_ratio,
        "last_abs_dt": last_dt,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("train_dir", type=Path)
    ap.add_argument("--next-step", type=float, required=True)
    ap.add_argument("--cumulative", type=float, default=0)
    ap.add_argument("--max-length-step", type=float, default=None)
    ap.add_argument("--hopeless-tol-mult", type=float, default=HOPELESS_TOL_MULT)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    r = decide(
        args.train_dir,
        next_step=args.next_step,
        cumulative=args.cumulative,
        max_length_step=args.max_length_step,
        hopeless_tol_mult=args.hopeless_tol_mult,
    )
    if args.json:
        print(json.dumps(r))
        sys.exit(0)
    else:
        print(f"{r['exp']}: {r['action']} — {r['reason'] or 'ok'}")
    if r["action"] == "proceed":
        sys.exit(0)
    sys.exit(2 if r["action"] == "skip_step" else 3)


if __name__ == "__main__":
    main()

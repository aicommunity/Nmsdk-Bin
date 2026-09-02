#!/usr/bin/env python3
"""Compare formula L_target vs L_reference cable residuals and measured peak dt."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asymrm_train_common import (
    compute_needed_delays,
    delay_len_of,
    estimate_est_delay_from_l,
    load_train_params,
)
from patch_l_reference import effective_l_target, get_reference_l
from asymrm_train_common import compute_l_target


def compare_exp(params_path: Path) -> None:
    p = load_train_params(params_path)
    exp = params_path.parent.parent.name
    expected = p["Expected"]
    tol = p["SyncTolerance"]
    needed = compute_needed_delays(expected)
    l_formula = compute_l_target(expected, estimate_est_delay_from_l(expected, p["DendriteLength"]) or 0.005)
    l_ref = get_reference_l(exp)
    l_eff = effective_l_target(l_formula, l_ref)

    print(f"## {exp}")
    print(f"SyncTolerance={tol:.6f}s ({tol*1000:.3f}ms)")
    print(f"L_formula={l_formula}  L_reference={l_ref}  L_effective={l_eff}")
    print()
    print("| dend | needed | L | cable_delay | residual | |res|/tol |")
    print("|:----:|:------:|:-:|:-----------:|:--------:|:-------:|")

    for label, L in [("formula", l_formula), ("reference", l_ref or l_eff)]:
        if L is None:
            continue
        est = estimate_est_delay_from_l(expected, L) or 0.005
        print(f"| **{label}** | | | | | |")
        for i in range(3):
            cd = delay_len_of(L[i], est)
            res = needed[i] - cd
            print(
                f"| {i} | {needed[i]*1000:.3f}ms | {L[i]} | {cd*1000:.3f}ms | "
                f"{res*1000:+.3f}ms | {abs(res)/tol:.2f}× |"
            )
        if label == "formula" and l_ref:
            est3 = estimate_est_delay_from_l(expected, l_formula) or 0.005
            est4 = estimate_est_delay_from_l(expected, l_ref) or 0.005
            d3 = delay_len_of(l_formula[2], est3)
            d4 = delay_len_of(l_ref[2], est4)
            delta_ms = (d4 - d3) * 1000
            print(f"\ndend2 cable delta L4-L3: {delta_ms:+.3f}ms (formula rounds down; LtzCal Done uses L4)\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("params", nargs="+", type=Path)
    args = ap.parse_args()
    for p in args.params:
        if p.exists():
            compare_exp(p)
        else:
            print(f"skip missing {p}")


if __name__ == "__main__":
    main()

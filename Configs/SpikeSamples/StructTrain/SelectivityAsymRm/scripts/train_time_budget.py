#!/usr/bin/env python3
"""Wall-clock time budget calibration and step abort helpers for AsymRm training."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from asymrm_train_common import (
    REF_DENDRITE,
    effective_iteration_gap_sec,
    iter_count_from_train_t,
    load_train_params,
    parse_console_iterations,
    read_gts_from_ini,
)

CALIB_FILE = "wall_clock_calibration.json"
DEFAULT_WALL_MULT = 2.0
DEFAULT_PLATEAU_CHECKS = 6


def pattern_span_from_params(p: dict[str, Any]) -> float:
    pat = p.get("InputPattern") or []
    return sum(pat) if pat else 0.025


def total_sim_budget(
    length_steps: list[int],
    amp_steps: list[int],
    *,
    iteration_gap: float = 1.5,
    max_l: int = 20,
) -> dict[str, Any]:
    length_sim = sum(length_steps)
    amp_sim = sum(amp_steps)
    return {
        "length_sim_sec": length_sim,
        "amp_sim_sec": amp_sim,
        "total_sim_sec": length_sim + amp_sim,
        "length_iter_est": iter_count_from_train_t(length_sim, iteration_gap, max_l),
        "amp_iter_est": iter_count_from_train_t(amp_sim, iteration_gap, max_l),
    }


def load_calibration(campaign_root: Path) -> dict[str, Any]:
    p = campaign_root / CALIB_FILE
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_calibration(campaign_root: Path, data: dict[str, Any]) -> None:
    (campaign_root / CALIB_FILE).write_text(json.dumps(data, indent=2), encoding="utf-8")


def calibrate_from_run(
    train_dir: Path,
    *,
    sim_t: float,
    wall_sec: float,
    gts: int | None = None,
    span_ms: float | None = None,
) -> dict[str, Any]:
    gts = gts or read_gts_from_ini(train_dir) or 0
    p = load_train_params(train_dir / "Parameters_00.xml")
    span = span_ms if span_ms is not None else pattern_span_from_params(p) * 1000
    coef = wall_sec / sim_t if sim_t > 0 else 0.0
    return {
        "gts": gts,
        "span_ms": span,
        "sim_t": sim_t,
        "wall_sec": wall_sec,
        "wall_per_sim_sec": coef,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def lookup_coef(cal: dict[str, Any], gts: int, span_ms: float) -> float | None:
    key = f"gts{gts}_span{int(span_ms)}"
    entry = cal.get("entries", {}).get(key)
    if entry:
        return float(entry.get("wall_per_sim_sec", 0))
    entries = cal.get("entries", {})
    if entries:
        return float(next(iter(entries.values())).get("wall_per_sim_sec", 0))
    return None


def check_step_budget(
    train_dir: Path,
    *,
    next_step_sim: float,
    campaign_root: Path,
    wall_budget_sec: float | None = None,
    wall_mult: float = DEFAULT_WALL_MULT,
) -> dict[str, Any]:
    train_dir = Path(train_dir)
    p = load_train_params(train_dir / "Parameters_00.xml")
    gts = read_gts_from_ini(train_dir) or 0
    span_ms = pattern_span_from_params(p) * 1000
    cal = load_calibration(campaign_root)
    coef = lookup_coef(cal, gts, span_ms)

    out: dict[str, Any] = {"action": "proceed", "coef": coef, "next_step_sim": next_step_sim}
    if coef is None or coef <= 0:
        out["reason"] = "no_calibration"
        return out

    exp_wall = next_step_sim * coef
    out["expected_wall_sec"] = exp_wall
    budget = wall_budget_sec
    if budget is None:
        max_l = max(p["DendriteLength"]) if p["DendriteLength"] else 1
        gap = effective_iteration_gap_sec(p["IterationGap"], max_l)
        budget = (next_step_sim / max(gap, 1e-6)) * gap * coef * wall_mult
    out["wall_budget_sec"] = budget
    if exp_wall > budget:
        out["action"] = "abort"
        out["reason"] = f"expected_wall {exp_wall:.0f}s > budget {budget:.0f}s"
    return out


def poll_plateau(train_dir: Path, *, sync_tol: float, checks: int = DEFAULT_PLATEAU_CHECKS) -> dict[str, Any]:
    iters = parse_console_iterations(train_dir / "run_console.log")
    if len(iters) < checks:
        return {"plateau": False, "reason": "insufficient_iters"}
    tail = iters[-checks:]
    lens = [x.get("len") for x in tail]
    if lens and all(a == b for a, b in zip(lens[:-1], lens[1:])):
        dts = []
        for x in tail:
            la = x.get("last_abs_dt") or []
            non_ref = [la[i] for i in range(min(3, len(la))) if i != REF_DENDRITE]
            if non_ref:
                dts.append(max(non_ref))
        if dts and max(dts) - min(dts) < sync_tol * 0.1:
            return {"plateau": True, "reason": "L_and_dt_flat", "worst_dt": max(dts)}
    return {"plateau": False}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_cal = sub.add_parser("calibrate")
    p_cal.add_argument("train_dir", type=Path)
    p_cal.add_argument("--sim-t", type=float, required=True)
    p_cal.add_argument("--wall-sec", type=float, required=True)
    p_cal.add_argument("--campaign-root", type=Path, default=None)

    p_chk = sub.add_parser("check-step")
    p_chk.add_argument("train_dir", type=Path)
    p_chk.add_argument("--next-step", type=float, required=True)
    p_chk.add_argument("--campaign-root", type=Path, required=True)
    p_chk.add_argument("--wall-budget", type=float, default=None)

    p_pl = sub.add_parser("plateau")
    p_pl.add_argument("train_dir", type=Path)

    p_tot = sub.add_parser("total-budget")
    p_tot.add_argument("--length-steps", type=int, nargs="+", default=[80, 160, 320])
    p_tot.add_argument("--amp-steps", type=int, nargs="+", default=[320, 640])

    args = ap.parse_args()

    if args.cmd == "calibrate":
        root = args.campaign_root or args.train_dir.parent.parent
        entry = calibrate_from_run(args.train_dir, sim_t=args.sim_t, wall_sec=args.wall_sec)
        cal = load_calibration(root)
        cal.setdefault("entries", {})
        key = f"gts{entry['gts']}_span{int(entry['span_ms'])}"
        cal["entries"][key] = entry
        save_calibration(root, cal)
        print(json.dumps(entry, indent=2))
        return 0

    if args.cmd == "check-step":
        r = check_step_budget(
            args.train_dir,
            next_step_sim=args.next_step,
            campaign_root=args.campaign_root,
            wall_budget_sec=args.wall_budget,
        )
        print(json.dumps(r, indent=2))
        return 0 if r["action"] == "proceed" else 1

    if args.cmd == "plateau":
        p = load_train_params(args.train_dir / "Parameters_00.xml")
        print(json.dumps(poll_plateau(args.train_dir, sync_tol=p["SyncTolerance"]), indent=2))
        return 0

    if args.cmd == "total-budget":
        print(json.dumps(total_sim_budget(args.length_steps, args.amp_steps), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

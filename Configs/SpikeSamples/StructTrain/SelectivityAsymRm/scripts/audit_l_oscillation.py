#!/usr/bin/env python3
"""Audit L oscillation: reconstruct needed/delay/dt at each DendriteLength transition."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from asymrm_train_common import (
    K_NUM_DENDRITES,
    REF_DENDRITE,
    compute_needed_delays,
    delay_len_of,
    estimate_est_delay_from_l,
    load_train_params,
    parse_console_iterations,
    parse_trace_tail_rows,
    resolve_trace_path,
)
from patch_l_reference import get_reference_l

PEAK_INVALID = 1.501


def parse_l_transitions_from_console(train_dir: Path) -> list[dict[str, Any]]:
    """L transitions from FinishTrainingIteration len= in run_console.log."""
    iters = parse_console_iterations(train_dir / "run_console.log")
    events: list[dict[str, Any]] = []
    prev_l: list[int] | None = None
    for it in iters:
        cur = it.get("len")
        if not cur:
            continue
        sim_t = float(it.get("iter", 0))
        if prev_l is None:
            prev_l = list(cur)
            continue
        for d in range(min(len(cur), len(prev_l))):
            if cur[d] != prev_l[d]:
                events.append(
                    {
                        "sim_t": sim_t,
                        "dendrite": d,
                        "L_from": prev_l[d],
                        "L_to": cur[d],
                        "L_vector": list(cur),
                        "source": "console",
                    }
                )
        prev_l = list(cur)
    return events


def parse_l_transitions_stream(trace_path: Path) -> list[dict[str, Any]]:
    """Full-file scan for L transitions (handles long runs)."""
    if not trace_path.is_file():
        return []
    events: list[dict[str, Any]] = []
    prev_l: list[int] | None = None
    try:
        with trace_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 6:
                    continue
                try:
                    t = float(parts[1].replace(",", "."))
                    vals = [int(round(float(x.replace(",", ".")))) for x in parts[2:6]]
                except ValueError:
                    continue
                if prev_l is None:
                    prev_l = vals
                    continue
                for d in range(min(len(vals), len(prev_l))):
                    if vals[d] != prev_l[d]:
                        events.append(
                            {
                                "sim_t": t,
                                "dendrite": d,
                                "L_from": prev_l[d],
                                "L_to": vals[d],
                                "L_vector": list(vals),
                                "source": "trace",
                            }
                        )
                prev_l = vals
    except OSError:
        return events
    return events


def nearest_console_iter(iters: list[dict], sim_t: float) -> dict | None:
    if not iters:
        return None
    best = min(iters, key=lambda x: abs(x.get("sim_t", x.get("iter", 0)) - sim_t))
    return best


def enrich_event(
    ev: dict[str, Any],
    *,
    needed: list[float],
    est_delay: float,
    sync_tol: float,
    console_iters: list[dict],
    last_dt_rows: list[tuple[float, list[float]]],
) -> dict[str, Any]:
    d = ev["dendrite"]
    L_from = ev["L_from"]
    L_to = ev["L_to"]
    nd = needed[d] if d < len(needed) else 0.0
    delay_len_from = delay_len_of(L_from, est_delay)
    delay_len_to = delay_len_of(L_to, est_delay)
    dt_from = nd - delay_len_from
    dt_to = nd - delay_len_to

  # nearest last_abs_dt at transition time
    last_dt = None
    for t, vals in reversed(last_dt_rows):
        if t <= ev["sim_t"] + 1e-6 and len(vals) > d:
            last_dt = vals[d]
            break

    direction = "grow" if L_to > L_from else "shrink"
    driver = "delay_len"
    if last_dt is not None and last_dt <= sync_tol and abs(dt_from) > sync_tol:
        driver = "cable_model_vs_synced_peak"

    ev.update(
        {
            "needed": nd,
            "est_delay_per_seg": est_delay,
            "delay_len_from": delay_len_from,
            "delay_len_to": delay_len_to,
            "dt_from": dt_from,
            "dt_to": dt_to,
            "last_abs_dt_at_t": last_dt,
            "direction": direction,
            "driver": driver,
        }
    )
    return ev


def audit_train_dir(
    train_dir: Path,
    stat_dir: Path,
    *,
    reference_l: list[int] | None = None,
) -> dict[str, Any]:
    train_dir = Path(train_dir)
    p = load_train_params(train_dir / "Parameters_00.xml")
    expected = p["Expected"]
    needed = compute_needed_delays(expected)
    est = estimate_est_delay_from_l(expected, p["DendriteLength"]) or 0.005
    sync_tol = p["SyncTolerance"]

    lp = resolve_trace_path(stat_dir, "DendriteLengthTrace")
    dt_path = resolve_trace_path(stat_dir, "LastAbsDtTrace")
    dt_rows = parse_trace_tail_rows(dt_path, tail_rows=100000) if dt_path else []
    transitions = parse_l_transitions_stream(lp) if lp else []
    if not transitions:
        transitions = parse_l_transitions_from_console(train_dir)
    console = parse_console_iterations(train_dir / "run_console.log")
    # attach sim_t from iter if missing
    for i, it in enumerate(console):
        it.setdefault("sim_t", float(it.get("iter", i)))

    enriched = [
        enrich_event(
            ev,
            needed=needed,
            est_delay=est,
            sync_tol=sync_tol,
            console_iters=console,
            last_dt_rows=dt_rows,
        )
        for ev in transitions
    ]

    ref_l = reference_l or get_reference_l(train_dir.parent.name)
    ref_analysis = None
    if ref_l:
        ref_analysis = {
            "reference_L": ref_l,
            "delay_len_at_ref": [delay_len_of(l, est) for l in ref_l],
            "needed": needed,
            "dt_at_ref": [
                (needed[i] - delay_len_of(ref_l[i], est)) if i != REF_DENDRITE else 0.0
                for i in range(K_NUM_DENDRITES)
            ],
        }

    by_dend: dict[int, int] = {}
    for ev in enriched:
        by_dend[ev["dendrite"]] = by_dend.get(ev["dendrite"], 0) + 1

    drivers: dict[str, int] = {}
    for ev in enriched:
        drivers[ev.get("driver", "?")] = drivers.get(ev.get("driver", "?"), 0) + 1

    return {
        "exp": train_dir.parent.name,
        "stat_dir": str(stat_dir),
        "DendriteLength_final": p["DendriteLength"],
        "reference_L": ref_l,
        "transition_count": len(enriched),
        "transitions_by_dendrite": by_dend,
        "drivers": drivers,
        "reference_analysis": ref_analysis,
        "transitions": enriched,
    }


def write_markdown_report(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# L Oscillation Audit",
        "",
        f"**EXP:** {audit.get('exp')}",
        f"**StatisticLog:** `{audit.get('stat_dir')}`",
        f"**Final L:** {audit.get('DendriteLength_final')}",
        f"**Reference L:** {audit.get('reference_L')}",
        f"**Transitions:** {audit.get('transition_count')}",
        "",
        "## Drivers",
        "",
    ]
    for k, v in sorted((audit.get("drivers") or {}).items()):
        lines.append(f"- {k}: {v}")
    lines.extend(["", "## Transitions (sample)", ""])
    for ev in (audit.get("transitions") or [])[:40]:
        lines.append(
            f"- t={ev['sim_t']:.1f} d{ev['dendrite']} {ev['L_from']}→{ev['L_to']} "
            f"{ev['direction']} needed={ev['needed']:.4f} "
            f"delay_len={ev['delay_len_from']:.4f} dt={ev['dt_from']:.4f} "
            f"last_abs_dt={ev.get('last_abs_dt_at_t')} driver={ev.get('driver')}"
        )
    if audit.get("reference_analysis"):
        ra = audit["reference_analysis"]
        lines.extend(["", "## Reference equilibrium (cable model)", ""])
        for i in range(K_NUM_DENDRITES):
            lines.append(
                f"- d{i}: L={ra['reference_L'][i]} delay_len={ra['delay_len_at_ref'][i]:.4f} "
                f"dt={ra['dt_at_ref'][i]:.4f}"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("train_dir", type=Path)
    ap.add_argument("--stat-dir", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    audit = audit_train_dir(args.train_dir, args.stat_dir)
    if args.json_out:
        args.json_out.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if args.report:
        write_markdown_report(audit, args.report)
    print(json.dumps({k: audit[k] for k in audit if k != "transitions"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

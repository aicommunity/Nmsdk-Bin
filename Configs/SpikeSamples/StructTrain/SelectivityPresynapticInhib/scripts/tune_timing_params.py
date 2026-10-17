#!/usr/bin/env python3
"""Generate / apply SyncTol + PeakMeasureMargin + DelayAgreeMarginMin grids.

Print candidates for a span, or patch XMLs with chosen values.

  tune_timing_params.py --span-ms 100 --list
  tune_timing_params.py xml... --sync-tol S --peak-margin P --agree-min A
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_pattern_scale import (  # noqa: E402
    FLOOR,
    compute_initial,
    patch_file,
)


def uniq_sorted(vals: list[float], lo: float, hi: float) -> list[float]:
    out: list[float] = []
    for v in vals:
        c = max(lo, min(hi, v))
        if not any(abs(c - x) < 1e-12 for x in out):
            out.append(c)
    return sorted(out)


def grid_for_span(span_ms: float) -> list[dict[str, float]]:
    span_s = span_ms / 1000.0
    init = compute_initial(span_s)
    sync0 = init["sync_tol"]
    peak0 = init["peak_margin"]
    dmin = init["delta_min"]
    hi = span_s

    syncs = uniq_sorted(
        [m * sync0 for m in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0)]
        + [dmin, 0.25 * span_s, 0.5 * span_s],
        FLOOR,
        hi,
    )
    peak_hi = min(0.45 * dmin, 0.06)
    peaks = uniq_sorted(
        [m * peak0 for m in (0.5, 0.75, 1.0, 1.25, 1.5)],
        FLOOR,
        max(FLOOR, peak_hi),
    )
    candidates: list[dict[str, float]] = []
    for s, p in itertools.product(syncs, peaks):
        agrees = uniq_sorted([s, p, max(s, min(0.03, p))], FLOOR, hi)
        for a in agrees:
            candidates.append(
                {
                    "sync_tol": s,
                    "peak_margin": p,
                    "agree_min": a,
                    "delta_min": dmin,
                    "sync0": sync0,
                    "peak0": peak0,
                }
            )
    # Done-seeking: never prefer SyncTol below sync0; climb SyncTol with peak≈peak0.
    def key(c: dict[str, float]) -> tuple:
        s, p = c["sync_tol"], c["peak_margin"]
        a0 = max(sync0, min(0.03, peak0))
        below = 0 if s + 1e-15 >= sync0 - 1e-15 else 1
        peak_pri = 0 if abs(p - peak0) < 1e-12 else 1
        agree_pri = 0 if abs(c["agree_min"] - max(s, min(0.03, p))) < 1e-12 else 1
        return (
            below,
            s,
            peak_pri,
            abs(p - peak0),
            agree_pri,
            abs(c["agree_min"] - a0),
        )

    candidates.sort(key=key)
    # Dedup exact triples
    seen: set[tuple[float, float, float]] = set()
    out: list[dict[str, float]] = []
    for c in candidates:
        t = (round(c["sync_tol"], 12), round(c["peak_margin"], 12), round(c["agree_min"], 12))
        if t in seen:
            continue
        seen.add(t)
        out.append(c)
    return out


def next_index_after_sync(span_ms: float, sync_tol: float) -> int | None:
    """First grid index with SyncTol strictly greater than sync_tol."""
    grid = grid_for_span(span_ms)
    cur = float(sync_tol)
    for i, c in enumerate(grid):
        # Require a meaningful step (>1e-6 s) so truncated CLI floats match.
        if c["sync_tol"] - cur > 1e-6:
            return i
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xmls", nargs="*", type=Path)
    ap.add_argument("--span-ms", type=float, required=True)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--index", type=int, default=None, help="Apply grid[index] to xmls")
    ap.add_argument(
        "--next-wider-after-sync",
        type=float,
        default=None,
        help="Print first grid index with SyncTol > given value",
    )
    ap.add_argument("--sync-tol", type=float, default=None)
    ap.add_argument("--peak-margin", type=float, default=None)
    ap.add_argument("--agree-min", type=float, default=None)
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()

    grid = grid_for_span(args.span_ms)
    if args.next_wider_after_sync is not None:
        nxt = next_index_after_sync(args.span_ms, args.next_wider_after_sync)
        print("EMPTY" if nxt is None else nxt)
        return
    if args.list:
        for i, c in enumerate(grid[: args.limit]):
            print(
                f"{i:3d}  SyncTol={c['sync_tol']:.6g}  "
                f"Peak={c['peak_margin']:.6g}  Agree={c['agree_min']:.6g}"
            )
        print(f"# total={len(grid)} (showing {min(args.limit, len(grid))})", file=sys.stderr)
        return

    sync = args.sync_tol
    peak = args.peak_margin
    agree = args.agree_min
    if args.index is not None:
        c = grid[args.index]
        sync, peak, agree = c["sync_tol"], c["peak_margin"], c["agree_min"]
    if sync is None or peak is None or agree is None:
        raise SystemExit("need --sync-tol/--peak-margin/--agree-min or --index")
    if not args.xmls:
        raise SystemExit("xml paths required when applying")

    for p in args.xmls:
        info = patch_file(
            p,
            alpha=None,
            sync_tol=sync,
            peak_margin=peak,
            agree_min=agree,
            do_scale=False,
        )
        print(
            f"tuned {p} SyncTol={info['SyncTolerance']:.6g} "
            f"Peak={info['PeakMeasureMargin']:.6g} Agree={info['DelayAgreeMarginMin']:.6g}"
        )


if __name__ == "__main__":
    main()

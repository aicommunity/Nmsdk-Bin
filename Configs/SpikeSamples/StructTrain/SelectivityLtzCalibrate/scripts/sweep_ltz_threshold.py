#!/usr/bin/env python3
"""Sweep FixedLTZ threshold offline from results.csv (fallback calibrate)."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def sweep(path: Path) -> None:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        print("empty csv")
        return
    ltvs = sorted({float(r["ltz_potential_max"]) for r in rows})
    best = None
    for thr in ltvs:
        tp = sum(1 for r in rows if r["target_class"] == "1" and float(r["ltz_potential_max"]) >= thr)
        tn = sum(1 for r in rows if r["target_class"] == "0" and float(r["ltz_potential_max"]) < thr)
        acc = tp + tn
        target_hit = int(rows[0]["target_class"] == "1" and float(rows[0]["ltz_potential_max"]) >= thr)
        if best is None or acc > best[0] or (acc == best[0] and target_hit > best[3]):
            best = (acc, thr, tp + (len(rows) - tp - tn - (len(rows) - 1 - tn)), target_hit)
    if best:
        print(f"{path.name}: best_acc={best[0]}/8 thr={best[1]:.6g} target_hit={best[3]} (fp={best[2]})")
    # print full sweep for target_hit=1 window
    ok_thr = []
    for thr in ltvs:
        target_hit = int(rows[0]["target_class"] == "1" and float(rows[0]["ltz_potential_max"]) >= thr)
        fp = sum(1 for r in rows[1:] if float(r["ltz_potential_max"]) >= thr)
        if target_hit:
            ok_thr.append((thr, fp))
    if ok_thr:
        print("  target_hit=1 thresholds (thr, fp):", ok_thr[:10])
    else:
        print("  no threshold gives target_hit=1")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path, nargs="+")
    args = ap.parse_args()
    for p in args.csv:
        sweep(p)


if __name__ == "__main__":
    main()

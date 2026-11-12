#!/usr/bin/env python3
"""Offline FixedLTZThreshold sweep from EXP00 CSV."""
import csv
import sys
from pathlib import Path

THRS = [0.0115, 0.0120, 0.0125, 0.0130, 0.0135, 0.0140, 0.0145, 0.0150]


def load_rows(path: Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def main():
    csv_path = Path(sys.argv[1])
    rows = load_rows(csv_path)
    trained = [r for r in rows if r["target_class"] == "1"]
    min_pos = min(float(r["ltz_potential_max"]) for r in trained)
    fp_rows = [r for r in rows if r["target_class"] == "0" and r["neuron_fired"] == "1"]
    max_fp = max((float(r["ltz_potential_max"]) for r in fp_rows), default=0.0)
    print(f"gap={min_pos - max_fp:.7f} min_pos={min_pos} max_fp={max_fp}")
    print("thr,accuracy,fp,fns")
    best = (0, -1.0)
    for thr in THRS:
        ok = 0
        fp = []
        fn = []
        for r in rows:
            fired = float(r["ltz_potential_max"]) >= thr
            expect = r["target_class"] == "1"
            match = fired == expect
            if match:
                ok += 1
            elif expect and not fired:
                fn.append(r["trial"])
            elif not expect and fired:
                fp.append(r["trial"])
        print(f"{thr},{ok}/8,fp={fp},fn={fn}")
        if ok > best[0] or (ok == best[0] and thr < best[1]):
            best = (ok, thr)
    print(f"best_offline={best[0]}/8 thr={best[1]}")


if __name__ == "__main__":
    main()

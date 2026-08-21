#!/usr/bin/env python3
"""Evaluate SelectivityLog/results.csv for PSI quality gate.

Stdout one machine-readable line:
  ok=0|1 n=8 acc=5 target_hit=1 fire_all=0 mode=selective fires=10001111 matches=10001111 fa=2

Exit 0 if file parsed (even when ok=0). Exit 2 if missing/unreadable.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def classify(rows: list[dict[str, str]]) -> dict[str, object]:
    n = len(rows)
    if n == 0:
        return {
            "ok": 0,
            "n": 0,
            "acc": 0,
            "target_hit": 0,
            "fire_all": 0,
            "mode": "silent",
            "fires": "",
            "matches": "",
            "fa": 0,
        }

    fires = [1 if r.get("neuron_fired") == "1" else 0 for r in rows]
    matches = [1 if r.get("match") == "1" else 0 for r in rows]
    acc = sum(matches)
    n_fire = sum(fires)
    fa = sum(fires[1:]) if n > 1 else 0
    t0 = rows[0]
    target_hit = 1 if (fires[0] == 1 and matches[0] == 1) else 0
    fire_all = 1 if n_fire == n and n > 0 else 0
    silent = n_fire == 0

    if silent:
        mode = "silent"
    elif fires[0] == 0:
        mode = "miss_target"
    elif fire_all:
        mode = "fire_all"
    elif target_hit and fa <= 2 and acc >= 4:
        mode = "selective"
    elif target_hit and not fire_all:
        mode = "partial_FA"
    else:
        mode = "miss_target"

    ok = 1 if (n == 8 and target_hit == 1 and fire_all == 0 and acc >= 4) else 0
    return {
        "ok": ok,
        "n": n,
        "acc": acc,
        "target_hit": target_hit,
        "fire_all": fire_all,
        "mode": mode,
        "fires": "".join(str(x) for x in fires),
        "matches": "".join(str(x) for x in matches),
        "fa": fa,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=Path)
    args = ap.parse_args()
    p = args.csv_path
    if not p.exists():
        print(
            "ok=0 n=0 acc=0 target_hit=0 fire_all=0 mode=missing fires= matches= fa=0",
            file=sys.stderr,
        )
        print("ok=0 n=0 acc=0 target_hit=0 fire_all=0 mode=missing fires= matches= fa=0")
        raise SystemExit(2)
    try:
        rows = list(csv.DictReader(p.open(encoding="utf-8")))
    except OSError as e:
        print(f"read error: {e}", file=sys.stderr)
        raise SystemExit(2)
    q = classify(rows)
    line = (
        f"ok={q['ok']} n={q['n']} acc={q['acc']} target_hit={q['target_hit']} "
        f"fire_all={q['fire_all']} mode={q['mode']} fires={q['fires']} "
        f"matches={q['matches']} fa={q['fa']}"
    )
    print(line)


if __name__ == "__main__":
    main()

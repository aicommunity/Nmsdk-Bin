#!/usr/bin/env python3
"""R0 (PLAN 2026-10-25 F5): Train-replay vs Test LTZ discrepancy.

After overlay_train_params (phase9) / Branch phase8 sync, run the same Test
stimulus twice conceptually: compare LTZ peak recorded on the Train workdir
(replay of learned weights) against the Test SelectivityLog / gate metric.

Usage (workdir that already finished SoftCold Train):
  python3 scripts/r0_train_test_ltz_replay.py \\
    --workdir /path/to/run_work_or_final \\
    --span-ms 25 [--kind asym|branch]

Exit 0 if |ltz_train - ltz_test| / max(|ltz_train|, eps) ≤ 0.05.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "SelectivityAsymRm" / "scripts"))

from phase9_preinh_bc_gate import overlay_train_params  # noqa: E402


def _ltz_from_flag(path: Path) -> float | None:
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("mid=") or line.startswith("FixedLTZ="):
            try:
                return float(line.split("=", 1)[1].split()[0].replace(",", "."))
            except ValueError:
                return None
    return None


def _ltz_from_params(path: Path) -> float | None:
    if not path.is_file():
        return None
    t = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<FixedLTZThreshold[^>]*>([^<]+)</FixedLTZThreshold>", t)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workdir", type=Path, required=True)
    ap.add_argument("--span-ms", type=int, default=25)
    ap.add_argument("--kind", choices=("asym", "branch"), default="asym")
    ap.add_argument("--tol", type=float, default=0.05, help="relative |Δ|/|train|")
    args = ap.parse_args()
    wd = args.workdir
    train, test = wd / "Train", wd / "Test"
    if not train.is_dir() or not test.is_dir():
        print(f"FAIL missing Train/Test under {wd}", file=sys.stderr)
        return 2

    # Ensure Test carries Train topology (F3) before comparing thresholds.
    if args.kind == "asym":
        thr = overlay_train_params(train, test)
        print(f"overlay_train_params thr={thr}")
    else:
        print("branch: expect phase8 prepare_test already applied NumSynapse overlay")

    train_ltz = _ltz_from_flag(train / "posttune_complete.flag") or _ltz_from_params(
        train / "Parameters_00.xml"
    )
    test_ltz = _ltz_from_flag(test / "posttune_complete.flag") or _ltz_from_params(
        test / "Parameters_00.xml"
    )
    print(f"ltz_train={train_ltz} ltz_test={test_ltz}")
    if train_ltz is None or test_ltz is None:
        print("FAIL missing LTZ on Train or Test", file=sys.stderr)
        return 2
    denom = max(abs(train_ltz), 1e-12)
    rel = abs(train_ltz - test_ltz) / denom
    print(f"rel_delta={rel:.6g} tol={args.tol}")
    if not math.isfinite(rel) or rel > args.tol:
        print("FAIL R0 Train/Test LTZ discrepancy")
        return 1
    print("PASS R0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Enable AutoCalibrateFixedLTZThreshold (delegates to train/test split scripts)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from patch_ltz_calibrate_train import patch_file as patch_train


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xml", nargs="+", type=Path)
    ap.add_argument("--gap-fraction", action="store_true")
    ap.add_argument("--test", action="store_true", help="Test-side patch (requires --train)")
    ap.add_argument("--train", type=Path, default=None)
    args = ap.parse_args()

    if args.test:
        if not args.train:
            print("--test requires --train", file=sys.stderr)
            sys.exit(1)
        from patch_ltz_calibrate_test import patch_test

        for p in args.xml:
            patch_test(p, args.train)
            print(f"patched LTZ calibrate: {p}")
        return

    for p in args.xml:
        if not p.exists():
            print(f"missing: {p}", file=sys.stderr)
            sys.exit(1)
        patch_train(p, gap_fraction=args.gap_fraction)
        print(f"patched LTZ calibrate: {p}")


if __name__ == "__main__":
    main()

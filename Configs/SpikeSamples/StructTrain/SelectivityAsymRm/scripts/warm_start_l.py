#!/usr/bin/env python3
"""Warm-start DendriteLength on selected dendrites (raise only; never lower)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_ints(s: str) -> list[int]:
    return [int(float(x.replace(",", "."))) for x in s.split() if x.strip()]


def patch_l(params: Path, target: list[int], dendrites: list[int], *, dry_run: bool) -> list[int]:
    text = params.read_text(encoding="utf-8")
    m = re.search(r"<DendriteLength\b[^>]*>([^<]*)</DendriteLength>", text)
    if not m:
        raise SystemExit(f"no DendriteLength in {params}")
    cur = parse_ints(m.group(1))
    new_l = list(cur)
    for i in dendrites:
        if i < 0 or i >= min(len(new_l), len(target), 3):
            continue
        if new_l[i] < target[i]:
            new_l[i] = target[i]
    if new_l != cur and not dry_run:
        new_s = " ".join(str(x) for x in new_l)
        text = re.sub(
            r"(<DendriteLength\b[^>]*>)[^<]*(</DendriteLength>)",
            rf"\g<1>{new_s}\g<2>",
            text,
            count=1,
        )
        params.write_text(text, encoding="utf-8")
    return new_l


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("params", type=Path, help=".../Train/Parameters_00.xml")
    ap.add_argument(
        "--target",
        required=True,
        help='Target L vector, e.g. "12 17 12 1" or "20 17 10 1"',
    )
    ap.add_argument(
        "--dendrites",
        default="0",
        help="Comma-separated non-ref dendrite indices to raise (default: 0)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    target = parse_ints(args.target)
    dens = [int(x) for x in args.dendrites.split(",") if x.strip()]
    new_l = patch_l(args.params, target, dens, dry_run=args.dry_run)
    print(f"{'dry-run ' if args.dry_run else ''}{args.params.parent.parent.name} L -> {new_l}")


if __name__ == "__main__":
    main()

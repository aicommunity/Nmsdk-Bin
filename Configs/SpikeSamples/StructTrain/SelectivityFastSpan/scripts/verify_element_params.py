#!/usr/bin/env python3
"""Verify DissociationTC / Capacity / InhibitionCoeff in a Model_00.xml."""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


def floats(tag: str, text: str) -> list[float]:
    return [float(m) for m in re.findall(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)]


def near(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(a - b) <= max(tol, abs(b) * 1e-9)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("model", type=Path)
    ap.add_argument("--expect-dissoc", type=float, required=True)
    ap.add_argument("--expect-cap", type=float, required=True)
    ap.add_argument("--expect-inh", type=float, default=None)
    ap.add_argument("--no-inh", action="store_true", help="require no InhibitionCoeff=2.5")
    ap.add_argument("--expect-class", type=str, default="")
    ap.add_argument("--min-count", type=int, default=4)
    ap.add_argument("--forbid-bio", action="store_true", default=True)
    args = ap.parse_args()

    if not args.model.exists():
        print(f"FAIL missing {args.model}", file=sys.stderr)
        return 1

    text = args.model.read_text(encoding="utf-8", errors="replace")
    errs: list[str] = []

    if args.expect_class:
        classes = re.findall(r'<Neuron Class="([^"]+)"', text)
        if not classes or classes[0] != args.expect_class:
            errs.append(f"Neuron Class={classes[:1]} expected {args.expect_class}")

    dissocs = floats("DissociationTC", text)
    caps = floats("Capacity", text)
    if len(dissocs) < args.min_count:
        errs.append(f"DissociationTC count {len(dissocs)} < {args.min_count}")
    if len(caps) < args.min_count:
        errs.append(f"Capacity count {len(caps)} < {args.min_count}")

    bad_d = [v for v in dissocs if not near(v, args.expect_dissoc)]
    bad_c = [v for v in caps if not near(v, args.expect_cap)]
    if bad_d:
        errs.append(
            f"DissociationTC unexpected {Counter(round(x, 12) for x in bad_d)} "
            f"(want {args.expect_dissoc}; all={Counter(round(x, 12) for x in dissocs)})"
        )
    if bad_c:
        errs.append(
            f"Capacity unexpected {Counter(round(x, 12) for x in bad_c)} "
            f"(want {args.expect_cap}; all={Counter(round(x, 12) for x in caps)})"
        )

    if args.forbid_bio:
        if any(near(v, 0.005) for v in dissocs) and not near(args.expect_dissoc, 0.005):
            errs.append("found Bio DissociationTC=0.005")
        if any(near(v, 1e-9) for v in caps) and not near(args.expect_cap, 1e-9):
            errs.append("found Bio Capacity=1e-9")

    inhs = floats("InhibitionCoeff", text)
    if args.expect_inh is not None:
        if not any(near(v, args.expect_inh) for v in inhs):
            errs.append(f"missing InhibitionCoeff={args.expect_inh} (have {Counter(inhs)})")
    if args.no_inh:
        if any(near(v, 2.5) for v in inhs):
            errs.append(f"unexpected InhibitionCoeff=2.5 (have {Counter(inhs)})")

    if errs:
        print(f"FAIL {args.model}:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(
        f"OK {args.model.name}: Dissoc×{len(dissocs)}={args.expect_dissoc} "
        f"Cap×{len(caps)}={args.expect_cap}"
        + (f" Inh={args.expect_inh}" if args.expect_inh is not None else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

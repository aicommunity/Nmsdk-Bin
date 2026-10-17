#!/usr/bin/env python3
"""Update AxisYmin/AxisYmax in Interface.xml from a peak value."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("interface", type=Path)
    ap.add_argument("--peak", type=float, required=True)
    ap.add_argument("--graph", type=int, default=0, help="graph index to update")
    ap.add_argument("--margin", type=float, default=0.25)
    args = ap.parse_args()
    peak = abs(args.peak)
    if peak < 1e-12:
        peak = 1.0
    ymin = -0.1 * peak if peak < 2 else -0.1
    ymax = peak * (1.0 + args.margin)
    text = args.interface.read_text(encoding="utf-8")
    # naive: replace Nth AxisYmin/max pair inside graph_N
    gname = f"graph_{args.graph}"
    m = re.search(rf"(<{gname}>.*?</{gname}>)", text, re.DOTALL)
    if not m:
        raise SystemExit(f"graph {gname} not found")
    block = m.group(1)
    block2 = re.sub(r"(<AxisYmin>)[^<]*(</AxisYmin>)", rf"\g<1>{ymin}\2", block, count=1)
    block2 = re.sub(r"(<AxisYmax>)[^<]*(</AxisYmax>)", rf"\g<1>{ymax}\2", block2, count=1)
    text = text[: m.start(1)] + block2 + text[m.end(1) :]
    args.interface.write_text(text, encoding="utf-8")
    print(f"Updated {args.interface} graph_{args.graph}: Y=[{ymin}, {ymax}]")


if __name__ == "__main__":
    main()

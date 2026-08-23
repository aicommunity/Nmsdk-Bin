#!/usr/bin/env python3
"""Train-side LTZ AutoCalibrate patch: UseFixedLTZ=0 during training."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TAG_SPECS: dict[str, tuple[str, str]] = {
    "AutoCalibrateFixedLTZThreshold": ("b", "1"),
    "CalibrateLTZThresholdMode": ("i", "1"),
    "CalibrateLTZThresholdFraction": ("d", "0.99"),
    "CalibrateLTZThresholdMin": ("d", "0.001"),
    "CalibrateLTZThresholdMax": ("d", "0.1"),
}


def set_tag(text: str, tag: str, value: str, count: int = 0) -> str:
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count or 0)


def ensure_tag(text: str, tag: str, elem_type: str, value: str, anchor: str) -> str:
    if re.search(rf"<{tag}\b", text):
        return set_tag(text, tag, value)
    insert = (
        f"\t\t\t\t\t<{tag} Type=\"{elem_type}\" PType=\"257\" IoType=\"17\">{value}</{tag}>"
    )
    pat = rf"(<{anchor}\b[^>]*>[^<]*</{anchor}>)"
    if not re.search(pat, text):
        raise ValueError(f"anchor {anchor} not found for {tag}")
    return re.sub(pat, rf"\1\n{insert}", text, count=1)


def patch_file(path: Path, *, gap_fraction: bool = False, preinh: bool = False) -> None:
    if "Parameters" not in path.name and path.name != "Parameters_00.xml":
        t = path.read_text(encoding="utf-8")
        if "AutoCalibrateFixedLTZThreshold" not in t and "NeuronTimeLearner" not in t:
            return
    t = path.read_text(encoding="utf-8")
    t = set_tag(t, "UseFixedLTZThreshold", "0")
    t = set_tag(t, "LTZThreshold", "100", count=1)
    t = set_tag(t, "FixedLTZThreshold", "0.0115", count=1)

    specs = dict(TAG_SPECS)
    if gap_fraction:
        specs["CalibrateLTZThresholdMode"] = ("i", "0")
        specs["CalibrateLTZThresholdFraction"] = ("d", "0.85")
        specs["CalibrateLTZThresholdMin"] = ("d", "0.0115")
        specs["CalibrateLTZThresholdMax"] = ("d", "0.05")
    elif preinh:
        specs["CalibrateLTZThresholdMax"] = ("d", "0.10")

    for tag, (typ, val) in specs.items():
        t = ensure_tag(t, tag, typ, val, "UseFixedLTZThreshold")
    path.write_text(t, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xml", nargs="+", type=Path)
    ap.add_argument("--gap-fraction", action="store_true", help="Regression golden protocol (mode=0, 0.85)")
    ap.add_argument("--preinh", action="store_true", help="Tier0 preinh: CalibrateMax=0.10")
    args = ap.parse_args()
    for p in args.xml:
        if not p.exists():
            print(f"missing: {p}", file=sys.stderr)
            sys.exit(1)
        patch_file(p, gap_fraction=args.gap_fraction, preinh=args.preinh)
        print(f"patched LTZ train: {p}")


if __name__ == "__main__":
    main()

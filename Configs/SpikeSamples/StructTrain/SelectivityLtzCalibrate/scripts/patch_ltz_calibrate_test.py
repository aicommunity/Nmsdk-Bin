#!/usr/bin/env python3
"""Test-side LTZ patch after sync: UseFixedLTZ=1, copy calibrated FixedLTZ from train."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def read_tag(text: str, tag: str) -> str | None:
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)
    return m.group(1).strip() if m else None


def set_tag(text: str, tag: str, value: str, count: int = 0) -> str:
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count or 0)


def patch_test(test_path: Path, train_path: Path | None) -> None:
    test = test_path.read_text(encoding="utf-8")
    flt = "0.0115"
    if train_path and train_path.exists():
        train = train_path.read_text(encoding="utf-8")
        flt = read_tag(train, "FixedLTZThreshold") or flt
    test = set_tag(test, "UseFixedLTZThreshold", "1", count=1)
    test = set_tag(test, "FixedLTZThreshold", flt, count=1)
    test = set_tag(test, "IsNeedToTrain", "0", count=1)
    test = set_tag(test, "StructureBuildMode", "0", count=1)
    test_path.write_text(test, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("test_xml", type=Path)
    ap.add_argument("--train", type=Path, default=None, help="Train Parameters_00.xml for FixedLTZ copy")
    args = ap.parse_args()
    if not args.test_xml.exists():
        print(f"missing: {args.test_xml}", file=sys.stderr)
        sys.exit(1)
    patch_test(args.test_xml, args.train)
    print(f"patched LTZ test: {args.test_xml}")


if __name__ == "__main__":
    main()

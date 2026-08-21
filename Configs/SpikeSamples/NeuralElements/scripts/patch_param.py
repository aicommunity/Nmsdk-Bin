#!/usr/bin/env python3
"""Replace named XML parameter tags (first or all occurrences)."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def set_tag(text: str, tag: str, value: str, count: int = 0) -> str:
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xml", type=Path)
    ap.add_argument("--set", nargs=2, action="append", metavar=("TAG", "VALUE"), default=[])
    ap.add_argument("--all", action="store_true", help="Replace every occurrence of each tag")
    args = ap.parse_args()
    text = args.xml.read_text(encoding="utf-8")
    count = 0 if args.all else 1
    for tag, value in args.set:
        text = set_tag(text, tag, value, count=count)
    args.xml.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

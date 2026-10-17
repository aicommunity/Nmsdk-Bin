#!/usr/bin/env python3
"""Set learner NeuronClassName (first occurrence under NeuronTimeLearner Parameters)."""
import re
import sys
from pathlib import Path

def patch(path: Path, class_name: str) -> None:
    text = path.read_text(encoding="utf-8")
    # Replace first NeuronClassName in file (learner block is first)
    new, n = re.subn(
        r'(<NeuronClassName Type="std::string" PType="257" IoType="17">)[^<]*(</NeuronClassName>)',
        rf'\g<1>{class_name}\g<2>',
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"NeuronClassName replace failed in {path}: {n}")
    path.write_text(new, encoding="utf-8")

if __name__ == "__main__":
    patch(Path(sys.argv[1]), sys.argv[2])

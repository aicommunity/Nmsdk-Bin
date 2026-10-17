#!/usr/bin/env python3
"""Patch EstDelayPerSeg=0.01 into phase6_480 + tn_classic SoftCold-source archives."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from repro_cold_lib import set_tag_all  # noqa: E402

EST = "0.01"
ESTDELAY_BLOCK = (
    '<EstDelayPerSeg Type="d" PType="257" IoType="17">{value}</EstDelayPerSeg>'
)

TARGETS = [
    ROOT / "SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Train",
    ROOT / "SelectivityPhaseA/Phase6/EXP_480_gen_posttune/Train",
    ROOT / "TimeNeuronTimeLearner/Train",
]


def insert_estdelay(text: str, value: str) -> str:
    if re.search(r"<EstDelayPerSeg\b", text):
        return set_tag_all(text, "EstDelayPerSeg", value)
    block = ESTDELAY_BLOCK.format(value=value)
    if re.search(r"</DendriteLength>", text):
        return re.sub(r"(</DendriteLength>)", rf"\1\n\t\t\t\t\t{block}", text, count=1)
    if re.search(r"</ResistanceMax>", text):
        return re.sub(r"(</ResistanceMax>)", rf"\1\n\t\t\t\t\t{block}", text, count=1)
    raise ValueError("no insertion anchor for EstDelayPerSeg")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    for train in TARGETS:
        for rel in ("Parameters_00.xml", "Model_00.xml"):
            path = train / rel
            if not path.is_file():
                print(f"skip missing {path}")
                continue
            text = path.read_text(encoding="utf-8")
            new = insert_estdelay(text, EST)
            changed = new != text
            print(f"{'DRY ' if args.dry_run else ''}{'PATCH' if changed else 'ok  '} {path}")
            if changed and not args.dry_run:
                path.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

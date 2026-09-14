#!/usr/bin/env python3
"""P4: silent soma mid retry on br480 preinh250 clone."""
from __future__ import annotations

import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

NM = Path("/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole")
ROOT = Path("/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain")
METRICS = ROOT / "scripts" / "selectivity_metrics.py"


def set_tag(text: str, tag: str, value: str) -> str:
    return re.sub(
        rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)",
        lambda m: m.group(1) + value + m.group(2),
        text,
    )


def set_fixed_thr(path: Path, thr: str) -> None:
    t = path.read_text(encoding="utf-8")
    for tag in ("FixedLTZThreshold", "LTZThreshold"):
        t = set_tag(t, tag, thr)
    t = set_tag(t, "UseFixedLTZThreshold", "1")
    t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "0")
    path.write_text(t, encoding="utf-8")


def main() -> None:
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("exp_root", type=Path)
    ap.add_argument("--test-t", type=float, default=40.0)
    args = ap.parse_args()
    test = args.exp_root.resolve() / "Test"
    for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
        set_fixed_thr(p, "1.0")
    with (test / "run_silent_probe.log").open("w") as f:
        subprocess.call(
            [str(NM), "-c", str(test / "Project.ini"), "-s", "-t", str(args.test_t), "-x"],
            stdout=f,
            stderr=subprocess.STDOUT,
        )
    csv_path = test / "SelectivityLog" / "results.csv"
    shutil.copy2(csv_path, test / "SelectivityLog" / "results_silent_thr1.csv")
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    somas = [float(r.get("soma_amp_sum") or 0) for r in rows]
    print("somas", somas)
    tgt, foil = somas[0], max(somas[1:])
    mid = 0.5 * (tgt + foil)
    print("mid", mid, "gap", tgt - foil)
    mid_s = f"{mid:.12g}"
    for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
        set_fixed_thr(p, mid_s)
    with (test / "run_gate.log").open("w") as f:
        subprocess.call(
            [str(NM), "-c", str(test / "Project.ini"), "-s", "-t", str(args.test_t), "-x"],
            stdout=f,
            stderr=subprocess.STDOUT,
        )
    subprocess.check_call([sys.executable, str(METRICS), "-v", str(csv_path)])
    print("thr", mid_s)


if __name__ == "__main__":
    main()

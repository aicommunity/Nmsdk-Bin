#!/usr/bin/env python3
"""PHASE9 P2: AsymRm silent mid (ltz_potential_max) + gate. No Train."""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

NM = Path("/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole")
ROOT = Path("/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain")
METRICS = ROOT / "scripts" / "selectivity_metrics.py"
SILENT_THR = "1.0"


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


def run_nm(ini: Path, tsec: float, log: Path) -> int:
    cmd = [str(NM), "-c", str(ini), "-s", "-t", str(tsec), "-x"]
    with log.open("w") as f:
        return subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)


def col_from_csv(csv_path: Path, col: str) -> list[float]:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    out = []
    for r in rows:
        v = r.get(col) or "0"
        try:
            out.append(float(v))
        except ValueError:
            out.append(0.0)
    return out


def mid_thr(vals: list[float]) -> tuple[float, float]:
    tgt = vals[0]
    below = [s for s in vals[1:] if s < tgt]
    foil = max(below) if below else max(vals[1:] or [0.0])
    gap = tgt - foil
    mid = 0.5 * (tgt + foil) if below else tgt * 0.99
    return mid, gap


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("exp_root", type=Path)
    ap.add_argument("--test-t", type=float, default=40.0)
    ap.add_argument("--silent-thr", default=SILENT_THR)
    ap.add_argument(
        "--metric",
        default="ltz_potential_max",
        choices=("ltz_potential_max", "soma_amp_sum"),
    )
    args = ap.parse_args()
    root = args.exp_root.resolve()
    test = root / "Test"
    csv_path = test / "SelectivityLog" / "results.csv"

    for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
        if p.exists():
            set_fixed_thr(p, args.silent_thr)

    slog = test / "run_silent_probe.log"
    rc = run_nm(test / "Project.ini", args.test_t, slog)
    print("silent rc", rc)
    if not csv_path.exists():
        raise SystemExit("no silent results.csv")
    archived = test / "SelectivityLog" / "results_silent_thr1.csv"
    shutil.copy2(csv_path, archived)
    vals = col_from_csv(archived, args.metric)
    print(args.metric, vals)
    if len(vals) < 8 or max(vals) <= 0:
        # fallback soma if ltz all zero
        if args.metric == "ltz_potential_max":
            vals = col_from_csv(archived, "soma_amp_sum")
            print("fallback soma_amp_sum", vals)
            if len(vals) < 8 or max(vals) <= 0:
                raise SystemExit("silent FAIL")
        else:
            raise SystemExit("silent FAIL")
    mid, gap = mid_thr(vals[:8])
    print(f"mid={mid} gap={gap}")
    if gap <= 0:
        print("FAIL gap<=0", file=sys.stderr)
        sys.exit(3)
    mid_s = f"{mid:.12g}"
    for p in [test / "Parameters_00.xml", test / "Model_00.xml"]:
        if p.exists():
            set_fixed_thr(p, mid_s)

    glog = test / "run_gate.log"
    rc = run_nm(test / "Project.ini", args.test_t, glog)
    print("gate rc", rc)
    subprocess.check_call([sys.executable, str(METRICS), "-v", str(csv_path)])
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    if rows:
        r0 = rows[0]
        t_rel = float(r0.get("neuron_t_rel") or -1)
        isis = [float(r0.get(f"isi{i}") or 0) for i in range(3)]
        pend = sum(isis)
        print(
            f"last-pulse t_rel={t_rel} pattern_end={pend} "
            f"ok={t_rel >= 0.8 * pend if t_rel >= 0 and pend else False}"
        )
    print("thr", mid_s)


if __name__ == "__main__":
    main()

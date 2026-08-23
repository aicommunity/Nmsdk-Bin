#!/usr/bin/env python3
"""Verify Train Parameters after -S: Done + AutoCalibrate applied (not cold FixedLTZ)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

COLD_FIXED_LTZ = 0.0115


def read_tag(path: Path, tag: str) -> str | None:
    t = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", t)
    return m.group(1).strip() if m else None


def check_params(path: Path, *, require_calibrated: bool = False) -> dict:
    fails: list[str] = []
    warns: list[str] = []
    need = read_tag(path, "IsNeedToTrain")
    phase = read_tag(path, "TrainingPhase")
    L = read_tag(path, "DendriteLength") or ""
    flt_s = read_tag(path, "FixedLTZThreshold") or "0"
    cal_s = read_tag(path, "CalibratedFixedLTZThreshold")
    auto = read_tag(path, "AutoCalibrateFixedLTZThreshold")
    tip = read_tag(path, "TipSynapseResistance") or ""

    try:
        flt = float(flt_s)
    except ValueError:
        flt = float("nan")
        fails.append(f"FixedLTZThreshold unparseable: {flt_s!r}")
    try:
        cal = float(cal_s) if cal_s is not None else 0.0
    except ValueError:
        cal = 0.0
        warns.append(f"CalibratedFixedLTZThreshold unparseable: {cal_s!r}")

    if need != "0":
        fails.append(f"IsNeedToTrain={need!r} (want 0)")
    if phase is not None and phase != "2":
        fails.append(f"TrainingPhase={phase!r} (want 2)")
    if abs(flt - COLD_FIXED_LTZ) < 1e-9:
        fails.append(f"FixedLTZThreshold still cold default {COLD_FIXED_LTZ}")
    if L.strip() == "1 1 1 1":
        fails.append(f"DendriteLength still cold {L!r}")
    if require_calibrated or cal_s is not None:
        if cal <= 0 and abs(flt - COLD_FIXED_LTZ) < 1e-9:
            fails.append("CalibratedFixedLTZThreshold missing/<=0 with cold FixedLTZ")
        elif cal <= 0 and cal_s is None:
            warns.append("CalibratedFixedLTZThreshold tag absent")
        elif cal <= 0:
            if require_calibrated:
                fails.append(f"CalibratedFixedLTZThreshold={cal_s!r} <= 0")
            else:
                warns.append(f"CalibratedFixedLTZThreshold={cal_s!r} <= 0")
    if auto is not None and auto != "1":
        warns.append(f"AutoCalibrateFixedLTZThreshold={auto!r}")
    tip0 = tip.replace(",", ".").split()
    if tip0 and tip0[0] in ("86000000", "86000000.0"):
        warns.append("TipSynapseResistance tip0 still 86e6 (may be ok if train early)")

    ok = len(fails) == 0
    return {
        "path": str(path),
        "ok": ok,
        "fails": fails,
        "warns": warns,
        "IsNeedToTrain": need,
        "TrainingPhase": phase,
        "DendriteLength": L,
        "FixedLTZThreshold": flt_s,
        "CalibratedFixedLTZThreshold": cal_s,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("params", nargs="*", type=Path, help="Train Parameters_00.xml")
    ap.add_argument("--meta", type=Path, default=None)
    ap.add_argument("--grid", type=Path, default=None, help="Grid root with EXP_*/Train")
    ap.add_argument("--strict", action="store_true", help="Treat warns as fails")
    ap.add_argument("--require-calibrated", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    paths: list[Path] = list(args.params)
    if args.meta and args.grid:
        lines = args.meta.read_text(encoding="utf-8").strip().splitlines()[1:]
        for ln in lines:
            if not ln.strip():
                continue
            exp = ln.split("\t")[0]
            paths.append(args.grid / exp / "Train" / "Parameters_00.xml")

    if not paths:
        ap.error("provide Parameters paths or --meta + --grid")

    results = []
    exit_fail = False
    for p in paths:
        if not p.exists():
            r = {"path": str(p), "ok": False, "fails": ["missing file"], "warns": []}
        else:
            r = check_params(p, require_calibrated=args.require_calibrated)
            if args.strict and r["warns"]:
                r["fails"].extend(r["warns"])
                r["warns"] = []
                r["ok"] = False
        results.append(r)
        if not r["ok"]:
            exit_fail = True
        status = "OK" if r["ok"] else "FAIL"
        print(f"{status} {p}")
        print(f"  L={r.get('DendriteLength')} FixedLTZ={r.get('FixedLTZThreshold')} "
              f"NeedTrain={r.get('IsNeedToTrain')} Phase={r.get('TrainingPhase')}")
        for f in r.get("fails", []):
            print(f"  FAIL: {f}")
        for w in r.get("warns", []):
            print(f"  WARN: {w}")

    if args.json:
        print(json.dumps(results, indent=2))
    sys.exit(1 if exit_fail else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verify RegressionFull480 results against golden SelectivityPresynapticInhib margprops."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


def parse_acc(s: str) -> tuple[int, int]:
    if "/" not in s:
        return 0, 0
    a, b = s.split("/", 1)
    return int(a), int(b)


def read_tag(path: Path, tag: str) -> str | None:
    t = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", t)
    return m.group(1).strip() if m else None


def fires_pattern(rows: list[dict]) -> str:
    return "".join("1" if r.get("neuron_fired") == "1" else "0" for r in rows)


def classify_csv(rows: list[dict]) -> dict:
    if not rows:
        return {"acc": 0, "n": 0, "target_hit": 0, "fp": 0, "fires": ""}
    acc = sum(1 for r in rows if r.get("match") == "1")
    fp = sum(1 for r in rows[1:] if r.get("neuron_fired") == "1")
    t0 = rows[0]
    target_hit = int(
        t0.get("target_class") == "1"
        and t0.get("neuron_fired") == "1"
        and t0.get("match") == "1"
    )
    return {
        "acc": acc,
        "n": len(rows),
        "target_hit": target_hit,
        "fp": fp,
        "fires": fires_pattern(rows),
    }


def parse_L(s: str) -> list[int]:
    return [int(x) for x in s.split()]


def L_within_tol(actual: str, golden: str, tol: int = 2) -> bool:
    a = parse_L(actual)
    g = parse_L(golden)
    if len(a) != len(g):
        return False
    return all(abs(x - y) <= tol for x, y in zip(a, g))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--golden", type=Path, default=Path(__file__).resolve().parents[1].parent / "SelectivityPresynapticInhib")
    ap.add_argument("--meta", type=Path, default=None)
    args = ap.parse_args()
    root = args.root
    meta = args.meta or root / "grid_regression.tsv"
    lines = meta.read_text(encoding="utf-8").strip().splitlines()
    header = lines[0].split("\t")
    rows_meta = [dict(zip(header, ln.split("\t"))) for ln in lines[1:] if ln.strip()]

    golden_map = {
        "EXP00_baseline_margprops": {
            "acc": (5, 8),
            "fires": "10100101",
            "L": "49 41 25 1",
            "flt": 0.01281123537910517,
        },
        "EXP04_preinh_250_margprops": {
            "acc": (6, 8),
            "fires": "10001000",
            "L": "49 41 25 1",
            "flt": 0.030173643466603391,
        },
    }

    all_ok = True
    report: list[str] = ["# Regression verification", ""]

    for row in rows_meta:
        exp = row["exp"]
        golden_exp = row["golden_exp"]
        g = golden_map[golden_exp]
        train_p = root / "RegressionFull480" / exp / "Train" / "Parameters_00.xml"
        csv_p = root / "RegressionFull480" / exp / "Test" / "SelectivityLog" / "results.csv"
        issues: list[str] = []

        phase = read_tag(train_p, "TrainingPhase")
        need_train = read_tag(train_p, "IsNeedToTrain")
        if phase != "2" and need_train != "0":
            issues.append(f"train not Done (TrainingPhase={phase!r}, IsNeedToTrain={need_train!r})")

        L = read_tag(train_p, "DendriteLength") or ""
        if not L_within_tol(L, g["L"]):
            issues.append(f"L={L!r} vs golden {g['L']!r}")

        cal = read_tag(train_p, "CalibratedFixedLTZThreshold")
        try:
            cal_f = float(cal or "0")
        except ValueError:
            cal_f = 0.0
        flt_s = read_tag(train_p, "FixedLTZThreshold") or "0"
        try:
            flt = float(flt_s)
        except ValueError:
            flt = 0.0
        auto = read_tag(train_p, "AutoCalibrateFixedLTZThreshold") == "1"
        if auto and cal_f <= 0 and abs(flt - 0.0115) < 1e-9:
            issues.append(f"AutoCalibrate=1 but FixedLTZ still cold default {flt!r}")
        elif cal_f <= 0 and not auto and flt <= 0:
            issues.append(f"FixedLTZThreshold={flt!r} <= 0")
        if g["flt"] > 0 and abs(flt - g["flt"]) / g["flt"] > 0.20:
            issues.append(f"FixedLTZ={flt:.6g} vs golden {g['flt']:.6g} (>20%)")

        if csv_p.exists():
            with csv_p.open(encoding="utf-8") as f:
                csv_rows = list(csv.DictReader(f))
            q = classify_csv(csv_rows)
            if (q["acc"], q["n"]) != g["acc"]:
                issues.append(f"acc={q['acc']}/{q['n']} expected {g['acc'][0]}/{g['acc'][1]}")
            if q["target_hit"] != 1:
                issues.append("target_hit=0")
            if q["fires"] != g["fires"]:
                issues.append(f"fires={q['fires']} expected {g['fires']}")
        else:
            issues.append(f"missing {csv_p}")

        status = "PASS" if not issues else "FAIL"
        if issues:
            all_ok = False
        report.append(f"## {exp} ({golden_exp}) — **{status}**")
        report.append(f"- Train L: `{L}` | FixedLTZ: `{flt_s}` | Calibrated: `{cal}`")
        if csv_p.exists():
            report.append(f"- Test acc: {q['acc']}/{q['n']} fires `{q['fires']}` target_hit={q['target_hit']}")
        for iss in issues:
            report.append(f"- FAIL: {iss}")
        report.append("")

    out = root / "REGRESSION.md"
    out.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"Wrote {out}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()

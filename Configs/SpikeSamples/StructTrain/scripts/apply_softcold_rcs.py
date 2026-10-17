#!/usr/bin/env python3
"""Append SoftCold HEAD rows into EXPERIMENTS.md from posttune_verify RCS + latest run bundles."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "EXPERIMENTS.md"
RUNS = ROOT / "_repro" / "runs"

# case id -> (canonical name, protocol label)
CASE_META = {
    "br50_gen": ("EXP_br_span50_packA_gen_C1e9", "SoftCold+PostTune"),
    "br25_preinh": ("EXP_br_span25_packA_preinh_C1e9", "SoftCold+PostTune"),
    "br50_preinh": ("EXP_br_span50_packA_preinh_C1e9", "SoftCold+PostTune"),
    "br100_preinh": ("EXP_br_span100_packA_preinh_C1e9", "SoftCold+PostTune"),
    "br25_nextseg": ("EXP_br_span25_packA_nextseginh_C1e9", "SoftCold+PostTune"),
    "br50_nextseg": ("EXP_br_span50_packA_nextseginh_C1e9", "SoftCold+PostTune"),
    "br100_nextseg": ("EXP_br_span100_packA_nextseginh_C1e9", "SoftCold+PostTune"),
    "br480_tiprmin": ("EXP_br480_tiprmin", "SoftCold+PostTune"),
    "br480_nextseg": ("EXP_br480_nextseginh_tiprmin", "SoftCold+PostTune"),
    "br480_preinh": ("EXP_br480_preinh250_tiprmin", "SoftCold+PostTune"),
    "asym25_preinh": ("EXP_span25ms_packA_preinh", "SoftCold+PostTune"),
    "asym50_preinh": ("EXP_span50ms_packA_preinh", "SoftCold+PostTune"),
    "asym100_gen": ("EXP_span100ms_packA_gen", "SoftCold+PostTune"),
    "asym100_preinh": ("EXP_span100ms_packA_preinh", "SoftCold+PostTune"),
    "phase6_thr_only": ("Phase6/EXP_480_gen_thr_only", "SoftCold+PostTune"),
    "phase6_preinh250": ("Phase6/EXP_480_preinh250_tiprmin", "SoftCold+PostTune"),
    "phase6_ltzcal_twin": ("Phase6/EXP_480_ltzcal_twin_gen", "SoftCold+PostTune"),
    "fs25_gen": ("EXP_span25ms_fast_C1e9", "SoftCold+PostTune"),
    "fs25_preinh": ("EXP_span25ms_fast_preinh_C1e9", "SoftCold+PostTune"),
    "fs50_preinh": ("EXP_span50ms_fast_preinh_C1e9", "SoftCold+PostTune"),
    "fs100_gen": ("EXP_span100ms_fast_C1e9", "SoftCold+PostTune"),
    "fs100_preinh": ("EXP_span100ms_fast_preinh_C1e9", "SoftCold+PostTune"),
    "ltz25_gen": ("LtzCal/EXP_span25ms_packA_gen", "SoftCold+PostTune"),
    "ltz25_preinh": ("LtzCal/EXP_span25ms_packA_preinh", "SoftCold+PostTune"),
    "ltz50_gen": ("LtzCal/EXP_span50ms_packA_gen", "SoftCold+PostTune"),
    "ltz50_preinh": ("LtzCal/EXP_span50ms_packA_preinh", "SoftCold+PostTune"),
    "ltz100_gen": ("LtzCal/EXP_span100ms_packA_gen", "SoftCold+PostTune"),
    "ltz100_preinh": ("LtzCal/EXP_span100ms_packA_preinh", "SoftCold+PostTune"),
    "pa00_baseline": ("EXP00_baseline", "SoftCold+PostTune"),
    "pa01_ltz_sweep": ("EXP01_ltz_threshold_sweep", "SoftCold+PostTune"),
    "pa02_ltzone_avg": ("EXP02_ltzone_average_mode", "SoftCold+PostTune"),
    "pa06_ltzone_int": ("EXP06_ltzone_integration", "SoftCold+PostTune"),
    "tn_classic": ("TimeNeuronTimeLearner", "SoftCold+PostTune"),
    "psi01_050": ("EXP01_preinh_050", "SoftCold+PostTune"),
    "psi14_260": ("EXP14_preinh_260", "SoftCold+PostTune"),
    "psi15_270": ("EXP15_preinh_270", "SoftCold+PostTune"),
    "psi21_100": ("EXP21_span100ms_preinh250", "SoftCold+PostTune"),
    "psi31_200": ("EXP31_span200ms_preinh250", "SoftCold+PostTune"),
    "psi32_300": ("EXP32_span300ms_baseline", "SoftCold+PostTune"),
    "psi33_300": ("EXP33_span300ms_preinh250", "SoftCold+PostTune"),
    "psi34_400": ("EXP34_span400ms_baseline", "SoftCold+PostTune"),
    "psi35_400": ("EXP35_span400ms_preinh250", "SoftCold+PostTune"),
}


def latest_bundle(case: str) -> Path | None:
    cands = sorted(RUNS.glob(f"{case}_*_work"), reverse=True)
    # prefer non-work provenance dir
    bundles = sorted([p for p in RUNS.glob(f"{case}_*") if p.is_dir() and not p.name.endswith("_work")], reverse=True)
    if bundles:
        return bundles[0]
    return cands[0] if cands else None


def row_for(case: str, rc: int) -> str | None:
    meta = CASE_META.get(case)
    if not meta:
        return None
    name, protocol = meta
    head = "PASS" if rc == 0 else "FAIL"
    bundle = latest_bundle(case)
    note = f"SoftCold case=`{case}` rc={rc}"
    if bundle:
        note += f"; bundle=`_repro/runs/{bundle.name}`"
    # Acc unknown here — leave — unless metrics in POSTTUNE result
    return (
        f"| {name} | — | SoftCold wave C | {protocol} | — | — | — | **{head}** | — | {note} | "
        f"`posttune_verify --case {case}` |"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rcs", type=Path, required=True)
    args = ap.parse_args()
    if not args.rcs.exists():
        print("missing rcs")
        return 1
    lines_to_add: list[str] = []
    for line in args.rcs.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) != 2:
            continue
        case, rc_s = parts
        try:
            rc = int(rc_s)
        except ValueError:
            continue
        row = row_for(case, rc)
        if row:
            lines_to_add.append(row)
    if not lines_to_add:
        print("no rows")
        return 0
    text = EXP.read_text(encoding="utf-8")
    marker = "\n## SoftCold wave C (auto)\n"
    block = marker + "\n".join([
        "",
        "| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |",
        "|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|",
        *lines_to_add,
        "",
    ])
    if "## SoftCold wave C (auto)" in text:
        text = re.sub(r"\n## SoftCold wave C \(auto\)\n.*?(?=\n## |\Z)", "", text, count=1, flags=re.S)
    # insert before OUT section
    if "\n## Вне строк" in text:
        text = text.replace("\n## Вне строк", block + "\n## Вне строк", 1)
    else:
        text = text.rstrip() + "\n" + block
    EXP.write_text(text, encoding="utf-8")
    print(f"appended SoftCold rows={len(lines_to_add)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Apply SoftCold RCS lines into EXPERIMENTS/SUCCESSFUL LastCheck (+ Working if PASS)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "EXPERIMENTS.md"
SUC = ROOT / "SUCCESSFUL_EXPERIMENTS.md"

# case -> registry Имя (canonical EXP folder / alias)
CASE_TO_NAME = {
    "br25_on": "EXP_br_span25_packA_gen_C1e9",
    "br25_off": "EXP_br_span25_packA_gen_C1e9",
    "asym25": "EXP_span25ms_packA_gen",
    "asym50": "EXP_span50ms_packA_gen",
    "br100_keep": "EXP_br_span100_packA_gen_C1e9",
    "br100_search": "EXP_br_span100_packA_gen_C1e9",
    "phase6_480": "Phase6/EXP_480_gen_tiprmin",
    "br50_gen": "EXP_br_span50_packA_gen_C1e9",
    "br25_preinh": "EXP_br_span25_packA_preinh_C1e9",
    "br50_preinh": "EXP_br_span50_packA_preinh_C1e9",
    "br100_preinh": "EXP_br_span100_packA_preinh_C1e9",
    "br25_nextseg": "EXP_br_span25_packA_nextseginh_C1e9",
    "br50_nextseg": "EXP_br_span50_packA_nextseginh_C1e9",
    "br100_nextseg": "EXP_br_span100_packA_nextseginh_C1e9",
    "br480_tiprmin": "EXP_br480_tiprmin",
    "br480_nextseg": "EXP_br480_nextseginh_tiprmin",
    "br480_preinh": "EXP_br480_preinh250_tiprmin",
    "asym25_preinh": "EXP_span25ms_packA_preinh",
    "asym50_preinh": "EXP_span50ms_packA_preinh",
    "asym100_gen": "EXP_span100ms_packA_gen",
    "asym100_preinh": "EXP_span100ms_packA_preinh",
    "phase6_thr_only": "Phase6/EXP_480_gen_thr_only",
    "phase6_preinh250": "Phase6/EXP_480_preinh250_tiprmin",
    "phase6_ltzcal_twin": "Phase6/EXP_480_ltzcal_twin_gen",
    "fs25_gen": "EXP_span25ms_fast_C1e9",
    "fs25_preinh": "EXP_span25ms_fast_preinh_C1e9",
    "fs50_preinh": "EXP_span50ms_fast_preinh_C1e9",
    "fs100_gen": "EXP_span100ms_fast_C1e9",
    "fs100_preinh": "EXP_span100ms_fast_preinh_C1e9",
    "ltz25_gen": "EXP_span25ms_packA_gen",
    "ltz25_preinh": "EXP_span25ms_packA_preinh",
    "ltz50_gen": "EXP_span50ms_packA_gen",
    "ltz50_preinh": "EXP_span50ms_packA_preinh",
    "ltz100_gen": "EXP_span100ms_packA_gen",
    "ltz100_preinh": "EXP_span100ms_packA_preinh",
    "pa00_baseline": "EXP00_baseline",
    "pa01_ltz_sweep": "EXP01_ltz_threshold_sweep",
    "pa02_ltzone_avg": "EXP02_ltzone_average_mode",
    "pa06_ltzone_int": "EXP06_ltzone_integration",
    "tn_classic": "TimeNeuronTimeLearner",
    "psi01_050": "EXP01_preinh_050",
    "psi14_260": "EXP14_preinh_260",
    "psi15_270": "EXP15_preinh_270",
    "psi21_100": "EXP21_span100ms_preinh250",
    "psi31_200": "EXP31_span200ms_preinh250",
    "psi32_300": "EXP32_span300ms_baseline",
    "psi33_300": "EXP33_span300ms_preinh250",
    "psi34_400": "EXP34_span400ms_baseline",
    "psi35_400": "EXP35_span400ms_preinh250",
}

RANK = {
    "SoftCold": 5,
    "SoftColdOff": 4,
    "SkipTrainGold": 3,
    "GoldTest": 2,
    "MatrixClone": 2,
    "none": 0,
}


def parse_rcs(path: Path) -> list[tuple[str, int]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            out.append((parts[0], int(parts[1])))
        except ValueError:
            continue
    return out


def row_matches_softcold_case(cols: list[str], case: str, *, pass_: bool) -> bool:
    """Do not rewrite every row with the same Имя — only SoftCold-related rows."""
    if len(cols) < 5:
        return False
    conf = cols[-1] if len(cols) > 10 else ""
    lc = cols[4]
    params = cols[2]
    if f"--case {case}" in conf or f"case={case}" in conf or f"case={case}" in lc:
        return True
    # SoftColdOff / off clone
    if case.endswith("_off") and ("posttune_off" in conf or "EnablePostTrainTuning=0" in params):
        return True
    if cols[1].strip() == "—" and (case in conf or f"--case {case}" in conf):
        return True
    if case == "br25_on" and "CanonRmin" in params and "soft-cold" in params:
        return True
    if case == "br25_off" and ("posttune_off" in conf or "PostTuneTuning=0" in params):
        return True
    if case == "br100_keep" and ("KeepDone" in params or "posttune_keep" in conf):
        return True
    if case == "br100_search" and ("SearchSynthetic" in params or "posttune_search" in conf):
        return True
    if pass_ and "posttune" not in conf.lower() and "packA" in params:
        if case.startswith(("asym", "ltz", "fs")) and "/Train)" in conf:
            return True
        if case.startswith("br") and "EXP_br" in conf and "posttune" in conf:
            return "posttune" in conf and case.replace("_", "") in conf.replace("_", "")
    # PhaseA / PSI / TimeNeuron / FastSpan: unique Имя → primary Selectivity* row
    if case.startswith(("pa", "psi")) or case == "tn_classic":
        if any(
            p in conf
            for p in (
                "SelectivityPhaseA/",
                "SelectivityPresynapticInhib/",
                "TimeNeuronTimeLearner/",
            )
        ):
            return True
    if case.startswith("fs") and "SelectivityFastSpan/" in conf:
        return True
    return False


def patch_table(text: str, name: str, lastcheck: str, *, pass_: bool, case: str) -> str:
    lines = text.splitlines()
    out = []
    name_rows: list[int] = []
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            out.append(line)
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if not cols or cols[0] != name:
            out.append(line)
            continue
        if len(cols) < 5 or cols[3] not in RANK:
            out.append(line)
            continue
        if not row_matches_softcold_case(cols, case, pass_=pass_):
            out.append(line)
            continue
        name_rows.append(i)
        working = cols[3]
        if pass_ and RANK.get("SoftCold", 0) > RANK.get(working, 0):
            cols[3] = "SoftCold"
        cols[4] = lastcheck
        if pass_:
            cols[8] = "PASS" if len(cols) > 8 else cols[8]
        else:
            # SoftCold FAIL does not demote Gold Working; HEAD on this SoftCold row = FAIL
            if "SoftCold" in lastcheck:
                cols[8] = "FAIL" if len(cols) > 8 else cols[8]
        out.append("| " + " | ".join(cols) + " |")
    if not name_rows:
        # append note line under a softcold section is too risky; skip
        print(f"WARN: name not found in table: {name}", file=sys.stderr)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rcs", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    rows = parse_rcs(args.rcs)
    exp = EXP.read_text(encoding="utf-8")
    suc = SUC.read_text(encoding="utf-8") if SUC.exists() else ""
    for case, rc in rows:
        name = CASE_TO_NAME.get(case, case)
        if rc == 0:
            lc = f"SoftCold PASS (case={case})"
            pass_ = True
        else:
            lc = f"SoftCold FAIL (case={case}, rc={rc})"
            pass_ = False
        print(f"{case} -> {name}: {lc}")
        exp = patch_table(exp, name, lc, pass_=pass_, case=case)
        if pass_ and suc:
            suc = patch_table(suc, name, lc, pass_=True, case=case)
    if args.dry_run:
        return
    EXP.write_text(exp, encoding="utf-8")
    if suc:
        SUC.write_text(suc, encoding="utf-8")
    print("updated", EXP, SUC if suc else "")


if __name__ == "__main__":
    main()

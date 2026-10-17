#!/usr/bin/env python3
"""Apply SoftCold RCS into EXPERIMENTS/SUCCESSFUL SoftCold columns (+ Working if PASS).

Schema (post migrate_experiments_softcold_columns.py):
  Имя | Алгоритм | Параметры | Working | Acc | Цель | SoftCold | SoftColdDetail | HEAD | …
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "EXPERIMENTS.md"
SUC = ROOT / "SUCCESSFUL_EXPERIMENTS.md"
LOCK = ROOT / "_repro" / "registry_apply.lock"
RUNS = ROOT / "_repro" / "runs"

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
    "ltz25_gen": "LtzCal/EXP_span25ms_packA_gen",
    "ltz25_preinh": "LtzCal/EXP_span25ms_packA_preinh",
    "ltz50_gen": "LtzCal/EXP_span50ms_packA_gen",
    "ltz50_preinh": "LtzCal/EXP_span50ms_packA_preinh",
    "ltz100_gen": "LtzCal/EXP_span100ms_packA_gen",
    "ltz100_preinh": "LtzCal/EXP_span100ms_packA_preinh",
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

BUCKET = {
    "ok": "PASS",
    "gate_fail": "N",
    "train_incomplete": "D",
    "tipr_mismatch": "A",
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


def case_dirs(case: str) -> list[Path]:
    return sorted(
        [p for p in RUNS.glob(f"{case}_*") if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def latest_prov(case: str) -> dict:
    for p in case_dirs(case):
        if p.name.endswith("_work"):
            continue
        pj = p / "provenance.json"
        if pj.exists():
            try:
                return json.loads(pj.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
    return {}


def find_results_csv(case: str) -> Path | None:
    for p in case_dirs(case):
        for rel in (
            Path("Test/results.csv"),
            Path("Test/SelectivityLog/results.csv"),
            Path("results.csv"),
        ):
            cand = p / rel
            if cand.exists():
                return cand
        for cand in p.glob("**/results.csv"):
            return cand
    return None


def acc_fires_from_csv(path: Path | None) -> tuple[str, str]:
    """Return (acc like '8/8', fires like '10000000') or ('?', '?')."""
    if path is None or not path.exists():
        return "?", "?"
    try:
        with path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except OSError:
        return "?", "?"
    if not rows:
        return "?", "?"
    n = len(rows)
    ok = 0
    fires = []
    for r in rows:
        m = r.get("match", "")
        try:
            ok += int(float(m))
        except (TypeError, ValueError):
            pass
        nf = r.get("neuron_fired", "0")
        try:
            fires.append("1" if int(float(nf)) else "0")
        except (TypeError, ValueError):
            fires.append("?")
    return f"{ok}/{n}", "".join(fires)


def detail_for(case: str, rc: int) -> str:
    prov = latest_prov(case)
    tipr = prov.get("tipr_class", "?")
    fc = prov.get("failure_class", "?")
    train = prov.get("train_status", "?")
    gate_rc = prov.get("gate_rc", "?")
    notes = prov.get("fail_notes") or []
    notes_s = ",".join(str(x) for x in notes[:4]) if isinstance(notes, list) else str(notes)
    need = prov.get("Need", prov.get("need", "?"))
    acc, fires = acc_fires_from_csv(find_results_csv(case))
    bucket = "PASS" if rc == 0 else BUCKET.get(str(fc), "?")
    base = (
        f"case={case}; tipr={tipr}; fc={fc}; train={train}; "
        f"acc={acc}; fires={fires}; Need={need}; bucket={bucket}"
    )
    if rc == 0:
        return base
    return f"{base}; gate_rc={gate_rc}; notes={notes_s}"


def is_data_row(cols: list[str]) -> bool:
    return len(cols) >= 9 and cols[3] in RANK and cols[6] in ("PASS", "FAIL", "—")


def patch_table_new(
    text: str,
    name: str,
    *,
    pass_: bool,
    case: str,
    detail: str,
    softcold_pass_for_name: bool | None,
) -> str:
    """Update SoftCold/SoftColdDetail on every data row with this Имя.

    softcold_pass_for_name: True if any Canon SoftCold (non-_off) case for this
    name is PASS; False if primary SoftCold FAIL; None if unknown / only _off.
    """
    lines = text.splitlines()
    out = []
    n = 0
    verdict = "PASS" if pass_ else "FAIL"
    for line in lines:
        if not line.startswith("|"):
            out.append(line)
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if not cols or cols[0] != name or not is_data_row(cols):
            out.append(line)
            continue
        n += 1
        working = cols[3]

        if case.endswith("_off"):
            # SoftColdOff must not overwrite Canon SoftCold FAIL primary
            if cols[6] != "FAIL":
                cols[6] = verdict
                cols[7] = detail
            else:
                tag = f"{case}:PASS" if pass_ else f"{case}:FAIL"
                if tag not in cols[7]:
                    cols[7] = cols[7] + f"; {tag}"
            if pass_ and RANK.get("SoftColdOff", 0) > RANK.get(working, 0):
                cols[3] = "SoftColdOff"
            # Canon SoftCold FAIL but SoftColdOff PASS: demote false SoftCold Working
            if softcold_pass_for_name is False and cols[3] == "SoftCold":
                cols[3] = "SoftColdOff"
        else:
            cols[6] = verdict
            cols[7] = detail
            if pass_ and RANK.get("SoftCold", 0) > RANK.get(working, 0):
                cols[3] = "SoftCold"
            elif not pass_ and cols[3] == "SoftCold":
                # Canon SoftCold FAIL: drop SoftCold Working (SoftColdOff may restore)
                cols[3] = "GoldTest" if RANK.get(working, 0) <= 5 else working
                # Prefer SoftColdOff if already noted, else GoldTest as safe floor
                if "SoftColdOff" in line or "_off:PASS" in cols[7]:
                    cols[3] = "SoftColdOff"
                elif working == "SoftCold":
                    # keep Acc as-is (may be SoftColdOff metrics); Working demoted
                    cols[3] = "GoldTest"

        out.append("| " + " | ".join(cols) + " |")
    if not n:
        print(f"WARN: name not found in new-schema table: {name}", file=sys.stderr)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rcs", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+", encoding="utf-8") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        try:
            rows = parse_rcs(args.rcs)
            exp = EXP.read_text(encoding="utf-8")
            suc = SUC.read_text(encoding="utf-8") if SUC.exists() else ""
            if "| SoftCold | SoftColdDetail |" not in exp:
                print(
                    "ERROR: EXPERIMENTS.md not migrated; run "
                    "scripts/migrate_experiments_softcold_columns.py first",
                    file=sys.stderr,
                )
                sys.exit(2)

            # Per-name: does any non-_off SoftCold case PASS?
            name_soft_pass: dict[str, bool] = {}
            for case, rc in rows:
                if case.endswith("_off"):
                    continue
                name = CASE_TO_NAME.get(case, case)
                if rc == 0:
                    name_soft_pass[name] = True
                else:
                    name_soft_pass.setdefault(name, False)

            # FAIL first, then PASS (primary FAIL not overwritten by SoftColdOff PASS)
            ordered = sorted(rows, key=lambda t: (0 if t[1] != 0 else 1, t[0]))
            for case, rc in ordered:
                name = CASE_TO_NAME.get(case, case)
                pass_ = rc == 0
                detail = detail_for(case, rc)
                print(f"{case} -> {name}: SoftCold={'PASS' if pass_ else 'FAIL'}")
                flag = name_soft_pass.get(name)
                exp = patch_table_new(
                    exp,
                    name,
                    pass_=pass_,
                    case=case,
                    detail=detail,
                    softcold_pass_for_name=flag,
                )
                if suc:
                    suc = patch_table_new(
                        suc,
                        name,
                        pass_=pass_,
                        case=case,
                        detail=detail,
                        softcold_pass_for_name=flag,
                    )
            if args.dry_run:
                return
            EXP.write_text(exp, encoding="utf-8")
            if suc:
                SUC.write_text(suc, encoding="utf-8")
            print("updated", EXP, SUC if suc else "")
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


if __name__ == "__main__":
    main()

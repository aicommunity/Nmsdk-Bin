#!/usr/bin/env python3
"""Structural inventory/audit for StructTrain TimeNeuron/selectivity experiments."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_TOP = {"XOR", "SpikeAnsTrainer", "SpikeTrainer", "RTlibs"}


def iter_campaign_dirs() -> list[Path]:
    out = []
    for p in sorted(ROOT.iterdir()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        if p.name in EXCLUDE_TOP:
            continue
        if p.name.startswith("Selectivity") or p.name.startswith("TimeNeuron"):
            out.append(p)
    return out


def find_exp_roots(campaign: Path) -> list[Path]:
    """Return experiment roots that should have Train/ and Test/."""
    roots: list[Path] = []
    # Direct TimeNeuron experiment roots
    if campaign.name.startswith("TimeNeuron"):
        if (campaign / "Train").is_dir() or (campaign / "Project.ini").exists():
            roots.append(campaign)
        return roots

    # Selectivity*: EXP* under campaign or one level of subcampaign
    for exp in sorted(campaign.rglob("EXP*")):
        if not exp.is_dir():
            continue
        if ".statistic" in str(exp):
            continue
        # EXP leaf = has Train or Test or Project.ini
        if (exp / "Train").is_dir() or (exp / "Test").is_dir() or (exp / "Project.ini").exists():
            # skip nested under Train/Test
            if "Train" in exp.parts or "Test" in exp.parts:
                continue
            if any(part.startswith("Test_") for part in exp.parts):
                continue
            roots.append(exp)
    return roots


def read_text(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def check_exp(exp: Path) -> dict[str, str]:
    train = exp / "Train"
    test = exp / "Test"
    fails: list[str] = []
    notes: list[str] = []

    if not train.is_dir():
        fails.append("no_Train")
    if not test.is_dir():
        fails.append("no_Test")

    train_model = train / "Model_00.xml"
    test_model = test / "Model_00.xml"
    train_params = train / "Parameters_00.xml"
    test_params = test / "Parameters_00.xml"

    has_learner = False
    if train_model.exists():
        tm = read_text(train_model)
        has_learner = bool(
            re.search(r"NeuronTimeLearner|NNeuronTimeLearner", tm)
        )
        if not has_learner:
            fails.append("train_no_TimeLearner")
        if "LTZone" not in tm and "ltzone" not in tm.lower():
            notes.append("train_no_LTZone_string")
    elif train.is_dir():
        fails.append("train_no_Model")

    if test_model.exists():
        te = read_text(test_model)
        if "PatternResponseAnalyzer" not in te and "NPatternResponseAnalyzer" not in te:
            fails.append("test_no_analyzer")
    elif test.is_dir():
        fails.append("test_no_Model")

    if train_params.exists():
        tp = read_text(train_params)
        if re.search(r"<NeuronClassName[^>]*>\s*</NeuronClassName>", tp):
            fails.append("empty_NeuronClassName")
        if re.search(r'<Enable[^>]*>0</Enable>', tp) and "Neuron" in tp:
            notes.append("Enable0_in_params")

    csv_path = test / "SelectivityLog" / "results.csv"
    n_trials = ""
    if not csv_path.exists():
        fails.append("no_results_csv")
    else:
        try:
            lines = [ln for ln in csv_path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
            n = max(0, len(lines) - 1)
            n_trials = str(n)
            if n != 8:
                fails.append(f"csv_n={n}")
        except OSError:
            fails.append("csv_unreadable")

    status = "FAIL" if fails else "PASS"
    return {
        "campaign": str(exp.relative_to(ROOT).parts[0]),
        "exp": str(exp.relative_to(ROOT)),
        "status": status,
        "fails": ";".join(fails),
        "notes": ";".join(notes),
        "n_trials": n_trials,
        "has_train": "1" if train.is_dir() else "0",
        "has_test": "1" if test.is_dir() else "0",
        "has_learner": "1" if has_learner else "0",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    day = date.today().isoformat()
    out = args.out or (ROOT / f"AUDIT_STRUCTURE_{day}.csv")

    rows = []
    for camp in iter_campaign_dirs():
        for exp in find_exp_roots(camp):
            rows.append(check_exp(exp))

    fields = ["campaign", "exp", "status", "fails", "notes", "n_trials", "has_train", "has_test", "has_learner"]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    n_fail = sum(1 for r in rows if r["status"] == "FAIL")
    findings = ROOT / "AUDIT_FINDINGS.md"
    findings.write_text(
        f"# StructTrain structural audit ({day})\n\n"
        f"- Experiments scanned: **{len(rows)}**\n"
        f"- FAIL: **{n_fail}**\n"
        f"- CSV: `{out.name}`\n\n"
        f"## FAIL sample\n\n"
        + "\n".join(
            f"- `{r['exp']}`: {r['fails']}" for r in rows if r["status"] == "FAIL"
        )[:8000]
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out} rows={len(rows)} fail={n_fail}")
    print(f"wrote {findings}")


if __name__ == "__main__":
    main()

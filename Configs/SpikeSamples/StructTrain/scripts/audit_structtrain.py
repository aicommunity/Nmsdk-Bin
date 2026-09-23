#!/usr/bin/env python3
"""Structural inventory/audit for StructTrain TimeNeuron/selectivity experiments.

Also builds AUDIT_MATRIX (trainer/recipe/gate/last-pulse/orphan) and optional GATE rebuild.
Does not change selectivity_metrics ok_audit thresholds.
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_TOP = {"XOR", "SpikeAnsTrainer", "SpikeTrainer", "RTlibs"}
sys.path.insert(0, str(ROOT / "scripts"))
from selectivity_metrics import classify  # noqa: E402


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
    if campaign.name.startswith("TimeNeuron"):
        if (campaign / "Train").is_dir() or (campaign / "Project.ini").exists():
            roots.append(campaign)
        return roots

    for exp in sorted(campaign.rglob("EXP*")):
        if not exp.is_dir():
            continue
        if ".statistic" in str(exp):
            continue
        if (exp / "Train").is_dir() or (exp / "Test").is_dir() or (exp / "Project.ini").exists():
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


def get_tag(text: str, tag: str) -> str | None:
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)
    return m.group(1).strip() if m else None


def detect_trainer(exp: Path) -> str:
    for rel in ("Train/ALGORITHM.md", "Test/ALGORITHM.md", "ALGORITHM.md"):
        p = exp / rel
        if p.exists():
            t = read_text(p, limit=50_000)
            if "NNeuronTimeLearnerBranch" in t or "NeuronTimeLearnerBranch" in t:
                return "Branch"
            if "NNeuronTimeLearner" in t or "NeuronTimeLearner" in t:
                return "TimeLearner"
    rel = str(exp.relative_to(ROOT))
    if "Branch" in rel or rel.startswith("TimeNeuronTimeLearnerBranch"):
        return "Branch"
    return "TimeLearner"


def mid_metric_for(exp: Path, trainer: str) -> str:
    rel = str(exp.relative_to(ROOT))
    if trainer == "Branch" or "SelectivityBranch" in rel or "Branch" in rel.split("/"):
        return "soma_amp_sum"
    return "ltz_potential_max"


def recipe_flags(test_params: Path) -> tuple[str, str]:
    if not test_params.exists():
        return "0", "0"
    t = read_text(test_params)
    tip = get_tag(t, "TipSynapseResistance") or ""
    rmin = get_tag(t, "ResistanceMin") or ""
    neur = get_tag(t, "NeuronClassName") or ""
    vals = tip.replace(",", " ").split()
    tiprmin = "0"
    if len(vals) >= 4 and all(v.startswith("20000000") for v in vals[:3]):
        if rmin.startswith("20000000"):
            tiprmin = "1"
    c1e9 = "1" if ("AsymRmD001C1e9" in neur or "Preinh2_5AsymRm" in neur) else "0"
    return tiprmin, c1e9


def last_pulse_ok(rows: list[dict[str, str]], *, dt_tol: float = 1e-9) -> str:
    """Target spike at/after last stim (sum of ISI), with discretization tolerance."""
    if not rows:
        return "0"
    r0 = rows[0]
    try:
        trel = float(r0.get("neuron_t_rel") or -1)
    except ValueError:
        return "0"
    isis = []
    for k in ("isi0", "isi1", "isi2", "isi3"):
        v = r0.get(k)
        if v is None or v == "":
            continue
        try:
            isis.append(float(v))
        except ValueError:
            pass
    if not isis or trel < 0:
        return "0"
    last_stim = sum(isis)
    return "1" if last_stim > 0 and trel + dt_tol >= last_stim else "0"


def last_pulse_ok_legacy(rows: list[dict[str, str]]) -> str:
    """Historical 0.8*max(ISI) rule (A06 legacy)."""
    if not rows:
        return "0"
    r0 = rows[0]
    try:
        trel = float(r0.get("neuron_t_rel") or -1)
    except ValueError:
        return "0"
    isis = []
    for k in ("isi0", "isi1", "isi2", "isi3"):
        v = r0.get(k)
        if v is None or v == "":
            continue
        try:
            isis.append(float(v))
        except ValueError:
            pass
    if not isis or trel < 0:
        return "0"
    pend = max(isis)
    return "1" if pend > 0 and trel >= 0.8 * pend else "0"


def orphan_class(
    exp: Path,
    *,
    tiprmin: str,
    c1e9: str,
    ok_audit: str,
    acc: str,
    structural_fails: str,
) -> str:
    rel = str(exp.relative_to(ROOT))
    name = exp.name
    if rel.startswith("TimeNeuronTimeLearnerBranch"):
        return "legacy_demoted"
    if "AsymRmLtzCalBranch" in rel:
        return "stall"
    if any(x in name for x in ("Dspan", "ampaudit", "_smoke")) or "RegressionFull480" in rel:
        return "diag"
    if any(x in name for x in ("phase9", "phase10", "phase11")):
        return "fail_probe"
    if tiprmin == "1" and c1e9 == "1" and ok_audit == "1":
        try:
            if int(acc) < 8:
                return "partial"
        except ValueError:
            pass
        return "covered"
    if tiprmin == "1" and ok_audit == "1":
        try:
            if int(acc) < 8:
                return "partial"
        except ValueError:
            return "partial"
        return "covered"
    if "no_results_csv" in structural_fails or "csv_n=" in structural_fails:
        return "orphan"
    return "orphan"


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
        has_learner = bool(re.search(r"NeuronTimeLearner|NNeuronTimeLearner", tm))
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
        if re.search(r"<Enable[^>]*>0</Enable>", tp) and "Neuron" in tp:
            notes.append("Enable0_in_params")

    csv_path = test / "SelectivityLog" / "results.csv"
    n_trials = ""
    rows_csv: list[dict[str, str]] = []
    if not csv_path.exists():
        fails.append("no_results_csv")
    else:
        try:
            rows_csv = list(csv.DictReader(csv_path.open(encoding="utf-8")))
            n = len(rows_csv)
            n_trials = str(n)
            if n != 8:
                fails.append(f"csv_n={n}")
        except OSError:
            fails.append("csv_unreadable")

    status = "FAIL" if fails else "PASS"
    trainer = detect_trainer(exp)
    tiprmin, c1e9 = recipe_flags(test_params)
    mid = mid_metric_for(exp, trainer)

    gate: dict[str, Any] = {}
    if rows_csv:
        gate = classify(rows_csv)

    ok_audit = str(int(gate.get("ok_audit", 0)))
    acc = str(gate.get("acc_strict", gate.get("acc", "")))
    mode = str(gate.get("mode_legacy", gate.get("mode", "")))
    rq = str(gate.get("response_quality", ""))
    gate_n = str(gate.get("n", n_trials or "0"))
    lp = last_pulse_ok(rows_csv) if rows_csv else "0"
    structural = ";".join(fails)
    oclass = orphan_class(
        exp,
        tiprmin=tiprmin,
        c1e9=c1e9,
        ok_audit=ok_audit,
        acc=acc or "0",
        structural_fails=structural,
    )

    return {
        "campaign": str(exp.relative_to(ROOT).parts[0]),
        "exp": str(exp.relative_to(ROOT)),
        "status": status,
        "fails": structural,
        "notes": ";".join(notes),
        "n_trials": n_trials,
        "has_train": "1" if train.is_dir() else "0",
        "has_test": "1" if test.is_dir() else "0",
        "has_learner": "1" if has_learner else "0",
        "trainer": trainer,
        "mid_metric": mid,
        "recipe_tiprmin": tiprmin,
        "recipe_c1e9_neuron": c1e9,
        "gate_n": gate_n,
        "ok_audit": ok_audit,
        "acc_strict": acc,
        "mode": mode,
        "response_quality": rq,
        "last_pulse_ok": lp,
        "csv_complete": "1" if n_trials == "8" else "0",
        "structural_fails": structural,
        "orphan_class": oclass,
        "csv_rel": str((csv_path.relative_to(ROOT)).as_posix()) if csv_path.exists() else "",
    }


def collect_gate_rows() -> list[dict[str, str]]:
    """Rebuild GATE rows from all Test SelectivityLog CSVs under campaign roots."""
    paths: list[Path] = []
    for camp in iter_campaign_dirs():
        for p in camp.rglob("Test/SelectivityLog/results.csv"):
            if any(part.startswith("Test_") for part in p.parts):
                continue
            paths.append(p)
    paths = sorted(set(paths))
    out: list[dict[str, str]] = []
    for p in paths:
        try:
            rows = list(csv.DictReader(p.open(encoding="utf-8")))
        except OSError:
            continue
        m = classify(rows)
        exp = str(p.parent.parent.relative_to(ROOT))
        out.append(
            {
                "exp": exp,
                "n": str(m.get("n", len(rows))),
                "ok_legacy": str(int(m.get("ok", m.get("ok_legacy", 0)))),
                "ok_strict": str(int(m.get("ok_strict", 0))),
                "ok_audit": str(int(m.get("ok_audit", 0))),
                "acc_legacy": str(m.get("acc", m.get("acc_legacy", 0))),
                "acc_strict": str(m.get("acc_strict", 0)),
                "fire_all_legacy": str(int(m.get("fire_all", m.get("fire_all_legacy", 0)))),
                "fire_all_strict": str(int(m.get("fire_all_strict", 0))),
                "late_fp": str(m.get("late_fp", 0)),
                "late_fn": str(m.get("late_fn", 0)),
                "response_quality": str(m.get("response_quality", "")),
                "n_burst": str(m.get("n_burst_trials", m.get("n_burst", 0))),
                "n_per_stim": str(m.get("n_per_stim_trials", m.get("n_per_stim", 0))),
                "max_spikes": str(m.get("max_spike_count", m.get("max_spikes", 0))),
                "mode_legacy": str(m.get("mode", m.get("mode_legacy", ""))),
                "csv": str(p.relative_to(ROOT).as_posix()),
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=None, help="AUDIT_STRUCTURE csv path")
    ap.add_argument("--out-matrix", type=Path, default=None, help="AUDIT_MATRIX csv path")
    ap.add_argument("--rebuild-gate", action="store_true", help="Rewrite AUDIT_GATE_RECOMPUTE.csv")
    ap.add_argument(
        "--archive-stamp",
        default="",
        help="UTC stamp for GATE archive filename (default now)",
    )
    args = ap.parse_args()
    day = date.today().isoformat()
    out = args.out or (ROOT / f"AUDIT_STRUCTURE_{day}.csv")
    stamp = args.archive_stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    matrix_out = args.out_matrix or (ROOT / f"AUDIT_MATRIX_{day.replace('-', '')}.csv")

    rows = []
    for camp in iter_campaign_dirs():
        for exp in find_exp_roots(camp):
            rows.append(check_exp(exp))

    struct_fields = [
        "campaign",
        "exp",
        "status",
        "fails",
        "notes",
        "n_trials",
        "has_train",
        "has_test",
        "has_learner",
    ]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=struct_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    matrix_fields = [
        "campaign",
        "exp",
        "trainer",
        "mid_metric",
        "recipe_tiprmin",
        "recipe_c1e9_neuron",
        "gate_n",
        "ok_audit",
        "acc_strict",
        "mode",
        "response_quality",
        "last_pulse_ok",
        "csv_complete",
        "structural_fails",
        "orphan_class",
        "status",
        "n_trials",
        "has_train",
        "has_test",
        "has_learner",
    ]
    with matrix_out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=matrix_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    n_fail = sum(1 for r in rows if r["status"] == "FAIL")
    findings = ROOT / "AUDIT_FINDINGS.md"
    findings.write_text(
        f"# StructTrain structural audit ({day})\n\n"
        f"- Experiments scanned: **{len(rows)}**\n"
        f"- FAIL: **{n_fail}**\n"
        f"- Structure CSV: `{out.name}`\n"
        f"- Matrix CSV: `{matrix_out.name}`\n\n"
        f"## FAIL sample\n\n"
        + "\n".join(f"- `{r['exp']}`: {r['fails']}" for r in rows if r["status"] == "FAIL")[:8000]
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out} rows={len(rows)} fail={n_fail}")
    print(f"wrote {matrix_out}")
    print(f"wrote {findings}")

    if args.rebuild_gate:
        gate_path = ROOT / "AUDIT_GATE_RECOMPUTE.csv"
        arch_dir = ROOT / "archive"
        arch_dir.mkdir(parents=True, exist_ok=True)
        arch = arch_dir / f"AUDIT_GATE_RECOMPUTE_{stamp}_phase11_reaudit.csv"
        if gate_path.exists():
            shutil.copy2(gate_path, arch)
            print(f"archived previous GATE -> {arch.name}")
        gate_rows = collect_gate_rows()
        gate_fields = [
            "exp",
            "n",
            "ok_legacy",
            "ok_strict",
            "ok_audit",
            "acc_legacy",
            "acc_strict",
            "fire_all_legacy",
            "fire_all_strict",
            "late_fp",
            "late_fn",
            "response_quality",
            "n_burst",
            "n_per_stim",
            "max_spikes",
            "mode_legacy",
            "csv",
        ]
        with gate_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=gate_fields)
            w.writeheader()
            w.writerows(gate_rows)
        ok = sum(1 for r in gate_rows if r["ok_audit"] == "1")
        print(f"wrote {gate_path} rows={len(gate_rows)} ok_audit={ok}")


if __name__ == "__main__":
    main()

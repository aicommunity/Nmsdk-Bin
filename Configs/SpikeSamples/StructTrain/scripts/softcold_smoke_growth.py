#!/usr/bin/env python3
"""S2 smoke: soft-cold + short train wall; pass if TipR leaves flat OR L[0]>1.

Does not require full SoftCold PASS / Need=0.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import posttune_verify as pv  # noqa: E402
from repro_cold_lib import (  # noqa: E402
    TIPR_COLD,
    get_tag,
    soft_cold_reset_train,
    tip_indices,
)

FLAT = [float(x) for x in TIPR_COLD.split()]


def _tipr_vec(raw: str | None) -> list[float] | None:
    if not raw:
        return None
    try:
        return [float(x) for x in raw.replace(",", " ").split()[:4]]
    except ValueError:
        return None


def _l_vec(raw: str | None) -> list[int] | None:
    if not raw:
        return None
    try:
        return [int(float(x)) for x in raw.replace(",", " ").split()[:4]]
    except ValueError:
        return None


def tipr_left_flat(tipr: list[float] | None, *, tol: float = 1e5) -> bool:
    if not tipr or len(tipr) < 4:
        return False
    return any(abs(a - b) > tol for a, b in zip(tipr, FLAT))


def read_growth(train: Path) -> dict:
    pt = (train / "Parameters_00.xml").read_text(encoding="utf-8")
    tipr = _tipr_vec(get_tag(pt, "TipSynapseResistance"))
    L = _l_vec(get_tag(pt, "DendriteLength"))
    live = train / "posttune_tipr_live.txt"
    live_tipr = None
    live_L = None
    if live.exists():
        text = live.read_text(encoding="utf-8")
        m = re.search(r"tipr=(.+)", text)
        if m:
            live_tipr = _tipr_vec(m.group(1))
        m = re.search(r"L=(.+)", text)
        if m:
            live_L = _l_vec(m.group(1))
    tipr_use = live_tipr or tipr
    L_use = live_L or L
    growth = tipr_left_flat(tipr_use) or (L_use is not None and L_use[0] > 1)
    return {
        "tipr": tipr_use,
        "L": L_use,
        "Need": get_tag(pt, "IsNeedToTrain"),
        "growth_started": growth,
        "source": "live" if live_tipr or live_L else "params",
    }


def _trace_growth(train: Path) -> dict | None:
    """Best-effort TipR/L from StatisticLog traces (NM may not have saved Parameters)."""
    stat = pv._latest_stat_dir(train)
    if stat is None:
        return None
    tipr = pv._last_trace_vector(stat, "TipSynapseResistanceTrace")
    lens = pv._last_trace_vector(stat, "DendriteLengthTrace")
    if not tipr and not lens:
        return None
    tipr_f = [float(x) for x in tipr[:4]] if tipr else None
    L_i = [int(float(x)) for x in lens[:4]] if lens else None
    return {
        "tipr": tipr_f,
        "L": L_i,
        "growth_started": tipr_left_flat(tipr_f)
        or (L_i is not None and len(L_i) > 0 and L_i[0] > 1),
        "source": "statistic_trace",
    }


def run_smoke(case: str, *, wall_min: float, train_t: float | None) -> dict:
    if case not in pv.CASES:
        raise SystemExit(f"unknown case {case}")
    meta = dict(pv.CASES[case])
    archive = meta["root"]
    tlim = float(train_t if train_t is not None else meta["train_t"])
    work = pv.prepare_clean_case(f"{case}_smoke", archive)
    train = work / "Train"
    soft_cold_reset_train(train)
    contract = json.loads((train / "cold_reset_contract.json").read_text(encoding="utf-8"))
    tips = tip_indices((train / "Model_00.xml").read_text(encoding="utf-8"))
    assert contract.get("softcold_fix") == "2026-09-27_sbm2_strip_tip1"
    assert tips and max(tips) <= 1

    from repro_cold_lib import ensure_tag_after, set_tag

    for rel in ("Parameters_00.xml", "Model_00.xml"):
        p = train / rel
        t = p.read_text(encoding="utf-8")
        t = ensure_tag_after(t, "IsNeedToTrain", "EnablePostTrainTuning", "1")
        t = set_tag(t, "EnablePostTrainTuning", "1", 1)
        t = ensure_tag_after(
            t,
            "EnablePostTrainTuning",
            "EnablePostTrainMidThreshold",
            "1",
            attrs=' Type="b" PType="257" IoType="17"',
        )
        t = set_tag(t, "EnablePostTrainMidThreshold", "1", 1)
        t = ensure_tag_after(
            t,
            "EnablePostTrainMidThreshold",
            "PostTrainTipResistanceMode",
            "1",
            attrs=' Type="i" PType="257" IoType="17"',
        )
        t = set_tag(t, "PostTrainTipResistanceMode", "1", 1)
        p.write_text(t, encoding="utf-8")

    log = train / "run_softcold_smoke.log"
    max_polls = max(2, int(wall_min * 60 / 30) + 1)
    print(f"SMOKE {case} work={work} -t {tlim} wall~{wall_min}m polls={max_polls}")
    ini = train / "Project.ini"
    pv.assert_disk_for_train()
    slog = train / "StatisticLog"
    if slog.is_dir():
        shutil.rmtree(slog, ignore_errors=True)
    for stale in ("posttune_complete.flag", "posttune_tipr_live.txt"):
        p = train / stale
        if p.exists():
            p.unlink()
    cmd = [str(pv.NM), "-c", str(ini), "-s", "-t", str(tlim), "-x", "-S"]
    proc = subprocess.Popen(
        cmd, cwd=str(train), stdout=log.open("w"), stderr=subprocess.STDOUT
    )
    early = None
    for i in range(1, max_polls + 1):
        time.sleep(30)
        if proc.poll() is not None:
            break
        need = get_tag(
            (train / "Parameters_00.xml").read_text(encoding="utf-8"), "IsNeedToTrain"
        )
        tg = _trace_growth(train)
        print(
            f"  poll#{i} Need={need} growth={tg} et~{i * 30}s rc={proc.poll()}"
        )
        if tg and tg["growth_started"]:
            early = tg
            print("  GROWTH detected — terminate NM for smoke")
            proc.terminate()
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
            break
    else:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
    child_rc = proc.poll()
    growth = early or _trace_growth(train) or read_growth(train)
    if isinstance(growth, dict) and "Need" not in growth:
        growth = {
            **growth,
            "Need": get_tag(
                (train / "Parameters_00.xml").read_text(encoding="utf-8"),
                "IsNeedToTrain",
            ),
        }
    out = {
        "case": case,
        "work": str(work),
        "train_t": tlim,
        "wall_min_budget": wall_min,
        "max_polls": max_polls,
        "child_rc": child_rc,
        "softcold_fix": contract.get("softcold_fix"),
        "model_max_seg": max(tips),
        "sbm_all": contract["xml_before_nm"]["StructureBuildMode_all"],
        **growth,
        "pass": bool(growth.get("growth_started")),
    }
    report = work / "softcold_smoke_report.json"
    report.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    # also copy under audit evidence
    ev = Path(
        "/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence"
    )
    ev.mkdir(parents=True, exist_ok=True)
    shutil.copy2(report, ev / f"S2_smoke_{case}.json")
    print("SMOKE_REPORT", report)
    print(json.dumps(out, indent=2))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--wall-min", type=float, default=20.0)
    ap.add_argument("--train-t", type=float, default=None)
    args = ap.parse_args()
    out = run_smoke(args.case, wall_min=args.wall_min, train_t=args.train_t)
    sys.exit(0 if out["pass"] else 2)


if __name__ == "__main__":
    main()

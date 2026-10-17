#!/usr/bin/env python3
"""T3 H3: soft_cold vs strip_cold on br25_on (same archive, two workdirs).

Does not mutate the EXP archive. Writes evidence/tails/T3_H3_soft_vs_strip.json.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/user/Nmsdk")
sys.path.insert(0, str(ROOT / "Bin/Configs/SpikeSamples/StructTrain/scripts"))
import posttune_verify as pv  # noqa: E402
from repro_cold_lib import soft_cold_reset_train, strip_cold_reset_train  # noqa: E402

EVIDENCE = ROOT / "Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails"
ARCHIVE = (
    ROOT
    / "Bin/Configs/SpikeSamples/StructTrain/SelectivityBranch"
    / "EXP_br_span25_packA_gen_C1e9_posttune"
)


def tip_count(model: Path) -> int:
    if not model.exists():
        return -1
    t = model.read_text(encoding="utf-8", errors="replace")
    # Count TipSynapseResistance vector entries or Tip components.
    m = re.search(r"<TipSynapseResistance[^>]*>([^<]*)</TipSynapseResistance>", t)
    if m:
        return len([x for x in m.group(1).split() if x.strip()])
    return t.count("TipSynapse")


def snap_side(work: Path, side: str) -> dict:
    params = work / side / "Parameters_00.xml"
    s = pv.snap_params(params) if params.exists() else {}
    flag = work / side / "posttune_complete.flag"
    meta = pv.parse_flag_file(flag) if flag.exists() else {}
    return {
        "Need": s.get("IsNeedToTrain"),
        "TipR": s.get("TipSynapseResistance"),
        "L": s.get("DendriteLength"),
        "mid": s.get("FixedLTZThreshold"),
        "flag_exists": flag.exists(),
        "flag_result": meta.get("result"),
        "flag_metrics": meta.get("metrics") or meta.get("mid"),
        "tip_slots": tip_count(work / side / "Model_00.xml"),
    }


def run_arm(label: str, reset_fn) -> dict:
    utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"br25_h3_{label}_{utc}"
    work = pv.prepare_clean_case(f"br25_h3_{label}", ARCHIVE)
    reset_fn(work / "Train")
    old = dict(pv.CASES["br25_on"])
    old_soft = pv.soft_cold_reset_train

    def noop(_train):
        return None

    try:
        # run_case always soft_cold_reset_train — disable so strip arm stays stripped.
        pv.soft_cold_reset_train = noop  # type: ignore
        pv.CASES["br25_on"] = dict(old)
        pv.CASES["br25_on"]["root"] = work
        row = pv.run_case(
            "br25_on",
            use_archive_inplace=True,
            skip_train=False,
        )
    finally:
        pv.CASES["br25_on"] = old
        pv.soft_cold_reset_train = old_soft
    train = snap_side(work, "Train")
    test = snap_side(work, "Test")
    return {
        "label": label,
        "work": str(work),
        "run_id": run_id,
        "train": train,
        "test": test,
        "row": {
            "train_status": row.get("train_status"),
            "Need": (row.get("after") or {}).get("IsNeedToTrain"),
            "TipR": (row.get("after") or {}).get("TipSynapseResistance"),
            "mid": (row.get("after") or {}).get("FixedLTZThreshold"),
            "fires": row.get("fires"),
            "gate_ok": row.get("gate_ok"),
            "row_fail": row.get("row_fail"),
            "fail_notes": row.get("fail_notes"),
            "params_source": row.get("params_source"),
            "tipr_class": row.get("tipr_class"),
        },
    }


def main() -> int:
    if not ARCHIVE.is_dir():
        print("missing archive", ARCHIVE)
        return 2
    soft = run_arm("soft", soft_cold_reset_train)
    strip = run_arm("strip", strip_cold_reset_train)

    def key(arm):
        r = arm["row"]
        return {
            "Need": r.get("Need"),
            "TipR": r.get("TipR"),
            "mid": r.get("mid"),
            "fires": r.get("fires"),
            "tipr_class": r.get("tipr_class"),
            "train_tips": arm["train"].get("tip_slots"),
        }

    diff = key(soft) != key(strip)
    out = {
        "probe": "T3_H3_soft_vs_strip",
        "archive": str(ARCHIVE),
        "soft": soft,
        "strip": strip,
        "strip_differs_from_soft": diff,
        "verdict": "strip_differs" if diff else "no_material_diff",
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / "T3_H3_soft_vs_strip.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    # also under _repro
    (ROOT / "Bin/Configs/SpikeSamples/StructTrain/_repro/runs").mkdir(parents=True, exist_ok=True)
    print(json.dumps({"verdict": out["verdict"], "evidence": str(path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

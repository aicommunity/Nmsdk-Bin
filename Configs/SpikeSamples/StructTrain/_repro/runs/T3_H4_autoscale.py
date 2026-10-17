#!/usr/bin/env python3
"""T3 H4: AutoScaleIterationGap=1 vs 0 on br25_on after soft cold."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("/home/user/Nmsdk")
sys.path.insert(0, str(ROOT / "Bin/Configs/SpikeSamples/StructTrain/scripts"))
import posttune_verify as pv  # noqa: E402
from repro_cold_lib import ensure_tag_after, soft_cold_reset_train  # noqa: E402

EVIDENCE = ROOT / "Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails"
ARCHIVE = (
    ROOT
    / "Bin/Configs/SpikeSamples/StructTrain/SelectivityBranch"
    / "EXP_br_span25_packA_gen_C1e9_posttune"
)
# Branch EffectiveDatasetDelaySec floor ~1.55 when AutoScale on (see NNeuronTimeLearnerBranch.cpp).
EXPECTED_DELAY_FLOOR = 1.55


def set_autoscale(train: Path, value: str) -> None:
    for rel in ("Parameters_00.xml", "Model_00.xml"):
        p = train / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        t = ensure_tag_after(
            t,
            "IterationGap",
            "AutoScaleIterationGap",
            value,
            attrs=' Type="b" PType="257" IoType="17"',
        )
        t = pv.set_tag(t, "AutoScaleIterationGap", value, 1)
        p.write_text(t, encoding="utf-8")


def arm(gap: str) -> dict:
    work = pv.prepare_clean_case(f"br25_h4_gap{gap}", ARCHIVE)
    soft_cold_reset_train(work / "Train")
    old_soft = pv.soft_cold_reset_train
    old_case = dict(pv.CASES["br25_on"])
    # Capture set_tag path: after run_case forces AutoScale=1, re-apply desired gap
    # before wait by wrapping soft_cold to set tags then gap.
    real_soft = soft_cold_reset_train

    def soft_then_gap(train: Path) -> None:
        real_soft(train)
        from repro_cold_lib import ensure_tag_after

        enable = "1"
        tip_mode = "1"
        for rel in ("Parameters_00.xml", "Model_00.xml"):
            p = train / rel
            if not p.exists():
                continue
            t = p.read_text(encoding="utf-8")
            t = ensure_tag_after(t, "IsNeedToTrain", "EnablePostTrainTuning", enable)
            t = pv.set_tag(t, "EnablePostTrainTuning", enable, 1)
            t = ensure_tag_after(
                t,
                "IterationGap",
                "AutoScaleIterationGap",
                gap,
                attrs=' Type="b" PType="257" IoType="17"',
            )
            t = pv.set_tag(t, "AutoScaleIterationGap", gap, 1)
            t = ensure_tag_after(
                t,
                "EnablePostTrainTuning",
                "EnablePostTrainMidThreshold",
                "1",
                attrs=' Type="b" PType="257" IoType="17"',
            )
            t = pv.set_tag(t, "EnablePostTrainMidThreshold", "1", 1)
            t = ensure_tag_after(
                t,
                "EnablePostTrainMidThreshold",
                "PostTrainTipResistanceMode",
                tip_mode,
                attrs=' Type="i" PType="257" IoType="17"',
            )
            t = pv.set_tag(t, "PostTrainTipResistanceMode", tip_mode, 1)
            p.write_text(t, encoding="utf-8")

    try:
        pv.soft_cold_reset_train = soft_then_gap  # type: ignore
        pv.CASES["br25_on"] = dict(old_case)
        pv.CASES["br25_on"]["root"] = work
        # skip tag block duplication: patch run_case by skip_train? No — need train.
        # Instead monkeypatch set_tag for AutoScale only when writing "1"
        real_set = pv.set_tag

        def set_tag_gap_aware(text, tag, value, count=1):
            if tag == "AutoScaleIterationGap":
                value = gap
            return real_set(text, tag, value, count)

        pv.set_tag = set_tag_gap_aware  # type: ignore
        row = pv.run_case("br25_on", use_archive_inplace=True)
    finally:
        pv.soft_cold_reset_train = old_soft
        pv.CASES["br25_on"] = old_case
        pv.set_tag = real_set  # type: ignore
    after = row.get("after") or {}
    gap_xml = after.get("AutoScaleIterationGap") or pv.get_tag(
        (work / "Train" / "Parameters_00.xml").read_text(encoding="utf-8"),
        "AutoScaleIterationGap",
    )
    delay = after.get("Delay") or after.get("DatasetDelay") or ""
    if not delay:
        delay = pv.get_tag(
            (work / "Train" / "Parameters_00.xml").read_text(encoding="utf-8"),
            "Delay",
        ) or ""
    return {
        "gap": gap,
        "work": str(work),
        "AutoScaleIterationGap": gap_xml,
        "Delay": delay,
        "Need": after.get("IsNeedToTrain"),
        "TipR": after.get("TipSynapseResistance"),
        "mid": after.get("FixedLTZThreshold"),
        "fires": row.get("fires"),
        "train_status": row.get("train_status"),
        "gate_ok": row.get("gate_ok"),
        "row_fail": row.get("row_fail"),
        "fail_notes": row.get("fail_notes"),
        "expected_delay_floor_sec": EXPECTED_DELAY_FLOOR,
    }


def main() -> int:
    a1 = arm("1")
    a0 = arm("0")
    out = {
        "probe": "T3_H4_autoscale",
        "gap1": a1,
        "gap0": a0,
        "differs": {k: a1.get(k) != a0.get(k) for k in ("Delay", "mid", "TipR", "fires", "Need")},
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / "T3_H4_autoscale.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"evidence": str(path), "differs": out["differs"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

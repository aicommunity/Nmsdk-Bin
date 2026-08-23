#!/usr/bin/env python3
"""Merge learner weight tags from train into test Model (preserve test topology/links)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

MODEL_WEIGHT_TAGS = [
    "DendriteLength",
    "TipSynapseResistance",
    "InitialSomaPotential",
    "FixedLTZThreshold",
    "LTZThreshold",
    "UseFixedLTZThreshold",
    "AttenuationGamma",
    "AutoCalibrateFixedLTZThreshold",
    "CalibrateLTZThresholdMode",
    "CalibrateLTZThresholdFraction",
    "CalibrateLTZThresholdMin",
    "CalibrateLTZThresholdMax",
    "CalibratedFixedLTZThreshold",
]

LEARNER_NAMES = ("NeuronTimeLearnerBranch", "NeuronTimeLearner")


def extract_tag(text: str, tag: str) -> str | None:
    pat = rf"(<(?:{tag})[^>]*>.*?</(?:{tag})>|<(?:{tag})[^>]*/>)"
    m = re.search(pat, text, re.DOTALL)
    return m.group(1) if m else None


def replace_tag(text: str, tag: str, block: str) -> str:
    pat = rf"<(?:{tag})[^>]*>.*?</(?:{tag})>|<(?:{tag})[^>]*/>"
    if re.search(pat, text, re.DOTALL):
        return re.sub(pat, block, text, count=1, flags=re.DOTALL)
    return text


def find_learner(text: str) -> str | None:
    for name in LEARNER_NAMES:
        if f"<{name} " in text:
            return name
    return None


def merge(train_dir: Path, test_dir: Path) -> None:
    train_params = train_dir / "Parameters_00.xml"
    train_model = train_dir / "Model_00.xml"
    test_model = test_dir / "Model_00.xml"
    if not test_model.exists():
        raise SystemExit(f"missing test model: {test_model}")

    train_p = train_params.read_text(encoding="utf-8") if train_params.exists() else ""
    train_m = train_model.read_text(encoding="utf-8") if train_model.exists() else ""
    test = test_model.read_text(encoding="utf-8")

    learner = find_learner(test) or find_learner(train_m) or "NeuronTimeLearner"

    for tag in MODEL_WEIGHT_TAGS:
        block = extract_tag(train_p, tag) or extract_tag(train_m, tag)
        if block:
            test = replace_tag(test, tag, block)

    test_model.write_text(test, encoding="utf-8")
    print(f"merged train weights into {test_model}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(f"Usage: {sys.argv[0]} <train_dir> <test_dir>")
    merge(Path(sys.argv[1]), Path(sys.argv[2]))

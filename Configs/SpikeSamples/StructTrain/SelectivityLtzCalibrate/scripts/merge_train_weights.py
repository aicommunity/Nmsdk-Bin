#!/usr/bin/env python3
"""Merge trained neuron weights from train Parameters into test Parameters (keep test dataset)."""
import re
import sys
from pathlib import Path


WEIGHT_TAGS = [
    "TipSynapseResistance",
    "DendriteLength",
    "InitialSomaPotential",
    "NumSynapse",
    "NumDendriteMembranePartsVec",
    "FixedLTZThreshold",
    "UseFixedLTZThreshold",
    "LTZThreshold",
    "CalibratedFixedLTZThreshold",
    "AttenuationGamma",
    "AutoCalibrateFixedLTZThreshold",
    "CalibrateLTZThresholdMode",
    "CalibrateLTZThresholdFraction",
    "CalibrateLTZThresholdMin",
    "CalibrateLTZThresholdMax",
]

TRAIN_ONLY_TAGS = [
    "TrainingPattern",
    "TrainingDendIndexes",
    "TrainingSynapsisNum",
    "TrainingPhase",
    "ResetToUntrainedState",
    "NeuronClassName",
    "UseElementDefaults",
    "MembraneCapacity",
    "SynapseDissociationTC",
]

TAGS = WEIGHT_TAGS + TRAIN_ONLY_TAGS


def extract_tag(text: str, tag: str) -> str | None:
    pat = rf"(<(?:{tag})[^>]*>.*?</(?:{tag})>|<(?:{tag})[^>]*/>)"
    m = re.search(pat, text, re.DOTALL)
    return m.group(1) if m else None


def replace_tag(text: str, tag: str, block: str) -> str:
    pat = rf"<(?:{tag})[^>]*>.*?</(?:{tag})>|<(?:{tag})[^>]*/>"
    if re.search(pat, text, re.DOTALL):
        return re.sub(pat, block, text, count=1, flags=re.DOTALL)
    return text


def merge(train_path: Path, test_path: Path, *, test_mode: bool = False) -> None:
    train = train_path.read_text(encoding="utf-8")
    test = test_path.read_text(encoding="utf-8")
    tags = WEIGHT_TAGS if test_mode else TAGS
    for tag in tags:
        block = extract_tag(train, tag)
        if block:
            test = replace_tag(test, tag, block)
    # ensure inference mode on test learner
    test = re.sub(
        r"<IsNeedToTrain Type=\"b\" PType=\"257\" IoType=\"17\">[01]</IsNeedToTrain>",
        '<IsNeedToTrain Type="b" PType="257" IoType="17">0</IsNeedToTrain>',
        test,
        count=1,
    )
    test = re.sub(
        r"(<NeuronTimeLearner(?:Branch)? Class=\"NNeuronTimeLearner(?:Branch)?\">[\s\S]*?<StructureBuildMode Type=\"i\" PType=\"257\" IoType=\"17\">)[0-9](</StructureBuildMode>)",
        r"\g<1>0\2",
        test,
        count=1,
    )
    test_path.write_text(test, encoding="utf-8")


if __name__ == "__main__":
    test_mode = "--test" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--test"]
    if len(args) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} [--test] <train_params> <test_params>")
    merge(Path(args[0]), Path(args[1]), test_mode=test_mode)

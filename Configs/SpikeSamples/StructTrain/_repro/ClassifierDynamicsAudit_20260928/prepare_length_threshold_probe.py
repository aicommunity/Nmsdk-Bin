#!/usr/bin/env python3
"""Clone dendrite-length controls at one shared LTZone threshold."""

from __future__ import annotations

import argparse
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE_ROOT = HERE / "NSpikeDendriteLengthAudit_20260928"
OUTPUT_ROOT = HERE.parent / "NSpikeDendriteThresholdAudit_20260928"
THRESHOLD = 0.0085
TOKEN = f"{THRESHOLD:.4f}".replace(".", "")
VARIANTS = {"short": 3, "medium": 8, "long": 17}


def set_text(parent: ET.Element, path: str, value: str) -> None:
    node = parent.find(path)
    if node is None:
        raise ValueError(f"Missing {path}")
    node.text = value


def write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="\t")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def clone_one(source_root: Path, output_root: Path, length_name: str, length: int, state: str) -> Path:
    source = source_root / f"NSpikeClassifier_Class2_{length_name}_D{length}_{state}_20260928"
    target = output_root / f"NSpikeClassifier_Class2_{length_name}_D{length}_{state}_Threshold{TOKEN}_20260928"
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")
    target.mkdir(parents=True)
    for filename in ("Project.ini", "Model_00.xml", "Parameters_00.xml", "Interface.xml", "input_data.txt", "expected_classes.csv", "History.xml"):
        path = source / filename
        if path.is_file():
            shutil.copy2(path, target / filename)

    for filename in ("Model_00.xml", "Parameters_00.xml"):
        path = target / filename
        tree = ET.parse(path)
        root = tree.getroot()
        classifier = next((node for node in root.iter() if node.tag == "SpikeClassifier" and node.get("Class") == "NSpikeClassifier"), None)
        if classifier is None:
            raise ValueError(f"NSpikeClassifier missing in {path}")
        for key, value in {
            "IsNeedToTrain": "0",
            "DataFromFile": "1",
            "LTZThreshold": format(THRESHOLD, ".17g"),
            "FixedLTZThreshold": format(THRESHOLD, ".17g"),
            "UseFixedLTZThreshold": "1",
        }.items():
            set_text(classifier, f"./Parameters/{key}", value)

        trainers = [node for node in root.iter() if node.get("Class") == "NNeuronTrainer"]
        if len(trainers) != 3:
            raise ValueError(f"Expected 3 NNeuronTrainer components, found {len(trainers)}")
        for trainer in trainers:
            for key, value in {
                "IsNeedToTrain": "0",
                "LTZThreshold": format(THRESHOLD, ".17g"),
                "FixedLTZThreshold": format(THRESHOLD, ".17g"),
                "UseFixedLTZThreshold": "1",
            }.items():
                set_text(trainer, f"./Parameters/{key}", value)
            neuron = trainer.find("./Components/Neuron")
            if neuron is None:
                raise ValueError("Trainer neuron missing")
            zone = neuron.find("./Components/LTZone")
            if zone is None:
                raise ValueError("LTZone missing")
            set_text(zone, "./Parameters/Threshold", format(THRESHOLD, ".17g"))

        recorder = next((node for node in root.iter() if node.tag == "ClassifierDynamicsRecorder"), None)
        if recorder is not None:
            # Keep the full Windows path below MAX_PATH. Every experiment
            # already has its own data directory, so a short local filename
            # is sufficient and avoids silent recorder open failures.
            set_text(recorder, "./Parameters/SavePath", "")
            set_text(recorder, "./Parameters/FileName", "trace.csv")
        write_xml(tree, path)

    project = target / "Project.ini"
    data = project.read_text(encoding="utf-8-sig")
    name = target.name
    data, count = re.subn(r"(<ProjectName>).*?(</ProjectName>)", rf"\g<1>{name}\g<2>", data, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError("ProjectName missing")
    project.write_text(data, encoding="utf-8")
    (target / "README.md").write_text(
        f"# {name}\n\n"
        f"Replay of the {state} length-control model. Branch 2 of class 2 has {length} segments and the same {37} active synapses as its source clone. "
        f"All classifier neurons use the same fixed LTZone threshold {THRESHOLD}; training is disabled. Only threshold, replay flags, run name, and recorder output path differ from the source.\n\n"
        "Run with `NeuroModelerConsole.exe -c Project.ini -s -t 8.1 -x -S`.\n",
        encoding="utf-8",
    )
    print(target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    source_root = args.source_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    for state in ("On", "Off"):
        for variant, length in VARIANTS.items():
            clone_one(source_root, output_root, variant, length, state)


if __name__ == "__main__":
    main()

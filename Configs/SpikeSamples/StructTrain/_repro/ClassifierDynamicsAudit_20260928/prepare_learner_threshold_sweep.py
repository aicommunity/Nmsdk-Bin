#!/usr/bin/env python3
"""Create fixed-topology response probes from the completed Learner run."""

from __future__ import annotations

import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parent
SEED = AUDIT_DIR / "NNeuronLearner_NSPNeuron_medium_spread_20260928"
THRESHOLDS = [0.009, 0.0092, 0.0093, 0.0094, 0.01, 0.0105, 0.011]
RUN_SECONDS = 10.5


def set_text(parent: ET.Element, path: str, value: str) -> None:
    node = parent.find(path)
    if node is None:
        raise ValueError(f"Missing {path}")
    node.text = value


def patch_project(path: Path, name: str) -> None:
    data = path.read_text(encoding="utf-8-sig")
    for tag, value in {
        "ProjectName": name,
        "MaxCalculationModelTime": str(RUN_SECONDS),
        "ProjectAutoSaveFlag": "1",
        "ProjectAutoSaveModelTimeInterval": "10",
    }.items():
        data, count = re.subn(
            rf"(<{tag}>).*?(</{tag}>)",
            lambda match: match.group(1) + value + match.group(2),
            data,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError(f"Expected one <{tag}>; found {count}")
    path.write_text(data, encoding="utf-8")


def write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="\t")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def prepare(threshold: float) -> Path:
    token = f"{threshold:.4f}".replace(".", "")
    name = f"NNeuronLearner_Threshold_{token}_20260928"
    dst = AUDIT_DIR / name
    dst.mkdir(parents=True, exist_ok=True)
    for filename in ("Project.ini", "Model_00.xml", "Parameters_00.xml", "Interface.xml"):
        shutil.copy2(SEED / filename, dst / filename)
    patch_project(dst / "Project.ini", name)

    for filename in ("Model_00.xml", "Parameters_00.xml"):
        path = dst / filename
        tree = ET.parse(path)
        root = tree.getroot()
        learner = root.find(".//NeuronLearner")
        if learner is None:
            raise ValueError(f"NeuronLearner missing in {path}")
        for key, value in {
            "IsNeedToTrain": "0",
            "LTZThreshold": format(threshold, ".17g"),
            "FixedLTZThreshold": format(threshold, ".17g"),
            "UseFixedLTZThreshold": "1",
        }.items():
            set_text(learner, f"./Parameters/{key}", value)
        neuron = learner.find("./Components/Neuron")
        if neuron is None or neuron.get("Class") != "NSPNeuron":
            raise ValueError("Exact NSPNeuron missing")
        set_text(neuron, "./Components/LTZone/Parameters/Threshold", format(threshold, ".17g"))
        recorder = root.find(".//LearnerSpikeRecorder")
        if recorder is not None:
            for key, value in {
                "SavePath": "LearnerSpikeProbe",
                "FileName": f"ltz_{token}.csv",
            }.items():
                set_text(recorder, f"./Parameters/{key}", value)
        write_xml(tree, path)

    (dst / "README.md").write_text(
        f"# NNeuronLearner fixed-topology threshold probe ({threshold:g})\n\n"
        "Replay the completed medium-spread structural-learning model with training "
        "disabled. The saved topology and all physical model parameters are kept fixed. "
        "Only the LTZone threshold and its Learner fixed-threshold fields are changed. "
        "The passive recorder captures LTZone output and potential for 10.5 seconds.\n\n"
        f"Run from this directory with `NeuroModelerConsole.exe -c Project.ini -s -t {RUN_SECONDS} -x -S`.\n",
        encoding="utf-8",
    )
    print(dst)
    return dst


if __name__ == "__main__":
    for value in THRESHOLDS:
        prepare(value)

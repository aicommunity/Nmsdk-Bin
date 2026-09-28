#!/usr/bin/env python3
"""Clone the existing synthetic NSpikeClassifier pair with calibrated LTZone thresholds."""

from __future__ import annotations

import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = AUDIT_DIR.parents[0] / "ClassifierDynamicsAudit_20260927"
RUN_SECONDS = 8.01
THRESHOLDS = [0.006, 0.0085, 0.009, 0.01]
STATES = {
    "On": ("NSpikeClassifier_Synthetic_OutputsOn_20260927", "1"),
    "Off": ("NSpikeClassifier_Synthetic_OutputsOff_20260927", "0"),
}


def set_text(parent: ET.Element, path: str, value: str) -> None:
    node = parent.find(path)
    if node is None:
        raise ValueError(f"Missing {path}")
    node.text = value


def write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="\t")
    tree.write(path, encoding="utf-8", xml_declaration=True)


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


def prepare(state: str, threshold: float) -> Path:
    source_name, _inhibition = STATES[state]
    source = SOURCE_ROOT / source_name
    token = f"{threshold:.4f}".replace(".", "")
    name = f"NSpikeClassifier_Synthetic_Outputs{state}_Threshold{token}_20260928"
    output = AUDIT_DIR / name
    output.mkdir(parents=True, exist_ok=True)
    for filename in ("Project.ini", "Model_00.xml", "Parameters_00.xml", "Interface.xml", "input_data.txt", "expected_classes.csv"):
        shutil.copy2(source / filename, output / filename)
    patch_project(output / "Project.ini", name)

    for filename in ("Model_00.xml", "Parameters_00.xml"):
        path = output / filename
        tree = ET.parse(path)
        root = tree.getroot()
        classifier = root.find(".//SpikeClassifier")
        if classifier is None or classifier.get("Class") != "NSpikeClassifier":
            raise ValueError(f"NSpikeClassifier wrapper missing in {path}")
        for key, value in {
            "IsNeedToTrain": "0",
            # A completed source replay persists DataFromFile=0 after EOF.
            # Explicitly re-arm the copied four-row synthetic file here.
            "DataFromFile": "1",
            "LTZThreshold": format(threshold, ".17g"),
            "FixedLTZThreshold": format(threshold, ".17g"),
            "UseFixedLTZThreshold": "1",
        }.items():
            set_text(classifier, f"./Parameters/{key}", value)
        trainers = [n for n in root.iter() if n.get("Class") == "NNeuronTrainer"]
        if len(trainers) != 3:
            raise ValueError(f"Expected three trained neurons in {path}; found {len(trainers)}")
        for trainer in trainers:
            for key, value in {
                "IsNeedToTrain": "0",
                "LTZThreshold": format(threshold, ".17g"),
                "FixedLTZThreshold": format(threshold, ".17g"),
                "UseFixedLTZThreshold": "1",
            }.items():
                set_text(trainer, f"./Parameters/{key}", value)
            neuron = trainer.find("./Components/Neuron")
            if neuron is None or neuron.get("Class") != "NSPNeuron":
                raise ValueError("The classifier no longer contains the audited NSPNeuron type")
            zone = neuron.find("./Components/LTZone")
            if zone is None or zone.get("Class") != "NPulseLTZoneThreshold":
                raise ValueError("The classifier LTZone type differs from the calibrated type")
            set_text(zone, "./Parameters/Threshold", format(threshold, ".17g"))

        recorder = root.find(".//ClassifierDynamicsRecorder")
        if recorder is not None:
            set_text(recorder, "./Parameters/FileName", f"LTZOutputs{state}_Threshold{token}.csv")
        write_xml(tree, path)

    (output / "README.md").write_text(
        f"# NSpikeClassifier synthetic replay: lateral inhibition {state}, threshold {threshold:g}\n\n"
        f"Clone of [{source_name}](../ClassifierDynamicsAudit_20260927/{source_name}/README.md). "
        "The four synthetic input rows and the three trained neuron structures are copied "
        "unchanged. All three `NSPNeuron` + `NPulseLTZoneThreshold` units receive the same "
        "fixed threshold through both the classifier wrapper and nested Trainer properties; "
        "training is disabled. The clone explicitly sets `DataFromFile=1`: a completed source "
        "run persists it as 0 after EOF, so copying the saved model without re-arming it would "
        "silently repeat the stored `InputPattern` instead of replaying `input_data.txt`. "
        "Only LTZone thresholds, this replay flag, run name, and recorder filename differ. Lateral inhibition setting and "
        "classifier wiring remain as in the source pair.\n\n"
        f"Run: `NeuroModelerConsole.exe -c Project.ini -s -t {RUN_SECONDS} -x -S`. "
        "Compare `output_data.txt` to `expected_classes.csv`, and count every rising "
        "edge in the three LTZone columns in `ClassifierDynamics/`.\n",
        encoding="utf-8",
    )
    print(output)
    return output


if __name__ == "__main__":
    for value in THRESHOLDS:
        for state in STATES:
            prepare(state, value)

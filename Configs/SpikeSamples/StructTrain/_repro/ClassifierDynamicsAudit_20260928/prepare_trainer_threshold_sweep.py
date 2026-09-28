#!/usr/bin/env python3
"""Create post-training LTZone threshold probes from the type-matched Trainer run."""

from __future__ import annotations

import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


AUDIT_DIR = Path(__file__).resolve().parent
SEED = AUDIT_DIR / "NNeuronTrainer_TypeMatched_wide_spread_20260928"
THRESHOLDS = [0.0047, 0.006, 0.008, 0.009, 0.01, 0.0105, 0.011, 0.012, 0.014]
RUN_SECONDS = 10.5


def text_node(parent: ET.Element, path: str, value: str) -> None:
    node = parent.find(path)
    if node is None:
        raise ValueError(f"Missing XML element {path}")
    node.text = value


def write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="\t")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def patch_project(path: Path, run_name: str) -> None:
    data = path.read_text(encoding="utf-8-sig")
    for tag, value in {
        "ProjectName": run_name,
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
            raise ValueError(f"Expected one <{tag}> element; found {count}")
    path.write_text(data, encoding="utf-8")


def append_potential_probe(root: ET.Element, run_name: str) -> None:
    model = root.find("./Model")
    model_components = model.find("./Components") if model is not None else None
    recorder = model_components.find("./TrainerSpikeRecorder") if model_components is not None else None
    if recorder is None:
        raise ValueError("TrainerSpikeRecorder component not found")
    params = recorder.find("./Parameters")
    text_node(params, "./SignalNamesCsv", "trainer_ltz,ltz_output_potential")
    text_node(params, "./FileName", f"ltz_threshold_{run_name}.csv")

    links = root.find(".//Links")
    if links is None:
        raise ValueError("Model link list not found")
    link = ET.SubElement(links, "elem", {"Type": "ULink"})
    ET.SubElement(link, "Item", {"Type": "ULinkSide", "Index": "-1", "Name": "OutputPotential"}).text = (
        "NeuronTrainer.Neuron.LTZone"
    )
    ET.SubElement(link, "Connector", {"Type": "ULinkSide", "Index": "-1", "Name": "Signals"}).text = (
        "TrainerSpikeRecorder"
    )
    links.set("Size", str(len(links.findall("./elem"))))


def prepare(threshold: float) -> None:
    token = f"{threshold:.4f}".replace(".", "")
    name = f"NNeuronTrainer_Threshold_{token}_20260928"
    dst = AUDIT_DIR / name
    dst.mkdir(parents=True, exist_ok=True)
    for filename in ("Project.ini", "Model_00.xml", "Parameters_00.xml", "Interface.xml"):
        shutil.copy2(SEED / filename, dst / filename)
    patch_project(dst / "Project.ini", name)

    for filename in ("Model_00.xml", "Parameters_00.xml"):
        path = dst / filename
        tree = ET.parse(path)
        root = tree.getroot()
        trainer = root.find(".//NeuronTrainer")
        if trainer is None:
            raise ValueError(f"NeuronTrainer not found in {path}")
        text_node(trainer, "./Parameters/IsNeedToTrain", "0")
        text_node(trainer, "./Parameters/LTZThreshold", format(threshold, ".17g"))
        text_node(trainer, "./Parameters/FixedLTZThreshold", format(threshold, ".17g"))
        text_node(trainer, "./Parameters/UseFixedLTZThreshold", "1")
        neuron = trainer.find("./Components/Neuron")
        if neuron is None:
            raise ValueError(f"Neuron not found in {path}")
        ltzone = neuron.find("./Components/LTZone")
        if ltzone is None:
            raise ValueError(f"LTZone not found in {path}")
        text_node(ltzone, "./Parameters/Threshold", format(threshold, ".17g"))
        if filename == "Model_00.xml":
            append_potential_probe(root, name)
        write_xml(tree, path)

    (dst / "README.md").write_text(
        f"# Trainer fixed-structure threshold probe ({threshold:g})\n\n"
        "This is a post-training replay of the wide-spread synthetic run. The trained "
        "structure and all membrane/synapse parameters are copied unchanged. Only the "
        "fixed `LTZone.Threshold` and matching Trainer threshold fields are varied; "
        "`IsNeedToTrain=0`, so no structural training runs. The neuron remains "
        "`NSPNeuron` with `NPulseLTZoneThreshold`.\n\n"
        f"Run: `NeuroModelerConsole.exe -c Project.ini -s -t {RUN_SECONDS} -x -S`. "
        "The recorder captures both LTZone pulses and `OutputPotential` for threshold "
        "crossing analysis.\n",
        encoding="utf-8",
    )
    print(dst)


def main() -> None:
    if not SEED.is_dir():
        raise FileNotFoundError(SEED)
    for threshold in THRESHOLDS:
        prepare(threshold)


if __name__ == "__main__":
    main()

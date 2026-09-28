#!/usr/bin/env python3
"""Clone a Trainer-trained NSPNeuron topology into NNeuronLearner for relearning."""

from __future__ import annotations

import copy
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parent
ROOT = AUDIT_DIR.parents[5]
TRAINER_SEED = AUDIT_DIR / "NNeuronTrainer_TypeMatched_wide_spread_20260928"
LEARNER_TEMPLATE = ROOT / "Bin/Configs/SpikeSamples/StructTrain/_repro/NNeuronTrainingReplay/relearning_2_ArbitraryStart_FullSubtreeFix_Run_20260927"
RUN_NAME = "NNeuronLearner_NSPNeuron_medium_spread_20260928"
OUTPUT = AUDIT_DIR / RUN_NAME
PATTERN = [0.05, 0.09, 0.13, 0.16, 0.2]
TRAINING_THRESHOLD = 100.0
FIXED_THRESHOLD = 0.0047
MAX_MODEL_TIME = 120


def set_text(parent: ET.Element, path: str, value: str) -> None:
    node = parent.find(path)
    if node is None:
        raise ValueError(f"Missing {path}")
    node.text = value


def write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="\t")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def patch_project(path: Path) -> None:
    data = path.read_text(encoding="utf-8-sig")
    for tag, value in {
        "ProjectName": RUN_NAME,
        "MaxCalculationModelTime": str(MAX_MODEL_TIME),
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


def update_learner_parameters(learner: ET.Element, neuron: ET.Element) -> None:
    learner.set("Class", "NNeuronLearner")
    p = learner.find("./Parameters")
    if p is None:
        raise ValueError("Learner parameters missing")

    dendrite_lengths = [int(v) for v in (neuron.findtext("./Parameters/NumDendriteMembranePartsVec") or "").split()]
    if len(dendrite_lengths) != 5:
        raise ValueError(f"Expected five physical dendrite lengths, got {dendrite_lengths}")
    synapse_counts = []
    for i, length in enumerate(dendrite_lengths, start=1):
        segment = neuron.find(f"./Components/Dendrite{i}_{length}")
        if segment is None:
            raise ValueError(f"Input segment Dendrite{i}_{length} missing")
        synapse_counts.append(int(segment.findtext("./Parameters/NumExcitatorySynapses") or "0"))

    values = {
        "StructureBuildMode": "1",
        "NeuronClassName": "NSPNeuron",
        "CalculateMode": "0",
        "IsNeedToTrain": "1",
        "UseAutoPreset": "0",
        "Delay": "0.10000000000000001",
        "SpikesFrequency": "0.5",
        "NumInputDendrite": "5",
        "MaxDendriteLength": "100",
        "InputPattern": "\n".join(format(v, ".17g") for v in PATTERN),
        "AdditionalInputPattern": "0\n0\n0\n0\n0",
        "LTZThreshold": format(TRAINING_THRESHOLD, ".17g"),
        "TrainingLTZThreshold": format(TRAINING_THRESHOLD, ".17g"),
        "FixedLTZThreshold": format(FIXED_THRESHOLD, ".17g"),
        "UseFixedLTZThreshold": "0",
        "DendriteLength": " ".join(map(str, dendrite_lengths)),
        "NumSynapse": " ".join(map(str, synapse_counts)),
        "EnableDebug": "0",
    }
    for key, value in values.items():
        node = p.find(f"./{key}")
        if node is None:
            raise ValueError(f"Learner parameter {key} missing")
        node.text = value
        if key in ("InputPattern", "AdditionalInputPattern"):
            node.set("Rows", "5")
            node.set("Cols", "1")
        if key in ("DendriteLength", "NumSynapse"):
            node.set("Size", "5")

    # Train from the actual Trainer-built structure and clear only LTZone threshold state.
    ltzone = neuron.find("./Components/LTZone")
    if ltzone is None:
        raise ValueError("NSPNeuron.LTZone missing")
    zone_threshold = ltzone.find("./Parameters/Threshold")
    if zone_threshold is not None:
        zone_threshold.text = format(TRAINING_THRESHOLD, ".17g")


def convert_to_learner(model_tree: ET.ElementTree, parameter_tree: ET.ElementTree, learner_template: ET.Element) -> None:
    model_root = model_tree.getroot()
    model = model_root.find("./Model")
    learner = model.find("./Components/NeuronTrainer") if model is not None else None
    if model is None or learner is None:
        raise ValueError("Trainer model component missing")
    neuron = learner.find("./Components/Neuron")
    if neuron is None or neuron.get("Class") != "NSPNeuron":
        raise ValueError("The saved Trainer model must contain an NSPNeuron")

    template_params = learner_template.find("./Parameters")
    if template_params is None:
        raise ValueError("Learner template parameters missing")
    old_params = learner.find("./Parameters")
    if old_params is not None:
        learner.remove(old_params)
    learner.insert(0, copy.deepcopy(template_params))
    learner.tag = "NeuronLearner"
    update_learner_parameters(learner, neuron)

    links = model.find("./Links")
    if links is None:
        raise ValueError("Model links missing")
    for node in links.iter():
        if node.text:
            node.text = node.text.replace("NeuronTrainer", "NeuronLearner")
            node.text = node.text.replace("TrainerSpikeRecorder", "LearnerSpikeRecorder")

    recorder = model.find("./Components/TrainerSpikeRecorder")
    if recorder is None:
        raise ValueError("Trainer recorder missing")
    recorder.tag = "LearnerSpikeRecorder"
    for key, value in {
        "SignalNamesCsv": "learner_ltz,learner_potential",
        "SavePath": "LearnerSpikeProbe",
        "FileName": "ltz.csv",
    }.items():
        set_text(recorder, f"./Parameters/{key}", value)

    potential_link = ET.SubElement(links, "elem", {"Type": "ULink"})
    ET.SubElement(potential_link, "Item", {"Type": "ULinkSide", "Index": "-1", "Name": "OutputPotential"}).text = "NeuronLearner.Neuron.LTZone"
    ET.SubElement(potential_link, "Connector", {"Type": "ULinkSide", "Index": "-1", "Name": "Signals"}).text = "LearnerSpikeRecorder"
    links.set("Size", str(len(links.findall("./elem"))))

    parameter_model = parameter_tree.getroot().find("./Model")
    parameter_components = parameter_model.find("./Components") if parameter_model is not None else None
    parameter_trainer = parameter_components.find("./NeuronTrainer") if parameter_components is not None else None
    if parameter_components is None or parameter_trainer is None:
        raise ValueError("Parameters trainer component missing")
    old_parameter_node = parameter_components.find("./TrainerSpikeRecorder")
    if old_parameter_node is None:
        raise ValueError("Parameters recorder component missing")
    old_parameter_node.tag = "LearnerSpikeRecorder"
    for key, value in {
        "SignalNamesCsv": "learner_ltz,learner_potential",
        "SavePath": "LearnerSpikeProbe",
        "FileName": "ltz.csv",
    }.items():
        set_text(old_parameter_node, f"./Parameters/{key}", value)

    learner_params = parameter_trainer.find("./Parameters")
    parameter_trainer.remove(learner_params)
    parameter_trainer.insert(0, copy.deepcopy(learner_template.find("./Parameters")))
    parameter_trainer.tag = "NeuronLearner"
    parameter_neuron = parameter_trainer.find("./Components/Neuron")
    if parameter_neuron is None:
        raise ValueError("Parameter-side NSPNeuron missing")
    update_learner_parameters(parameter_trainer, parameter_neuron)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename in ("Project.ini", "Model_00.xml", "Parameters_00.xml", "Interface.xml"):
        shutil.copy2(TRAINER_SEED / filename, OUTPUT / filename)
    patch_project(OUTPUT / "Project.ini")

    learner_params_tree = ET.parse(LEARNER_TEMPLATE / "Model_00.xml")
    learner_template = learner_params_tree.getroot().find("./Model/Components/NeuronLearner")
    if learner_template is None:
        raise ValueError("NNeuronLearner template missing")

    model_tree = ET.parse(OUTPUT / "Model_00.xml")
    parameter_tree = ET.parse(OUTPUT / "Parameters_00.xml")
    convert_to_learner(model_tree, parameter_tree, learner_template)
    write_xml(model_tree, OUTPUT / "Model_00.xml")
    write_xml(parameter_tree, OUTPUT / "Parameters_00.xml")
    (OUTPUT / "README.md").write_text(
        "# Type-matched NNeuronLearner incremental training\n\n"
        "This clone starts from a fully recorded `NSPNeuron` structure produced by the "
        "matching type-matched Trainer run. It uses the same membrane, channel, synapse, "
        "and input connectivity tree, then enables `NNeuronLearner` on a new synthetic "
        "five-input temporal pattern `[0.05, 0.09, 0.13, 0.16, 0.2]`. The synapse counts "
        "and dendrite lengths in the Learner config are copied from the actual input "
        "segments, preserving a valid starting graph. Training uses threshold 100 and "
        f"switches to fixed threshold {FIXED_THRESHOLD:g} at convergence. Neuron model "
        "parameters are copied unchanged; project autosaves every 10 model seconds.\n\n"
        f"Run from this directory with `NeuroModelerConsole.exe -c Project.ini -s -t {MAX_MODEL_TIME} -x -S`.\n",
        encoding="utf-8",
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()

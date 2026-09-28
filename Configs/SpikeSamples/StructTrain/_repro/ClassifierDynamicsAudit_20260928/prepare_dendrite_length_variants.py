#!/usr/bin/env python3
"""Create matched short/medium/long class-2 dendrite replays.

Only the second input dendrite of class 2 is moved.  Its active excitatory
synapse count, synapse parameter records, training pattern, neuron parameters,
and all other class/dendrite structures stay fixed.  The script derives six
On/Off clones from the already-audited competition pair.
"""

from __future__ import annotations

import copy
import argparse
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASES = {
    "on": HERE / "NSpikeClassifier_AllProbesCompetition_DynamicsOn_Threshold0006_20260928",
    "off": HERE / "NSpikeClassifier_AllProbesCompetition_DynamicsOff_Threshold0006_20260928",
}
VARIANTS = {"short": 3, "medium": 8, "long": 17}
OUTPUT_ROOT = HERE / "NSpikeDendriteLengthAudit_20260928"
TRAINER_NAME = "NeuronTrainer2"
BRANCH = 2
OLD_LENGTH = 17
MODEL_PREFIX = f"SpikeClassifier.{TRAINER_NAME}.Neuron."
SOURCE_NAME = f"SpikeClassifier.{TRAINER_NAME}.Source{BRANCH}"
RECORDER_NAME = "ClassifierDynamicsRecorder"
RECORDER_SIGNAL_ALIAS = "class2_dendrite_input2"


def property_node(component: ET.Element, name: str) -> ET.Element:
    node = component.find(f"./Parameters/{name}")
    if node is None:
        raise ValueError(f"{component.tag} has no {name} parameter")
    return node


def trainer_and_neuron(root: ET.Element) -> tuple[ET.Element, ET.Element]:
    for trainer in root.iter():
        if trainer.tag == TRAINER_NAME and trainer.get("Class") == "NNeuronTrainer":
            neuron = trainer.find("./Components/Neuron")
            if neuron is None:
                break
            return trainer, neuron
    raise ValueError(f"Could not find {TRAINER_NAME}.Neuron")


def rewrite_links(root: ET.Element, old_prefix: str, new_prefix: str) -> None:
    links = root.find("./Model/Links")
    if links is None:
        return
    for link in links.findall("./elem"):
        # Move only links that touch an excitatory synapse. Cable/channel links
        # keep their original topology and are rebuilt by NPulseNeuron on load.
        sides = [side for side in link if (side.text or "").strip()]
        if any(".ExcSynapse" in side.text for side in sides):
            for side in sides:
                side.text = side.text.replace(old_prefix, new_prefix)
        # Keep the probe attached to the active tip after changing its length.
        for side in sides:
            if side.text.endswith(f"{old_prefix}SumPotential"):
                side.text = side.text.replace(old_prefix, new_prefix)


def move_active_synapses(neuron: ET.Element, old_len: int, new_len: int) -> int:
    components = neuron.find("./Components")
    if components is None:
        raise ValueError("Neuron has no Components")
    old = components.find(f"./Dendrite{BRANCH}_{old_len}")
    target = components.find(f"./Dendrite{BRANCH}_{new_len}")
    if old is None or target is None:
        raise ValueError(f"Missing dendrite component for move {old_len} -> {new_len}")
    count = int((property_node(old, "NumExcitatorySynapses").text or "1").strip())
    if new_len == old_len:
        return count

    old_components = old.find("./Components")
    target_components = target.find("./Components")
    if old_components is None or target_components is None:
        raise ValueError("Dendrite component has no child list")

    source_synapses = [
        child for child in list(old_components)
        if re.fullmatch(r"ExcSynapse\d+", child.tag)
    ]
    if len(source_synapses) != count:
        raise ValueError(f"Expected {count} active synapses, found {len(source_synapses)}")

    # Preserve synapse component properties while placing the same active set
    # at the new tip. The target membrane keeps its own channel and geometry.
    for child in list(target_components):
        if re.fullmatch(r"ExcSynapse\d+", child.tag):
            target_components.remove(child)
    for synapse in source_synapses:
        target_components.append(copy.deepcopy(synapse))
    property_node(target, "NumExcitatorySynapses").text = str(count)

    # Leave one default, unconnected synapse on the former tip, matching the
    # ordinary inactive segments along the branch.
    for child in list(old_components):
        if re.fullmatch(r"ExcSynapse\d+", child.tag) and child.tag != "ExcSynapse1":
            old_components.remove(child)
    property_node(old, "NumExcitatorySynapses").text = "1"
    return count


def set_vector(neuron: ET.Element, field: str, values: list[int]) -> None:
    node = property_node(neuron, field)
    node.text = "\n".join(str(value) for value in values)
    if field == "NumDendriteMembranePartsVec":
        node.set("Size", str(len(values)))
    elif field in ("TrainingDendIndexes", "TrainingSynapsisNum"):
        node.set("Rows", str(len(values)))
        node.set("Cols", "1")


def set_file_input(root: ET.Element) -> None:
    for classifier in root.iter():
        if classifier.tag == "SpikeClassifier" and classifier.get("Class") == "NSpikeClassifier":
            prop = property_node(classifier, "DataFromFile")
            prop.text = "1"
            return
    raise ValueError("Could not find NSpikeClassifier")


def retarget_dendrite_probe(model_root: ET.Element, length: int) -> None:
    model = model_root.find("./Model")
    links = model.find("./Links") if model is not None else None
    if links is None:
        raise ValueError("Model has no global Links section")

    recorder_probe_found = False
    target_text = f"{MODEL_PREFIX}Dendrite{BRANCH}_{length}"
    for existing in links.findall("./elem"):
        item = existing.find("./Item")
        connector = existing.find("./Connector")
        if (item is not None and connector is not None and connector.text == RECORDER_NAME
                and item.get("Name") == "SumPotential"
                and item.text == f"{MODEL_PREFIX}Dendrite{BRANCH}_{OLD_LENGTH}"):
            item.text = target_text
            recorder_probe_found = True
            break
    if not recorder_probe_found:
        raise ValueError(f"Could not find existing {RECORDER_SIGNAL_ALIAS} recorder link")


def write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="\t")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def create_clone(mode: str, label: str, length: int, output_root: Path) -> Path:
    source = BASES[mode]
    target_dir = output_root / f"NSpikeClassifier_Class2_{label}_D{length}_{mode.title()}_20260928"
    if target_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing experiment clone: {target_dir}")
    target_dir.mkdir(parents=True)
    for name in ("Project.ini", "Interface.xml", "Model_00.xml", "Parameters_00.xml", "input_data.txt", "expected_classes.csv", "History.xml"):
        if (source / name).is_file():
            shutil.copy2(source / name, target_dir / name)

    for filename in ("Model_00.xml", "Parameters_00.xml"):
        file_path = target_dir / filename
        tree = ET.parse(file_path)
        root = tree.getroot()
        trainer, neuron = trainer_and_neuron(root)
        lengths = [int(value) for value in property_node(neuron, "NumDendriteMembranePartsVec").text.split()]
        old_len = lengths[BRANCH - 1]
        synapses = [int(value) for value in property_node(neuron, "TrainingSynapsisNum").text.split()]
        count = move_active_synapses(neuron, old_len, length)
        lengths[BRANCH - 1] = length
        set_vector(neuron, "NumDendriteMembranePartsVec", lengths)
        indexes = [int(value) for value in property_node(neuron, "TrainingDendIndexes").text.split()]
        indexes[BRANCH - 1] = length
        set_vector(neuron, "TrainingDendIndexes", indexes)
        if synapses[BRANCH - 1] != count:
            raise ValueError("Active branch synapse count does not match training metadata")
        # Do not let the class-2 Trainer retrain this fixed morphology during a
        # response replay. The source project already has IsNeedToTrain=0.
        set_file_input(root)
        rewrite_links(root, f"{MODEL_PREFIX}Dendrite{BRANCH}_{old_len}.", f"{MODEL_PREFIX}Dendrite{BRANCH}_{length}.")
        if filename == "Model_00.xml":
            retarget_dendrite_probe(root, length)
        for n in root.iter():
            if n.tag == "FileName" and n.text and n.text.endswith(".csv"):
                n.text = f"Class2_{label}_D{length}_{mode.title()}.csv"
        write_xml(tree, file_path)

    ini = target_dir / "Project.ini"
    text = ini.read_text(encoding="utf-8")
    text = text.replace("<ProjectAutoSaveModelTimeInterval>10</ProjectAutoSaveModelTimeInterval>", "<ProjectAutoSaveModelTimeInterval>10</ProjectAutoSaveModelTimeInterval>")
    text = re.sub(r"(<ProjectName>).*?(</ProjectName>)", rf"\g<1>{target_dir.name}\g<2>", text, count=1, flags=re.DOTALL)
    ini.write_text(text, encoding="utf-8")
    (target_dir / "README.md").write_text(
        f"# {target_dir.name}\n\n"
        f"Matched class-2 branch-length replay cloned from the {mode.upper()} competition control. "
        f"Only branch 2 length changed from {OLD_LENGTH} to {length}; its {count} connected excitatory synapses, "
        "their saved parameters, all other branches, neuron physical parameters, and input file are held fixed. "
        "The class-2 trainer remains completed. The recorder adds the changed branch tip SumPotential.\n\n"
        "Run from this directory: `NeuroModelerConsole.exe -c Project.ini -s -t 8.1 -x -S`.\n",
        encoding="utf-8",
    )
    return target_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modes", nargs="+", choices=tuple(BASES), default=list(BASES))
    parser.add_argument("--variants", nargs="+", choices=tuple(VARIANTS), default=list(VARIANTS))
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    for mode in args.modes:
        source = BASES[mode]
        if not source.is_dir():
            raise FileNotFoundError(source)
        for label in args.variants:
            length = VARIANTS[label]
            print(create_clone(mode, label, length, args.output_root))


if __name__ == "__main__":
    main()

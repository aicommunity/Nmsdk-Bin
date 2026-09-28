#!/usr/bin/env python3
"""Prepare paired fixed-topology replays with different synapse counts.

Only class 2, branch 2 is changed. Its dendrite remains length 17 while the
connected excitatory synapse count is reduced from the trained value. All
remaining synapses keep their saved parameters and continue to receive Source2.
"""

from __future__ import annotations

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
DEFAULT_OUTPUT_ROOT = HERE / "NSpikeSynapseCountAudit_20260928"
BRANCH = 2
DENDRITE_LENGTH = 17
TRAINER_NAME = "NeuronTrainer2"
NEURON_PREFIX = f"SpikeClassifier.{TRAINER_NAME}.Neuron."
DENDRITE_NAME = f"Dendrite{BRANCH}_{DENDRITE_LENGTH}"
DENDRITE_PATH = NEURON_PREFIX + DENDRITE_NAME
SYNAPSE_RE = re.compile(r"ExcSynapse(\d+)$")
COUNTS = (6, 12, 24, 37)
RUN_SECONDS = 8.1


def set_text(parent: ET.Element, path: str, value: str) -> None:
    node = parent.find(path)
    if node is None:
        raise ValueError(f"Missing XML node {path}")
    node.text = value


def find_neuron(root: ET.Element) -> ET.Element:
    for trainer in root.iter(TRAINER_NAME):
        if trainer.get("Class") != "NNeuronTrainer":
            continue
        neuron = trainer.find("./Components/Neuron")
        if neuron is not None:
            return neuron
    raise ValueError(f"Could not find {TRAINER_NAME}.Neuron")


def exc_synapses(dendrite: ET.Element) -> list[ET.Element]:
    components = dendrite.find("./Components")
    if components is None:
        raise ValueError(f"{DENDRITE_NAME} has no Components")
    found = [child for child in list(components) if SYNAPSE_RE.fullmatch(child.tag)]
    found.sort(key=lambda node: int(SYNAPSE_RE.fullmatch(node.tag).group(1)))
    return found


def trim_neuron_structure(root: ET.Element, target_count: int) -> set[str]:
    neuron = find_neuron(root)
    dendrite = neuron.find(f"./Components/{DENDRITE_NAME}")
    if dendrite is None:
        raise ValueError(f"Missing active branch {DENDRITE_NAME}")

    active = exc_synapses(dendrite)
    old_count = int((dendrite.find("./Parameters/NumExcitatorySynapses").text or "0").strip())
    if len(active) != old_count:
        raise ValueError(f"Active synapse components ({len(active)}) != saved count ({old_count})")
    if target_count < 1 or target_count > old_count:
        raise ValueError(f"Count {target_count} must be between 1 and {old_count}")

    removed = {node.tag for node in active[target_count:]}
    components = dendrite.find("./Components")
    for node in active[target_count:]:
        components.remove(node)
    set_text(dendrite, "./Parameters/NumExcitatorySynapses", str(target_count))

    counts_node = neuron.find("./Parameters/TrainingSynapsisNum")
    if counts_node is None:
        raise ValueError("Neuron has no TrainingSynapsisNum metadata")
    counts = [int(value) for value in (counts_node.text or "").split()]
    if len(counts) < BRANCH:
        raise ValueError("TrainingSynapsisNum has fewer entries than the branch index")
    counts[BRANCH - 1] = target_count
    counts_node.text = "\n".join(map(str, counts))
    if counts_node.get("Rows") is not None:
        counts_node.set("Rows", str(len(counts)))
    return {f"{DENDRITE_PATH}.{name}" for name in removed}


def remove_dangling_synapse_links(root: ET.Element, removed_paths: set[str]) -> None:
    links = root.find("./Model/Links")
    if links is None:
        raise ValueError("Model has no Links section")

    for link in list(links.findall("./elem")):
        item = link.find("./Item")
        connector_nodes = link.findall("./Connector")
        item_removed = item is not None and (item.text or "").strip() in removed_paths
        if item_removed:
            links.remove(link)
            continue
        for connector in list(connector_nodes):
            if (connector.text or "").strip() in removed_paths:
                link.remove(connector)
        if link.find("./Item") is None or not link.findall("./Connector"):
            links.remove(link)

    links.set("Size", str(len(links.findall("./elem"))))
    leftovers = [
        (side.text or "").strip()
        for side in links.iter()
        if side.tag in ("Item", "Connector") and (side.text or "").strip() in removed_paths
    ]
    if leftovers:
        raise ValueError(f"Removed synapses still have links: {leftovers[:3]}")


def set_file_input(root: ET.Element) -> None:
    for classifier in root.iter("SpikeClassifier"):
        if classifier.get("Class") == "NSpikeClassifier":
            set_text(classifier, "./Parameters/DataFromFile", "1")
            return
    raise ValueError("Could not find NSpikeClassifier")


def patch_project(path: Path, name: str) -> None:
    data = path.read_text(encoding="utf-8-sig")
    replacements = {
        "ProjectName": name,
        "MaxCalculationModelTime": str(RUN_SECONDS),
        "ProjectAutoSaveFlag": "1",
        "ProjectAutoSaveModelTimeInterval": "10",
    }
    for tag, value in replacements.items():
        data, count = re.subn(
            rf"(<{tag}>).*?(</{tag}>)",
            lambda match: match.group(1) + value + match.group(2),
            data,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError(f"Expected one <{tag}> element in {path}; found {count}")
    path.write_text(data, encoding="utf-8")


def write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="\t")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def create_clone(mode: str, target_count: int, output_root: Path) -> Path:
    source = BASES[mode]
    if not source.is_dir():
        raise FileNotFoundError(source)
    name = f"NSpikeClassifier_Class2_D17_Syn{target_count}_{mode.title()}_20260928"
    destination = output_root / name
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing experiment clone: {destination}")
    destination.mkdir(parents=True)

    for filename in (
        "Project.ini", "Interface.xml", "Model_00.xml", "Parameters_00.xml",
        "input_data.txt", "expected_classes.csv",
    ):
        shutil.copy2(source / filename, destination / filename)
    patch_project(destination / "Project.ini", name)

    for filename in ("Model_00.xml", "Parameters_00.xml"):
        path = destination / filename
        tree = ET.parse(path)
        root = tree.getroot()
        set_file_input(root)
        removed_paths = trim_neuron_structure(root, target_count)
        if filename == "Model_00.xml":
            remove_dangling_synapse_links(root, removed_paths)
            for node in root.iter("FileName"):
                if node.text and node.text.endswith(".csv"):
                    node.text = f"Class2_D17_Syn{target_count}_{mode.title()}.csv"
        write_xml(tree, path)

    (destination / "README.md").write_text(
        f"# {name}\n\n"
        f"Fixed-topology class-2 replay from the {mode.upper()} competition control. "
        f"Branch 2 remains length {DENDRITE_LENGTH}; its active excitatory synapse count "
        f"is reduced from 37 to {target_count}. Retained synapses keep their saved physical "
        "parameters and remain connected to the same `Source2` input. Other dendrites, "
        "classifier parameters, input file and lateral-inhibition setting are unchanged. "
        "Training is disabled.\n\n"
        f"Run: `NeuroModelerConsole.exe -c Project.ini -s -t {RUN_SECONDS} -x -S`.\n",
        encoding="utf-8",
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--counts", nargs="+", type=int, default=list(COUNTS))
    parser.add_argument("--modes", nargs="+", choices=tuple(BASES), default=list(BASES))
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    for count in args.counts:
        for mode in args.modes:
            print(create_clone(mode, count, args.output_root))


if __name__ == "__main__":
    main()

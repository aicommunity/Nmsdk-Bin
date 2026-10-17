#!/usr/bin/env python3
"""Create paired inhibition-on/off probes from saved trained classifiers."""

from __future__ import annotations

import csv
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
AUDIT_DIR = Path(__file__).resolve().parent / "DetailedSignals_20260927"
SOURCES = {
    "NSpikeClassifier": ROOT / "Bin/Configs/SpikeSamples/StructTrain/_repro/ClassifierAudit/NSpikeClassifier_InhibitionDynamicsTrace_20260927",
    "NClassifier": ROOT / "Bin/Configs/SpikeSamples/StructTrain/_repro/ClassifierAudit/NClassifier_TrainingPatternRecognitionSmoke_20260927",
}


def direct_component(parent: ET.Element, tag: str) -> ET.Element:
    node = parent.find(f"./Components/{tag}")
    if node is None:
        raise ValueError(f"Component {tag} was not found")
    return node


def property_node(component: ET.Element, name: str, type_name: str, ptype: int = 257) -> ET.Element:
    params = component.find("./Parameters")
    if params is None:
        params = ET.SubElement(component, "Parameters")
    node = params.find(name)
    if node is None:
        node = ET.SubElement(params, name, {"Type": type_name, "PType": str(ptype), "IoType": "17"})
    return node


def set_value(component: ET.Element, name: str, value: str, type_name: str = "bool") -> None:
    property_node(component, name, type_name).text = value


def matrix_values(component: ET.Element, name: str) -> tuple[int, int, list[list[float]]]:
    node = component.find(f"./Parameters/{name}")
    if node is None:
        raise ValueError(f"Property {name} was not found")
    rows, cols = int(node.attrib["Rows"]), int(node.attrib["Cols"])
    values = [float(v) for v in (node.text or "").split()]
    if len(values) != rows * cols:
        raise ValueError(f"{name} declares {rows}x{cols}, contains {len(values)} values")
    return rows, cols, [values[r * cols:(r + 1) * cols] for r in range(rows)]


def create_probe_inputs(classifier: ET.Element, class_count: int, examples_per_class: int) -> list[tuple[int, list[float]]]:
    rows, cols, matrix = matrix_values(classifier, "TrainingPatterns")
    if rows < class_count * examples_per_class:
        raise ValueError("TrainingPatterns does not contain a complete row group per class")
    selected = [(class_index + 1, matrix[class_index * examples_per_class])
                for class_index in range(class_count)]
    if class_count >= 2:
        midpoint = [(a + b) / 2.0 for a, b in zip(matrix[0], matrix[examples_per_class])]
        selected.append((0, midpoint))
    if any(len(row) != cols for _, row in selected):
        raise ValueError("Prototype row size mismatch")
    return selected


def add_link(links: ET.Element, source: str, destination: str = "ClassifierDynamicsRecorder",
             source_connector: str = "Output") -> None:
    link = ET.SubElement(links, "elem", {"Type": "ULink"})
    ET.SubElement(link, "Item", {"Type": "ULinkSide", "Index": "-1", "Name": source_connector}).text = source
    ET.SubElement(link, "Connector", {"Type": "ULinkSide", "Index": "-1", "Name": "Signals"}).text = destination


def append_probe_signals(classifier_name: str, classifier: ET.Element,
                         recorder_links: ET.Element, names: list[str]) -> None:
    classifier_instance = "SpikeClassifier" if classifier_name == "NSpikeClassifier" else "Classifier"
    if classifier_name == "NSpikeClassifier":
        trainers = [c for c in classifier.findall("./Components/*") if re.fullmatch(r"NeuronTrainer\d+", c.tag)]
    else:
        trainers = [c for c in classifier.findall("./Components/*") if re.fullmatch(r"NeuronTrainer\d+_\d+", c.tag)]

    # Observe all per-example neurons for NClassifier and all class neurons for NSpikeClassifier.
    for trainer in trainers:
        neuron = trainer.find("./Components/Neuron")
        if neuron is None:
            continue
        base = f"{classifier_instance}.{trainer.tag}.Neuron"
        add_link(recorder_links, f"{base}.LTZone")
        names.append(f"{trainer.tag}_ltz")
        add_link(recorder_links, f"{base}.Soma1", source_connector="SumPotential")
        names.append(f"{trainer.tag}_soma")

        terminal_segments: dict[int, tuple[int, str]] = {}
        for child in neuron.findall("./Components/*"):
            match = re.fullmatch(r"Dendrite(\d+)_(\d+)", child.tag)
            if not match:
                continue
            input_index, segment_index = int(match.group(1)), int(match.group(2))
            if input_index not in terminal_segments or segment_index > terminal_segments[input_index][0]:
                terminal_segments[input_index] = (segment_index, child.tag)
        for input_index, (_, segment_name) in sorted(terminal_segments.items()):
            add_link(recorder_links, f"{base}.{segment_name}", source_connector="SumPotential")
            names.append(f"{trainer.tag}_dendrite{input_index}_terminal")

    # Read the OR neurons' response and both sides of the lateral synapses.
    if classifier_name == "NClassifier":
        or_neurons = [c for c in classifier.findall("./Components/*") if re.fullmatch(r"OrNeuron\d+", c.tag)]
        for or_neuron in or_neurons:
            base = f"{classifier_instance}.{or_neuron.tag}"
            add_link(recorder_links, f"{base}.LTZone")
            names.append(f"{or_neuron.tag}_ltz")
            add_link(recorder_links, f"{base}.Soma1", source_connector="SumPotential")
            names.append(f"{or_neuron.tag}_soma")
            soma = or_neuron.find("./Components/Soma1")
            if soma is not None:
                for synapse in soma.findall("./Components/*"):
                    if not synapse.tag.startswith("InhSynapse"):
                        continue
                    synapse_base = f"{base}.Soma1.{synapse.tag}"
                    add_link(recorder_links, synapse_base, source_connector="OutInCopy")
                    names.append(f"{or_neuron.tag}_{synapse.tag}_input")
                    add_link(recorder_links, synapse_base)
                    names.append(f"{or_neuron.tag}_{synapse.tag}_output")
                if soma.find("./Components/InhChannel") is not None:
                    add_link(recorder_links, f"{base}.Soma1.InhChannel")
                    names.append(f"{or_neuron.tag}_inh_channel")
    else:
        # NSpikeClassifier's own trained neurons already appear in `trainers` above.
        for trainer in trainers:
            neuron = classifier.find(f"./Components/{trainer.tag}/Components/Neuron")
            if neuron is None:
                continue
            for soma in neuron.findall("./Components/*"):
                if not re.fullmatch(r"Soma\d+", soma.tag):
                    continue
                base = f"{classifier_instance}.{trainer.tag}.Neuron.{soma.tag}"
                suffix = f"dendrite{soma.tag[4:]}"
                for synapse in soma.findall("./Components/*"):
                    if not synapse.tag.startswith("InhSynapse"):
                        continue
                    synapse_base = f"{base}.{synapse.tag}"
                    add_link(recorder_links, synapse_base, source_connector="OutInCopy")
                    names.append(f"{trainer.tag}_{suffix}_{synapse.tag}_input")
                    add_link(recorder_links, synapse_base)
                    names.append(f"{trainer.tag}_{suffix}_{synapse.tag}_output")
                if soma.find("./Components/InhChannel") is not None:
                    add_link(recorder_links, f"{base}.InhChannel")
                    names.append(f"{trainer.tag}_{suffix}_inh_channel")


def write_recorder_parameters(parameters_components: ET.Element, names: list[str]) -> None:
    recorder = ET.SubElement(parameters_components, "ClassifierDynamicsRecorder", {"Class": "NClassifierDynamicsRecorder"})
    params = ET.SubElement(recorder, "Parameters")
    values = [
        ("Activity", "bool", "1"),
        ("MaxCalculationDuration", "__int64", "-1"),
        ("CalculationDurationThreshold", "__int64", "-1"),
        ("Coord", "MVector<double>", "0 0 0"),
        ("SignalNamesCsv", "std::string", ",".join(names)),
        ("SavePath", "std::string", "ClassifierDynamics"),
        ("FileName", "std::string", "signals.csv"),
        ("SampleInterval", "double", "0.0005"),
        ("FlushInterval", "double", "0.01"),
        ("AppendMode", "bool", "0"),
        ("Enable", "bool", "1"),
    ]
    for name, type_name, text in values:
        attrib = {"Type": type_name, "PType": "257", "IoType": "17"}
        if name == "Coord":
            attrib["Size"] = "3"
        ET.SubElement(params, name, attrib).text = text
    ET.SubElement(recorder, "Components")


def create_clone(classifier_name: str, source: Path, run_name: str, use_inhibition: bool) -> None:
    destination = AUDIT_DIR / run_name
    if destination.exists():
        if not (destination / "expected_classes.csv").is_file():
            raise FileExistsError(f"Refusing to overwrite an unrecognized experiment directory: {destination}")
    else:
        destination.mkdir(parents=True)
    for filename in ("Project.ini", "Model_00.xml", "Parameters_00.xml", "Interface.xml", "input_data.txt",
                     "README.md", "Description.rtf", "History.xml"):
        path = source / filename
        if path.is_file():
            shutil.copy2(path, destination / filename)

    project_path = destination / "Project.ini"
    project_text = project_path.read_text(encoding="utf-8-sig")
    project_text = re.sub(r"<ProjectName>.*?</ProjectName>", f"<ProjectName>{run_name}</ProjectName>", project_text)
    project_text = re.sub(r"<ProjectAutoSaveModelTimeInterval>.*?</ProjectAutoSaveModelTimeInterval>",
                          "<ProjectAutoSaveModelTimeInterval>10</ProjectAutoSaveModelTimeInterval>", project_text)
    project_path.write_text(project_text, encoding="utf-8")

    model_path = destination / "Model_00.xml"
    model_tree = ET.parse(model_path)
    model_root = model_tree.getroot()
    model = model_root.find("./Model")
    model_components = model.find("./Components") if model is not None else None
    if model is None or model_components is None:
        raise ValueError(f"Unexpected Model_00.xml structure in {source}")
    classifier_instance = "SpikeClassifier" if classifier_name == "NSpikeClassifier" else "Classifier"
    classifier = direct_component(model, classifier_instance)

    params_path = destination / "Parameters_00.xml"
    params_tree = ET.parse(params_path)
    params_root = params_tree.getroot()
    params_model = params_root.find("./Model")
    params_components = params_model.find("./Components") if params_model is not None else None
    if params_components is None:
        raise ValueError(f"Unexpected Parameters_00.xml structure in {source}")
    params_classifier = direct_component(params_model, classifier_instance)

    set_value(params_classifier, "DataFromFile", "1")
    set_value(params_classifier, "IsNeedToTrain", "0")
    set_value(params_classifier, "UseLateralInhibition", "1" if use_inhibition else "0")
    if classifier_name == "NSpikeClassifier":
        class_count_node = params_classifier.find("./Parameters/NumNeurons")
        class_count = int(class_count_node.text)
        examples_per_class = 1
    else:
        class_count_node = params_classifier.find("./Parameters/NumClasses")
        class_count = int(class_count_node.text)
        size_node = params_classifier.find("./Parameters/SizeTrainingSet")
        examples_per_class = int(size_node.text)

    probes = create_probe_inputs(params_classifier, class_count, examples_per_class)
    first = params_classifier.find("./Parameters/InputPattern")
    if first is not None:
        first.attrib["Rows"], first.attrib["Cols"] = str(len(probes[0][1])), "1"
        first.text = "\n".join(format(value, ".17g") for value in probes[0][1])
    (destination / "input_data.txt").write_text(
        "".join(" ".join(format(value, ".17g") for value in row) + "\n" for _, row in probes),
        encoding="ascii")
    with (destination / "expected_classes.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["probe_index", "expected_class", "source"])
        for i, (label, row) in enumerate(probes):
            writer.writerow([i, label, "midpoint(class1,class2)" if label == 0 else "saved_training_pattern"])

    links = model.find("./Links")
    if links is None:
        raise ValueError(f"No ULinksList in {source}/Model_00.xml")
    names: list[str] = []
    append_probe_signals(classifier_name, classifier, links, names)
    links.set("Size", str(len(links.findall("./elem"))))

    # The model file contains topology; the companion parameter file supplies recorder settings.
    model_recorder = ET.SubElement(model_components, "ClassifierDynamicsRecorder", {"Class": "NClassifierDynamicsRecorder"})
    ET.SubElement(model_recorder, "Components")
    write_recorder_parameters(params_components, names)
    model_tree.write(model_path, encoding="utf-8", xml_declaration=False)
    params_tree.write(params_path, encoding="utf-8", xml_declaration=False)

    (destination / "README.md").write_text(
        f"# {run_name}\n\n"
        f"Paired synthetic dynamics replay for `{classifier_name}`. This clone uses stored class training rows as pure temporal prototypes and their class-1/class-2 midpoint as an intentionally ambiguous probe. `UseLateralInhibition={1 if use_inhibition else 0}` is the only classifier-topology difference in the pair. The saved trained neuron structures and physical parameters are preserved. The recorder captures inhibitory synapse `OutInCopy` inputs separately from outputs, for every input dendrite.\n\n"
        "Run from this directory with the Release console: `NeuroModelerConsole.exe -c Project.ini -s -t 16 -x -S`. "
        "The recorder writes signed signals every 0.5 ms to `ClassifierDynamics/signals.csv`; `expected_classes.csv` labels the three pure prototypes and the midpoint (0).\n",
        encoding="utf-8")


def main() -> None:
    for classifier_name, source in SOURCES.items():
        if not source.is_dir():
            raise FileNotFoundError(source)
        create_clone(classifier_name, source, f"{classifier_name}_Synthetic_InhibitionOn_DetailedSignals", True)
        create_clone(classifier_name, source, f"{classifier_name}_Synthetic_InhibitionOff_DetailedSignals", False)


if __name__ == "__main__":
    main()

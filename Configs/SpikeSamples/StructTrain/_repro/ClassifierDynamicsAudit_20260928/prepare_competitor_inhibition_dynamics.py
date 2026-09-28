#!/usr/bin/env python3
"""Clone the 0.006 synthetic class-3 probe and record the active class-1/2 pair."""

from __future__ import annotations

import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parent
RUN_SECONDS = 8.01
STATES = ("On", "Off")


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


def signal_sources(model: ET.Element) -> list[tuple[str, str, str]]:
    signals = [(f"input{i}", "Output", f"SpikeClassifier.Source{i}") for i in range(1, 6)]
    for class_index in (1, 2):
        neuron = model.find(
            f"./Components/SpikeClassifier/Components/NeuronTrainer{class_index}/Components/Neuron"
        )
        if neuron is None:
            raise ValueError(f"NeuronTrainer{class_index}.Neuron missing")
        lengths_text = neuron.findtext("./Parameters/NumDendriteMembranePartsVec")
        if not lengths_text:
            raise ValueError(f"NeuronTrainer{class_index} lacks dendrite length vector")
        lengths = [int(value) for value in lengths_text.split()]
        if len(lengths) != 5:
            raise ValueError(f"Expected five lengths for class {class_index}; got {lengths}")

        prefix = f"SpikeClassifier.NeuronTrainer{class_index}.Neuron"
        signals.append((f"class{class_index}_ltz_potential", "OutputPotential", f"{prefix}.LTZone"))
        for soma_index in range(1, 6):
            soma = f"{prefix}.Soma{soma_index}"
            signals.extend([
                (f"class{class_index}_soma{soma_index}", "SumPotential", soma),
                (f"class{class_index}_inh_channel{soma_index}", "Output", f"{soma}.InhChannel"),
                (f"class{class_index}_inh_channel_input{soma_index}", "SumChannelInput",
                 f"{soma}.InhChannel"),
                (f"class{class_index}_inh_syn1{soma_index}", "Output", f"{soma}.InhSynapse1"),
                (f"class{class_index}_inh_syn1input{soma_index}", "OutInCopy", f"{soma}.InhSynapse1"),
                (f"class{class_index}_inh_syn2{soma_index}", "Output", f"{soma}.InhSynapse2"),
                (f"class{class_index}_inh_syn2input{soma_index}", "OutInCopy", f"{soma}.InhSynapse2"),
                (f"class{class_index}_dendrite_input{soma_index}", "SumPotential",
                 f"{prefix}.Dendrite{soma_index}_{lengths[soma_index - 1]}"),
            ])
    return signals


def append_signals(model: ET.Element, aliases: list[str], sources: list[tuple[str, str, str]]) -> None:
    links = model.find("./Links")
    if links is None:
        raise ValueError("Model.Links missing")
    for alias, endpoint, source in sources:
        if alias in aliases:
            raise ValueError(f"Duplicate recorder alias: {alias}")
        aliases.append(alias)
        link = ET.SubElement(links, "elem", {"Type": "ULink"})
        ET.SubElement(link, "Item", {"Type": "ULinkSide", "Index": "-1", "Name": endpoint}).text = source
        ET.SubElement(link, "Connector", {"Type": "ULinkSide", "Index": "-1", "Name": "Signals"}).text = "ClassifierDynamicsRecorder"
    links.set("Size", str(len(links.findall("./elem"))))


def prepare(state: str) -> Path:
    source = AUDIT_DIR / f"NSpikeClassifier_Synthetic_Outputs{state}_Threshold0006_20260928"
    name = f"NSpikeClassifier_AllProbesCompetition_Dynamics{state}_Threshold0006_20260928"
    output = AUDIT_DIR / name
    output.mkdir(parents=True, exist_ok=True)
    for filename in ("Project.ini", "Model_00.xml", "Parameters_00.xml", "Interface.xml", "expected_classes.csv", "input_data.txt"):
        shutil.copy2(source / filename, output / filename)

    # Keep all four rows so detailed traces can be reconciled against the
    # classifier's own output_data.txt windows without an offset assumption.
    patch_project(output / "Project.ini", name)

    for filename in ("Model_00.xml", "Parameters_00.xml"):
        path = output / filename
        tree = ET.parse(path)
        root = tree.getroot()
        model = root.find("./Model")
        if model is None:
            raise ValueError(f"Model node missing in {path}")
        classifier = model.find("./Components/SpikeClassifier")
        if classifier is None:
            raise ValueError("SpikeClassifier missing")
        set_text(classifier, "./Parameters/DataFromFile", "1")
        recorder = model.find("./Components/ClassifierDynamicsRecorder")
        if recorder is None:
            raise ValueError("ClassifierDynamicsRecorder missing")
        aliases = [value for value in (recorder.findtext("./Parameters/SignalNamesCsv") or "").split(",") if value]
        sources = signal_sources(model)
        set_text(recorder, "./Parameters/SignalNamesCsv", ",".join(aliases + [item[0] for item in sources]))
        set_text(recorder, "./Parameters/SavePath", "ClassifierDynamicsCompetition")
        set_text(recorder, "./Parameters/FileName", f"Class12Competition_{state}_Threshold0006.csv")
        if filename == "Model_00.xml":
            append_signals(model, aliases, sources)
        write_xml(tree, path)

    (output / "README.md").write_text(
        f"# Synthetic competition dynamics: lateral inhibition {state}\n\n"
        "Clone of the verified 0.006 threshold replay, retaining all four synthetic input patterns. "
        "The trained structures and all physical parameters are unchanged. `DataFromFile` is set to 1 "
        "in the experiment clone because completed source replays persist it as 0 after EOF. This probe captures the "
        "source class LTZone outputs, target somas, input dendrites, inhibitory synapse 1/2 direct inputs "
        "(`OutInCopy`) and conductance outputs, and inhibitory channel outputs/inputs. In this wiring, "
        "class 1 drives `InhSynapse1` and class 3 drives `InhSynapse2` on class 2.\n\n"
        f"Run: `NeuroModelerConsole.exe -c Project.ini -s -t {RUN_SECONDS} -x -S`.\n",
        encoding="utf-8",
    )
    print(output)
    return output


if __name__ == "__main__":
    for mode in STATES:
        prepare(mode)

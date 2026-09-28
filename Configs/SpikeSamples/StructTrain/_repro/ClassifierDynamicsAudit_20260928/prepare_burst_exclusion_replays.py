#!/usr/bin/env python3
"""Create fixed-structure classifier replays with LTZone spike recording.

Only recognition thresholds and file-replay/recorder settings are changed.
No trained structures, synapses, or physical neuron parameters are optimized.
"""

from __future__ import annotations

import argparse
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
CLASSIFIER_AUDIT = HERE.parent / "ClassifierAudit"
NPCA_AUDIT = HERE
SYNAPSE_AUDIT = HERE / "NSpikeSynapseCountAudit_20260928"
COMPETITION_AUDIT = HERE
OUTPUT_ROOT = HERE.parent / "BurstReplayVerified_Rerun"
RECORDER_SEED = HERE / "NSpikeClassifier_Synthetic_OutputsOn_Threshold00085_20260928"

IRIS_SOURCE = CLASSIFIER_AUDIT / "NSpikeClassifier_TrainerPointerFix_Iris10_20260927"
IRIS_REPLAY_SOURCE = CLASSIFIER_AUDIT / "NSpikeClassifier_TrainerPointerFix_IrisReplay_20260927"
NCLASSIFIER_SOURCE = CLASSIFIER_AUDIT / "NClassifier_WorkingThresholdReplay_20260927"
NPCA_SOURCE = NPCA_AUDIT / "NPCAClassifier_OnePatternReplay_InitFix_20260928"

IRIS_SECONDS = 21.0
NCLASSIFIER_SECONDS = 6.0
NPCA_SECONDS = 60.0
FIXED_REPLAY_SECONDS = 8.1


def set_text(parent: ET.Element, path: str, value: str) -> None:
    node = parent.find(path)
    if node is None:
        raise ValueError(f"Missing XML node {path}")
    node.text = value


def copy_core(source: Path, destination: Path, filenames: tuple[str, ...]) -> None:
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    destination.mkdir(parents=True)
    for filename in filenames:
        path = source / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        shutil.copy2(path, destination / filename)


def patch_project(path: Path, name: str, seconds: float) -> None:
    text = path.read_text(encoding="utf-8-sig")
    for tag, value in {
        "ProjectName": name,
        "MaxCalculationModelTime": f"{seconds:g}",
        "ProjectAutoSaveFlag": "1",
        "ProjectAutoSaveModelTimeInterval": "10",
    }.items():
        text, count = re.subn(
            rf"(<{tag}>).*?(</{tag}>)",
            lambda match: match.group(1) + value + match.group(2),
            text,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError(f"Expected one <{tag}> in {path}; found {count}")
    path.write_text(text, encoding="utf-8")


def model_node(root: ET.Element) -> ET.Element:
    model = root.find("./Model")
    if model is None:
        raise ValueError("Serialized Model node is missing")
    return model


def set_replay_input(root: ET.Element) -> None:
    model = model_node(root)
    found = 0
    for component in model.iter():
        if component.get("Class") in {"NSpikeClassifier", "NClassifier"}:
            node = component.find("./Parameters/DataFromFile")
            if node is not None:
                node.text = "1"
                found += 1
    if not found:
        raise ValueError("No file-driven classifier was found")


def set_fixed_threshold(root: ET.Element, threshold: float) -> None:
    model = model_node(root)
    value = f"{threshold:.17g}"
    trainer_count = 0
    zone_count = 0
    for component in model.iter():
        classname = component.get("Class", "")
        params = component.find("./Parameters")
        if params is None:
            continue
        if classname == "NNeuronTrainer":
            for tag in ("LTZThreshold", "FixedLTZThreshold"):
                node = params.find(tag)
                if node is not None:
                    node.text = value
            use_fixed = params.find("UseFixedLTZThreshold")
            if use_fixed is not None:
                use_fixed.text = "1"
            trainer_count += 1
        if classname in {"NSpikeClassifier", "NClassifier"}:
            for tag in ("LTZThreshold", "FixedLTZThreshold"):
                node = params.find(tag)
                if node is not None:
                    node.text = value
        if classname == "NPulseLTZoneThreshold":
            node = params.find("Threshold")
            if node is None:
                raise ValueError(f"LTZone {component.tag} has no Threshold")
            node.text = value
            zone_count += 1
    if trainer_count == 0 or zone_count == 0:
        raise ValueError(f"Threshold patch found trainers={trainer_count}, LTZones={zone_count}")


def recorder_template(filename: str, signal_names: list[str]) -> ET.Element:
    seed = ET.parse(RECORDER_SEED / "Model_00.xml").getroot()
    component = model_node(seed).find("./Components/ClassifierDynamicsRecorder")
    if component is None:
        raise ValueError("Recorder template component missing")
    component = ET.fromstring(ET.tostring(component))
    set_text(component, "./Parameters/SignalNamesCsv", ",".join(signal_names))
    set_text(component, "./Parameters/SavePath", "")
    set_text(component, "./Parameters/FileName", filename)
    set_text(component, "./Parameters/Enable", "1")
    return component


def add_recorder(
    root: ET.Element,
    filename: str,
    signals: list[tuple[str, str]],
    connect: bool,
) -> None:
    """Add or reconfigure a recorder; signals contain (alias, source output path)."""
    model = model_node(root)
    components = model.find("./Components")
    links = model.find("./Links")
    if components is None or (connect and links is None):
        raise ValueError("Model Components/Links are missing")
    recorder = components.find("./ClassifierDynamicsRecorder")
    if recorder is None:
        recorder = recorder_template(filename, [alias for alias, _ in signals])
        components.append(recorder)
    else:
        set_text(recorder, "./Parameters/SignalNamesCsv", ",".join(alias for alias, _ in signals))
        set_text(recorder, "./Parameters/SavePath", "")
        set_text(recorder, "./Parameters/FileName", filename)
        set_text(recorder, "./Parameters/Enable", "1")

    if not connect:
        return

    # Remove only recorder destinations from prior fan-out links. A model link
    # can also carry neuron inputs, so deleting the whole link would disconnect
    # the classifier while replacing its diagnostic probe.
    for link in list(links.findall("./elem")):
        for connector in list(link.findall("./Connector")):
            if (
                connector.get("Name") == "Signals"
                and (connector.text or "").strip() == "ClassifierDynamicsRecorder"
            ):
                link.remove(connector)
        if not link.findall("./Connector"):
            links.remove(link)
    for alias, source in signals:
        link = ET.SubElement(links, "elem", {"Type": "ULink"})
        ET.SubElement(link, "Item", {
            "Type": "ULinkSide", "Index": "-1", "Name": "Output",
        }).text = source
        ET.SubElement(link, "Connector", {
            "Type": "ULinkSide", "Index": "-1", "Name": "Signals",
        }).text = "ClassifierDynamicsRecorder"
    links.set("Size", str(len(links.findall("./elem"))))
    recorder_links = [
        link for link in links.findall("./elem")
        if any(
            connector.get("Name") == "Signals"
            and (connector.text or "").strip() == "ClassifierDynamicsRecorder"
            for connector in link.findall("./Connector")
        )
    ]
    actual_sources = [
        (link.find("./Item").text or "").strip()
        for link in recorder_links
    ]
    expected_sources = [source for _, source in signals]
    if actual_sources != expected_sources:
        raise ValueError(
            "Recorder link order/source mismatch: "
            f"expected={expected_sources}, actual={actual_sources}"
        )


def add_nspike_signals(root: ET.Element) -> list[tuple[str, str]]:
    return [
        (f"class{index}_ltz", f"SpikeClassifier.NeuronTrainer{index}.Neuron.LTZone")
        for index in (1, 2, 3)
    ]


def add_nclassifier_signals(root: ET.Element) -> list[tuple[str, str]]:
    model = model_node(root)
    classifier = model.find("./Components/Classifier")
    if classifier is None:
        raise ValueError("NClassifier root component missing")
    components = classifier.find("./Components")
    if components is None:
        raise ValueError("NClassifier has no Components")
    signals: list[tuple[str, str]] = []
    trainers = sorted(
        (component.tag for component in components
         if component.get("Class") == "NNeuronTrainer"),
        key=lambda name: tuple(int(value) for value in re.findall(r"\d+", name)),
    )
    for trainer_name in trainers:
        signals.append((f"{trainer_name}_ltz", f"Classifier.{trainer_name}.Neuron.LTZone"))
    for class_index in (1, 2, 3):
        signals.append((f"or_class{class_index}_ltz", f"Classifier.OrNeuron{class_index}.LTZone"))
    if len(signals) <= 3:
        raise ValueError(f"Expected internal trainers plus three OR neurons, got {len(signals)}")
    return signals


def write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="\t")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def prepare_clone(
    source: Path,
    name: str,
    threshold: float,
    seconds: float,
    input_name: str,
    output_root: Path,
    signals_builder,
) -> Path:
    destination = output_root / name
    copy_names = ["Project.ini", "Interface.xml", "Model_00.xml", "Parameters_00.xml"]
    for filename in (
        "input_data.txt", "expected_classes.csv", "norm_matrix.txt", "testing_input.txt", "Description.rtf",
    ):
        if (source / filename).is_file():
            copy_names.append(filename)
    # NPCA reads its saved source matrix and will regenerate its output files.
    if source == NPCA_SOURCE and (source / "input_data.txt").exists():
        pass
    copy_core(source, destination, tuple(copy_names))
    patch_project(destination / "Project.ini", name, seconds)

    for filename in ("Model_00.xml", "Parameters_00.xml"):
        path = destination / filename
        tree = ET.parse(path)
        root = tree.getroot()
        set_fixed_threshold(root, threshold)
        if input_name != "NPCA":
            set_replay_input(root)
        signals = signals_builder(root)
        add_recorder(root, "signals.csv", signals,
                     connect=filename == "Model_00.xml")
        if filename == "Parameters_00.xml":
            # These replays must not perform structural training.
            for component in model_node(root).iter():
                if component.get("Class") == "NNeuronTrainer":
                    node = component.find("./Parameters/IsNeedToTrain")
                    if node is not None and node.text != "0":
                        raise ValueError(f"Unexpected training enabled on {component.tag}: {node.text}")
        write_xml(tree, path)

    (destination / "README.md").write_text(
        f"# {name}\n\n"
        f"Fixed-structure recognition replay cloned from `{source.name}`. The only neural "
        f"parameter changed is the LTZone threshold ({threshold:g}); trained synapse/dendrite "
        "structures and physical neuron parameters remain as saved. A passive recorder samples "
        "the named LTZone outputs every 0.5 ms so each response window can be checked for "
        "zero, one, or multiple rising edges. After EOF the classifier saves DataFromFile=0; "
        "prepare a fresh clone before repeating the file replay.\n\n"
        f"Run from this directory: `NeuroModelerConsole.exe -c Project.ini -s -t {seconds:g} -x -S`.\n",
        encoding="utf-8",
    )
    return destination


def prepare_iris(output_root: Path) -> list[Path]:
    return [prepare_clone(
        IRIS_SOURCE,
        "NSpikeClassifier_Iris10_Threshold00085_20260928",
        0.0085,
        IRIS_SECONDS,
        "Iris10",
        output_root,
        add_nspike_signals,
    )]


def prepare_iris_smoke(output_root: Path) -> list[Path]:
    return [prepare_clone(
        IRIS_REPLAY_SOURCE,
        "NSpikeClassifier_Iris3Prototypes_Threshold00085_20260928",
        0.0085,
        7.0,
        "Iris3Prototypes",
        output_root,
        add_nspike_signals,
    )]


def prepare_iris_no_recorder_control(output_root: Path) -> list[Path]:
    name = "NSpikeClassifier_Iris3Prototypes_NoRecorder_Control_20260928"
    destination = output_root / name
    copy_names = ("Project.ini", "Interface.xml", "Model_00.xml", "Parameters_00.xml", "input_data.txt")
    copy_core(IRIS_REPLAY_SOURCE, destination, copy_names)
    patch_project(destination / "Project.ini", name, 7.0)
    for filename in ("Model_00.xml", "Parameters_00.xml"):
        path = destination / filename
        tree = ET.parse(path)
        root = tree.getroot()
        set_replay_input(root)
        write_xml(tree, path)
    (destination / "README.md").write_text(
        f"# {name}\n\n"
        "Control clone of the previously successful three-prototype Iris replay. It retains the "
        "source threshold and all neuron/synapse parameters, enables only file replay, and does "
        "not add the dynamics recorder. This distinguishes saved-model startup from recorder-link "
        "startup.\n\nRun: `NeuroModelerConsole.exe -c Project.ini -s -t 7 -x -S`.\n",
        encoding="utf-8",
    )
    return [destination]


def prepare_nclassifier_sweep(output_root: Path, thresholds: tuple[float, ...]) -> list[Path]:
    return [prepare_clone(
        NCLASSIFIER_SOURCE,
        f"NClassifier_ThreeProbes_Threshold{int(round(threshold * 100000)):05d}_20260928",
        threshold,
        NCLASSIFIER_SECONDS,
        "NClassifier",
        output_root,
        add_nclassifier_signals,
    ) for threshold in thresholds]


def prepare_npca(output_root: Path, thresholds: tuple[float, ...]) -> list[Path]:
    return [prepare_clone(
        NPCA_SOURCE,
        f"NPCAClassifier_OnePattern_Threshold{int(round(threshold * 100000)):05d}_20260928",
        threshold,
        NPCA_SECONDS,
        "NPCA",
        output_root,
        lambda root: [(
            "neuron_ltz",
            "NPCAClassifier.SpikeClassifier.NeuronTrainer1.Neuron.LTZone",
        )],
    ) for threshold in thresholds]


def clone_existing(source: Path, destination: Path, threshold: float, seconds: float) -> Path:
    name = destination.name
    files = ["Project.ini", "Interface.xml", "Model_00.xml", "Parameters_00.xml", "input_data.txt"]
    for filename in ("expected_classes.csv",):
        if (source / filename).is_file():
            files.append(filename)
    copy_core(source, destination, tuple(files))
    patch_project(destination / "Project.ini", name, seconds)
    for filename in ("Model_00.xml", "Parameters_00.xml"):
        path = destination / filename
        tree = ET.parse(path)
        root = tree.getroot()
        set_fixed_threshold(root, threshold)
        model = model_node(root)
        classifier = next((node for node in model.iter()
                           if node.get("Class") == "NSpikeClassifier"), None)
        if classifier is None:
            raise ValueError(f"NSpikeClassifier missing in {source}")
        set_text(classifier, "./Parameters/DataFromFile", "1")
        recorder = model.find("./Components/ClassifierDynamicsRecorder")
        if recorder is None:
            raise ValueError(f"Recorder missing in {source}")
        add_recorder(
            root,
            "signals.csv",
            add_nspike_signals(root),
            connect=filename == "Model_00.xml",
        )
        write_xml(tree, path)
    (destination / "README.md").write_text(
        f"# {name}\n\nClone of `{source.name}` with the same already-trained network and "
        f"lateral-inhibition setting. All LTZone thresholds were set to {threshold:g}; "
        "structures and physical parameters were not changed. The recorder was rebuilt "
        "to connect only the three class-neuron LTZone outputs, leaving all classifier "
        "input and neuron links intact. After EOF DataFromFile is saved as 0; create a "
        "fresh clone before repeating the replay.\n\n"
        f"Run: `NeuroModelerConsole.exe -c Project.ini -s -t {seconds:g} -x -S`.\n",
        encoding="utf-8",
    )
    return destination


def prepare_synapse_and_inhibition(output_root: Path) -> list[Path]:
    clones: list[Path] = []
    for synapse_dir in sorted(SYNAPSE_AUDIT.glob("NSpikeClassifier_Class2_D17_Syn*_20260928")):
        match = re.search(r"Syn(\d+)_(On|Off)_", synapse_dir.name)
        if not match:
            continue
        count, mode = match.groups()
        dest = output_root / f"NSpikeSynapseCount_Syn{count}_{mode}_Threshold00085_20260928"
        clones.append(clone_existing(synapse_dir, dest, 0.0085, FIXED_REPLAY_SECONDS))

    for mode in ("On", "Off"):
        source = COMPETITION_AUDIT / f"NSpikeClassifier_AllProbesCompetition_Dynamics{mode}_Threshold0006_20260928"
        dest = output_root / f"NSpikeClassifier_AllProbes_{mode}_Threshold00085_20260928"
        clones.append(clone_existing(source, dest, 0.0085, FIXED_REPLAY_SECONDS))
    return clones


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--only", choices=("iris", "iris-smoke", "iris-control", "nclassifier", "npca", "fixed", "all"), default="all")
    parser.add_argument("--nclassifier-thresholds", nargs="+", type=float,
                        default=(0.0035, 0.006, 0.0085, 0.0117))
    parser.add_argument("--npca-thresholds", nargs="+", type=float, default=(0.0085,))
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    if args.only in ("iris", "all"):
        created += prepare_iris(args.output_root)
    if args.only == "iris-smoke":
        created += prepare_iris_smoke(args.output_root)
    if args.only == "iris-control":
        created += prepare_iris_no_recorder_control(args.output_root)
    if args.only in ("nclassifier", "all"):
        created += prepare_nclassifier_sweep(args.output_root, tuple(args.nclassifier_thresholds))
    if args.only in ("npca", "all"):
        created += prepare_npca(args.output_root, tuple(args.npca_thresholds))
    if args.only in ("fixed", "all"):
        created += prepare_synapse_and_inhibition(args.output_root)
    print("\n".join(str(path) for path in created))


if __name__ == "__main__":
    main()

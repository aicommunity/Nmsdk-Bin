#!/usr/bin/env python3
"""Prepare fresh NNeuronTrainer runs from the saved classifier neuron subtree.

Only the training pattern, project run length/name, and IsNeedToTrain state are
changed. The neuron class, LTZone type/threshold, and physical model parameters
are copied from the audited NSpikeClassifier trainer subtree.
"""

from __future__ import annotations

import shutil
import re
import xml.etree.ElementTree as ET
from pathlib import Path


AUDIT_DIR = Path(__file__).resolve().parent
SEED = (Path(__file__).resolve().parents[1] / "ClassifierDynamicsAudit_20260927"
        / "NNeuronTrainer_NSPNeuron_ClassifierTemplate_Synthetic_20260927")
PATTERNS = {
    "wide_spread": [0.0389, 0.125, 0.0102, 0.0167, 0.2],
    "medium_spread": [0.05, 0.09, 0.13, 0.16, 0.2],
    "short_spread": [0.155, 0.17, 0.185, 0.195, 0.2],
}
RUN_SECONDS = 120


def set_text(parent: ET.Element, path: str, value: str) -> None:
    node = parent.find(path)
    if node is None:
        raise ValueError(f"Missing XML node: {path}")
    node.text = value


def write_xml(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="\t")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def prepare(name: str, pattern: list[float]) -> None:
    dst = AUDIT_DIR / f"NNeuronTrainer_TypeMatched_{name}_20260928"
    dst.mkdir(parents=True, exist_ok=True)
    for filename in ("Project.ini", "Model_00.xml", "Parameters_00.xml", "Interface.xml"):
        shutil.copy2(SEED / filename, dst / filename)

    project_path = dst / "Project.ini"
    # Project.ini is XML-like but uses the invalid XML element name <00>.
    # Patch only the intended scalar fields without reformatting the file.
    project_text = project_path.read_text(encoding="utf-8-sig")
    project_replacements = {
        "ProjectName": dst.name,
        "MaxCalculationModelTime": str(RUN_SECONDS),
        "ProjectAutoSaveFlag": "1",
        "ProjectAutoSaveModelTimeInterval": "10",
    }
    for tag, value in project_replacements.items():
        project_text, count = re.subn(
            rf"(<{tag}>).*?(</{tag}>)",
            lambda match: match.group(1) + value + match.group(2),
            project_text,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError(f"Expected one <{tag}> element in {project_path}, found {count}")
    project_path.write_text(project_text, encoding="utf-8")

    for filename in ("Model_00.xml", "Parameters_00.xml"):
        path = dst / filename
        tree = ET.parse(path)
        root = tree.getroot()
        trainer = root.find(".//NeuronTrainer")
        if trainer is None:
            raise ValueError(f"NeuronTrainer not found in {path}")
        set_text(trainer, "./Parameters/IsNeedToTrain", "1")
        input_node = trainer.find("./Parameters/InputPattern")
        if input_node is None:
            raise ValueError(f"InputPattern not found in {path}")
        input_node.attrib["Rows"] = str(len(pattern))
        input_node.attrib["Cols"] = "1"
        input_node.text = "\n" + "\n".join(format(value, ".17g") for value in pattern)

        sources = trainer.find("./Components")
        if sources is None:
            raise ValueError(f"Trainer components not found in {path}")
        trainer_delay = float(trainer.findtext("./Parameters/Delay", "0"))
        for index, value in enumerate(pattern, start=1):
            source = sources.find(f"Source{index}")
            if source is None:
                raise ValueError(f"Source{index} not found in {path}")
            set_text(source, "./Parameters/Delay", format(trainer_delay + value, ".17g"))
        write_xml(tree, path)

    (dst / "README.md").write_text(
        f"# Type-matched Trainer sweep: {name}\n\n"
        "Fresh structural training from the exact saved classifier neuron subtree: "
        "`NSPNeuron` with `NPulseLTZoneThreshold`. The pattern is the only training/model "
        "input varied across this sweep. Neuron and synapse physical parameters and both "
        "LTZone thresholds are copied from the seed unchanged. `IsNeedToTrain=1`; the run "
        f"uses {RUN_SECONDS} model seconds and 10-second model/parameter autosaves.\n\n"
        f"InputPattern: `{pattern}`\n\n"
        "Run from this directory with `NeuroModelerConsole.exe -c Project.ini -s -t 120 -x -S`.\n\n"
        "The passive recorder writes `TrainerSpikeProbe/ltz.csv`. At completion, compare "
        "`TrainingDendIndexes`, `TrainingSynapsisNum`, `NumDendriteMembranePartsVec`, "
        "and the LTZone rising-edge count per 2-second input period.\n",
        encoding="utf-8",
    )
    print(dst)


def main() -> None:
    if not SEED.is_dir():
        raise FileNotFoundError(SEED)
    for name, pattern in PATTERNS.items():
        prepare(name, pattern)


if __name__ == "__main__":
    main()

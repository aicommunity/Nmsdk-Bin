#!/usr/bin/env python3
"""Add SomaAmplitudeInput link for Branch test Model_00.xml.

Idempotent: never turns NeuronTimeLearnerBranch into BranchBranch.
Also repairs any existing BranchBranch typos.
"""
import re
import sys
from pathlib import Path


def repair_branchbranch(text: str) -> str:
    text = text.replace("NNeuronTimeLearnerBranchBranch", "NNeuronTimeLearnerBranch")
    text = text.replace("NeuronTimeLearnerBranchBranch", "NeuronTimeLearnerBranch")
    return text


def ensure_branch_names(text: str) -> str:
    """Rename classic TimeLearner component to Branch once."""
    text = repair_branchbranch(text)
    if "NeuronTimeLearnerBranch" in text:
        return text
    text = re.sub(r"NeuronTimeLearner(?!Branch)", "NeuronTimeLearnerBranch", text)
    text = re.sub(r"NNeuronTimeLearner(?!Branch)", "NNeuronTimeLearnerBranch", text)
    return text


def patch_model(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = ensure_branch_names(text)
    if "SomaAmplitudeInput" in text:
        path.write_text(text, encoding="utf-8")
        return

    link_block = """
			<elem Type="ULink">
				<Item Type="ULinkSide" Index="-1" Name="SomaNeuronAmplitude">NeuronTimeLearnerBranch</Item>
				<Connector Type="ULinkSide" Index="-1" Name="SomaAmplitudeInput">PatternResponseAnalyzer</Connector>
			</elem>"""

    marker = (
        '<Item Type="ULinkSide" Index="-1" Name="CurrentClassMatrix">'
        "NeuronTimeLearnerBranch.DatasetMatrix</Item>"
    )
    insert_after = "\t\t\t<elem Type=\"ULink\">\n\t\t\t\t" + marker
    if insert_after not in text:
        raise SystemExit(f"link anchor not found in {path}")
    text = text.replace(
        insert_after, link_block + "\n\t\t\t<elem Type=\"ULink\">\n\t\t\t\t" + marker, 1
    )

    m = re.search(r'<Links Type="ULinksList" Size="(\d+)">', text)
    if not m:
        raise SystemExit(f"Links Size not found in {path}")
    old_size = int(m.group(1))
    text = text.replace(
        f'<Links Type="ULinksList" Size="{old_size}">',
        f'<Links Type="ULinksList" Size="{old_size + 1}">',
        1,
    )
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_model(Path(sys.argv[1]))

#!/usr/bin/env python3
"""Add SomaAmplitudeInput link for Branch test Model_00.xml."""
import re
import sys
from pathlib import Path


def patch_model(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "NeuronTimeLearnerBranch" not in text:
        text = text.replace("NeuronTimeLearner", "NeuronTimeLearnerBranch")
    if "SomaAmplitudeInput" in text:
        path.write_text(text, encoding="utf-8")
        return

    link_block = """
\t\t\t<elem Type="ULink">
\t\t\t\t<Item Type="ULinkSide" Index="-1" Name="SomaNeuronAmplitude">NeuronTimeLearnerBranch</Item>
\t\t\t\t<Connector Type="ULinkSide" Index="-1" Name="SomaAmplitudeInput">PatternResponseAnalyzer</Connector>
\t\t\t</elem>"""

    marker = '<Item Type="ULinkSide" Index="-1" Name="CurrentClassMatrix">NeuronTimeLearnerBranch.DatasetMatrix</Item>'
    insert_after = '\t\t\t<elem Type="ULink">\n\t\t\t\t' + marker
    if insert_after not in text:
        raise SystemExit(f"link anchor not found in {path}")
    text = text.replace(insert_after, link_block + '\n\t\t\t<elem Type="ULink">\n\t\t\t\t' + marker, 1)

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

#!/usr/bin/env python3
"""Add SomaAmplitudeInput link to PatternResponseAnalyzer in test Model_00.xml."""
import re
import sys
from pathlib import Path


def patch_model(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "SomaAmplitudeInput" in text:
        return

    link_block = """
\t\t\t<elem Type="ULink">
\t\t\t\t<Item Type="ULinkSide" Index="-1" Name="SomaNeuronAmplitude">NeuronTimeLearner</Item>
\t\t\t\t<Connector Type="ULinkSide" Index="-1" Name="SomaAmplitudeInput">PatternResponseAnalyzer</Connector>
\t\t\t</elem>"""

    marker = '<Item Type="ULinkSide" Index="-1" Name="CurrentClassMatrix">NeuronTimeLearner.DatasetMatrix</Item>'
    insert_after = '\t\t\t<elem Type="ULink">\n\t\t\t\t' + marker
    if insert_after not in text:
        # fallback: insert before first PatternResponseAnalyzer Stimulus link
        marker2 = '<Connector Type="ULinkSide" Index="-1" Name="StimulusInputs">PatternResponseAnalyzer</Connector>'
        if marker2 not in text:
            raise SystemExit(f"link anchor not found in {path}")
        text = text.replace(
            '\t\t\t<elem Type="ULink">\n\t\t\t\t<Item Type="ULinkSide" Index="-1" Name="Output">NeuronTimeLearner.DatasetMatrix.Generator1</Item>\n\t\t\t\t' + marker2,
            link_block + '\n\t\t\t<elem Type="ULink">\n\t\t\t\t<Item Type="ULinkSide" Index="-1" Name="Output">NeuronTimeLearner.DatasetMatrix.Generator1</Item>\n\t\t\t\t' + marker2,
            1,
        )
    else:
        text = text.replace(insert_after, link_block + '\n\t\t\t<elem Type="ULink">\n\t\t\t\t' + marker, 1)

    m = re.search(r"<Links Type=\"ULinksList\" Size=\"(\d+)\">", text)
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

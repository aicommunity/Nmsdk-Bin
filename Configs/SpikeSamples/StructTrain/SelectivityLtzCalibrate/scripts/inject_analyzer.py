#!/usr/bin/env python3
"""Add PatternResponseAnalyzer to test Model in-place (do not replace test Model from train)."""
import re
import sys
from pathlib import Path

ANALYZER_LINKS = """			<elem Type="ULink">
				<Item Type="ULinkSide" Index="-1" Name="Output">NeuronTimeLearner.DatasetMatrix.Generator1</Item>
				<Connector Type="ULinkSide" Index="-1" Name="StimulusInputs">PatternResponseAnalyzer</Connector>
			</elem>
			<elem Type="ULink">
				<Item Type="ULinkSide" Index="-1" Name="Output">NeuronTimeLearner.Neuron.LTZone</Item>
				<Connector Type="ULinkSide" Index="-1" Name="NeuronOutputs">PatternResponseAnalyzer</Connector>
			</elem>
			<elem Type="ULink">
				<Item Type="ULinkSide" Index="-1" Name="CurrentClassMatrix">NeuronTimeLearner.DatasetMatrix</Item>
				<Connector Type="ULinkSide" Index="-1" Name="TargetClassInput">PatternResponseAnalyzer</Connector>
			</elem>
			<elem Type="ULink">
				<Item Type="ULinkSide" Index="-1" Name="SomaNeuronAmplitude">NeuronTimeLearner</Item>
				<Connector Type="ULinkSide" Index="-1" Name="SomaAmplitudeInput">PatternResponseAnalyzer</Connector>
			</elem>
"""

ANALYZER_COMPONENT = """			<PatternResponseAnalyzer Class="NPatternResponseAnalyzer">
				<Parameters>
					<Activity Type="b" PType="257" IoType="17">1</Activity>
					<MaxCalculationDuration Type="x" PType="257" IoType="17">-1</MaxCalculationDuration>
					<CalculationDurationThreshold Type="x" PType="257" IoType="17">-1</CalculationDurationThreshold>
					<Coord Type="MVector&lt;d&gt;" Size="3" PType="257" IoType="17">20 5 0</Coord>
					<DebugSysEventsMask Type="j" PType="769" IoType="17">4294967295</DebugSysEventsMask>
					<PostPatternWindow Type="d" PType="257" IoType="17">0.5</PostPatternWindow>
					<PulseDetectThreshold Type="d" PType="257" IoType="17">0</PulseDetectThreshold>
					<SavePath Type="std::string" PType="257" IoType="17">SelectivityLog</SavePath>
					<FileName Type="std::string" PType="257" IoType="17">results.csv</FileName>
					<AppendMode Type="b" PType="257" IoType="17">0</AppendMode>
					<Enable Type="b" PType="257" IoType="17">1</Enable>
				</Parameters>
				<Components/>
			</PatternResponseAnalyzer>
"""


def inject(model_text: str) -> str:
    if "PatternResponseAnalyzer" not in model_text:
        m = re.search(r'<Links Type="ULinksList" Size="(\d+)">', model_text)
        if not m:
            raise SystemExit("Links Size not found")
        old = int(m.group(1))
        model_text = model_text.replace(
            f'<Links Type="ULinksList" Size="{old}">',
            f'<Links Type="ULinksList" Size="{old + 4}">\n' + ANALYZER_LINKS,
            1,
        )
        model_text = model_text.replace(
            "\t\t</Components>\n\t</Model>",
            ANALYZER_COMPONENT + "\t\t</Components>\n\t</Model>",
            1,
        )
    return model_text


def main() -> None:
    args = sys.argv[1:]
    if not args:
        raise SystemExit("Usage: inject_analyzer.py <test/Model_00.xml>  OR  inject_analyzer.py <train/Model> <test/Model>")

    if len(args) == 1:
        test_model = Path(args[0])
    else:
        test_model = Path(args[1])

    text = inject(test_model.read_text(encoding="utf-8"))
    test_model.write_text(text, encoding="utf-8")

    if "SomaAmplitudeInput" not in text:
        sys.path.insert(0, str(Path(__file__).parent))
        from patch_test_model import patch_model

        patch_model(test_model)

    print(f"injected PatternResponseAnalyzer in-place: {test_model}")


if __name__ == "__main__":
    main()

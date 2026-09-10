#!/usr/bin/env python3
"""Build delay/chain/chain_and_delay templates for AxoneLengthDelayStudy."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
NE = STUDY.parent
AX_DELAY = NE / "AxoneDelaySweep"
AX_CHAIN = NE / "AxoneChainLengthSweep"
AX_CMP = NE / "AxoneTypesCompare"

STAT_BLOCK = """\
\t\t\t<StatisticDoubleMatrix Class="UStatisticDoubleMatrix">
\t\t\t\t<Parameters>
\t\t\t\t\t<ForceCreateSavePath Type="b" PType="257" IoType="17">1</ForceCreateSavePath>
\t\t\t\t\t<Coord Type="MVector&lt;d&gt;" Size="3" PType="257" IoType="17">22 5 6</Coord>
\t\t\t\t\t<MaxCalculationDuration Type="x" PType="257" IoType="17">-1</MaxCalculationDuration>
\t\t\t\t\t<Activity Type="b" PType="257" IoType="17">1</Activity>
\t\t\t\t\t<CalculationDurationThreshold Type="x" PType="257" IoType="17">-1</CalculationDurationThreshold>
\t\t\t\t\t<DebugSysEventsMask Type="j" PType="769" IoType="17">2147483647</DebugSysEventsMask>
\t\t\t\t\t<SavePath Type="std::string" PType="257" IoType="17">StatisticLog</SavePath>
\t\t\t\t\t<TimeToFileNameFlag Type="b" PType="257" IoType="17">0</TimeToFileNameFlag>
\t\t\t\t\t<PrefixName Type="std::string" PType="257" IoType="17">ax</PrefixName>
\t\t\t\t\t<SubFolderAfterResetFlag Type="b" PType="257" IoType="17">0</SubFolderAfterResetFlag>
\t\t\t\t\t<OrderIndexToFileNameFlag Type="b" PType="257" IoType="17">1</OrderIndexToFileNameFlag>
\t\t\t\t\t<ExcludeModelFileName Type="b" PType="257" IoType="17">1</ExcludeModelFileName>
\t\t\t\t\t<AverageMode Type="i" PType="257" IoType="17">0</AverageMode>
\t\t\t\t\t<SaveMode Type="i" PType="257" IoType="17">0</SaveMode>
\t\t\t\t\t<NumSkipSteps Type="i" PType="257" IoType="17">0</NumSkipSteps>
\t\t\t\t\t<ManualModeEnabled Type="b" PType="257" IoType="17">0</ManualModeEnabled>
\t\t\t\t\t<TimeInterval Type="d" PType="257" IoType="17">0</TimeInterval>
\t\t\t\t\t<ManualModeSwitch Type="b" PType="257" IoType="17">0</ManualModeSwitch>
\t\t\t\t\t<WriteModelTimeStampFlag Type="b" PType="257" IoType="17">1</WriteModelTimeStampFlag>
\t\t\t\t\t<WriteSourceTimeStampFlag Type="b" PType="257" IoType="17">0</WriteSourceTimeStampFlag>
\t\t\t\t\t<AverageNumber Type="i" PType="257" IoType="17">1</AverageNumber>
\t\t\t\t\t<AverageInput Type="std::pair" PType="257" IoType="17">
\t\t\t\t\t\t<first Type="std::string"></first>
\t\t\t\t\t\t<second Type="std::string"></second>
\t\t\t\t\t</AverageInput>
\t\t\t\t\t<WriteTimeStampFlag Type="b" PType="257" IoType="17">0</WriteTimeStampFlag>
\t\t\t\t\t<WriteTimeFromResetFlag Type="b" PType="257" IoType="17">0</WriteTimeFromResetFlag>
\t\t\t\t\t<WriteIndexFlag Type="b" PType="257" IoType="17">0</WriteIndexFlag>
\t\t\t\t</Parameters>
\t\t\t\t<Components/>
\t\t\t</StatisticDoubleMatrix>
"""

LINKS = """\
\t\t<Links Type="ULinksList" Size="3">
\t\t\t<elem Type="ULink">
\t\t\t\t<Item Type="ULinkSide" Index="-1" Name="Output">PGenerator</Item>
\t\t\t\t<Connector Type="ULinkSide" Index="-1" Name="Input">AxoneUnderTest</Connector>
\t\t\t</elem>
\t\t\t<elem Type="ULink">
\t\t\t\t<Item Type="ULinkSide" Index="-1" Name="Output">PGenerator</Item>
\t\t\t\t<Connector Type="ULinkSide" Index="-1" Name="InputMatrixData">StatisticDoubleMatrix</Connector>
\t\t\t</elem>
\t\t\t<elem Type="ULink">
\t\t\t\t<Item Type="ULinkSide" Index="-1" Name="Output">AxoneUnderTest</Item>
\t\t\t\t<Connector Type="ULinkSide" Index="-1" Name="InputMatrixData">StatisticDoubleMatrix</Connector>
\t\t\t</elem>
\t\t</Links>
"""

PGEN = """\
\t\t\t<PGenerator Class="NPGenerator">
\t\t\t\t<Parameters>
\t\t\t\t\t<Activity Type="b" PType="257" IoType="17">1</Activity>
\t\t\t\t\t<MaxCalculationDuration Type="x" PType="257" IoType="17">-1</MaxCalculationDuration>
\t\t\t\t\t<CalculationDurationThreshold Type="x" PType="257" IoType="17">-1</CalculationDurationThreshold>
\t\t\t\t\t<Coord Type="MVector&lt;d&gt;" Size="3" PType="257" IoType="17">4.66666 5.33333 1</Coord>
\t\t\t\t\t<DebugSysEventsMask Type="j" PType="769" IoType="17">2147483647</DebugSysEventsMask>
\t\t\t\t\t<ActionPeriod Type="j" PType="257" IoType="17">0</ActionPeriod>
\t\t\t\t\t<Frequency Type="d" PType="257" IoType="17">10</Frequency>
\t\t\t\t\t<PulseLength Type="d" PType="257" IoType="17">0.001</PulseLength>
\t\t\t\t\t<Amplitude Type="d" PType="257" IoType="17">1</Amplitude>
\t\t\t\t\t<Delay Type="d" PType="257" IoType="17">0</Delay>
\t\t\t\t\t<FrequencyDeviation Type="d" PType="257" IoType="17">0</FrequencyDeviation>
\t\t\t\t\t<AvgInterval Type="d" PType="257" IoType="17">5</AvgInterval>
\t\t\t\t</Parameters>
\t\t\t\t<Components/>
\t\t\t</PGenerator>
"""

MODEL_HEADER = """\
<Save ModelName="Model">
\t<Model Class="Model">
\t\t<Parameters>
\t\t\t<Activity Type="b" PType="257" IoType="17">1</Activity>
\t\t\t<MaxCalculationDuration Type="x" PType="257" IoType="17">-1</MaxCalculationDuration>
\t\t\t<CalculationDurationThreshold Type="x" PType="257" IoType="17">-1</CalculationDurationThreshold>
\t\t\t<Coord Type="MVector&lt;d&gt;" Size="3" PType="257" IoType="17">0 0 0</Coord>
\t\t\t<DebugSysEventsMask Type="j" PType="769" IoType="17">2147483647</DebugSysEventsMask>
\t\t\t<Output Type="UBitmap" Size="0" PType="257" IoType="17">
\t\t\t\t<Width Type="i">0</Width>
\t\t\t\t<Height Type="i">0</Height>
\t\t\t\t<ColorModel Type="UBMColorModel">3</ColorModel>
\t\t\t\t<Data/>
\t\t\t</Output>
\t\t</Parameters>
"""

PARAMS_HEADER = """\
<SaveProperties ModelName="Model">
\t<Model Class="Model">
\t\t<Parameters>
\t\t\t<Activity Type="b" PType="257" IoType="17">1</Activity>
\t\t\t<MaxCalculationDuration Type="x" PType="257" IoType="17">-1</MaxCalculationDuration>
\t\t\t<CalculationDurationThreshold Type="x" PType="257" IoType="17">-1</CalculationDurationThreshold>
\t\t\t<Coord Type="MVector&lt;d&gt;" Size="3" PType="257" IoType="17">0 0 0</Coord>
\t\t\t<DebugSysEventsMask Type="j" PType="769" IoType="17">2147483647</DebugSysEventsMask>
\t\t\t<Output Type="UBitmap" Size="0" PType="257" IoType="17">
\t\t\t\t<Width Type="i">0</Width>
\t\t\t\t<Height Type="i">0</Height>
\t\t\t\t<ColorModel Type="UBMColorModel">3</ColorModel>
\t\t\t\t<Data/>
\t\t\t</Output>
\t\t</Parameters>
"""

FOOTER = """\
\t\t</Components>
\t</Model>
</Save>
"""

PARAMS_FOOTER = """\
\t\t</Components>
\t</Model>
</SaveProperties>
"""

DELAY_AXON = """\
\t\t\t<AxoneUnderTest Class="NAxoneDelay">
\t\t\t\t<Parameters>
\t\t\t\t\t<Activity Type="b" PType="257" IoType="17">1</Activity>
\t\t\t\t\t<MaxCalculationDuration Type="x" PType="257" IoType="17">-1</MaxCalculationDuration>
\t\t\t\t\t<CalculationDurationThreshold Type="x" PType="257" IoType="17">-1</CalculationDurationThreshold>
\t\t\t\t\t<Coord Type="MVector&lt;d&gt;" Size="3" PType="257" IoType="17">12 5.5 0</Coord>
\t\t\t\t\t<DebugSysEventsMask Type="j" PType="769" IoType="17">2147483647</DebugSysEventsMask>
\t\t\t\t\t<ActionPeriod Type="j" PType="257" IoType="17">0</ActionPeriod>
\t\t\t\t\t<DelayTime Type="d" PType="257" IoType="17">0.001</DelayTime>
\t\t\t\t</Parameters>
\t\t\t\t<Components/>
\t\t\t</AxoneUnderTest>
"""

CHAIN_AXON = """\
\t\t\t<AxoneUnderTest Class="NAxoneChain">
\t\t\t\t<Parameters>
\t\t\t\t\t<Activity Type="b" PType="257" IoType="17">1</Activity>
\t\t\t\t\t<MaxCalculationDuration Type="x" PType="257" IoType="17">-1</MaxCalculationDuration>
\t\t\t\t\t<CalculationDurationThreshold Type="x" PType="257" IoType="17">-1</CalculationDurationThreshold>
\t\t\t\t\t<Coord Type="MVector&lt;d&gt;" Size="3" PType="257" IoType="17">12 5.5 0</Coord>
\t\t\t\t\t<DebugSysEventsMask Type="j" PType="769" IoType="17">2147483647</DebugSysEventsMask>
\t\t\t\t\t<ActionPeriod Type="j" PType="257" IoType="17">0</ActionPeriod>
\t\t\t\t\t<NumSegments Type="i" PType="257" IoType="17">1</NumSegments>
\t\t\t\t\t<MembraneClassName Type="std::string" PType="257" IoType="17">NPMembraneBio</MembraneClassName>
\t\t\t\t\t<LTZoneClassName Type="std::string" PType="257" IoType="17">NPulseLTZoneThreshold</LTZoneClassName>
\t\t\t\t\t<PosGeneratorClassName Type="std::string" PType="257" IoType="17">NPNeuronPosCGenerator</PosGeneratorClassName>
\t\t\t\t</Parameters>
\t\t\t\t<Components/>
\t\t\t</AxoneUnderTest>
"""

CAD_AXON = """\
\t\t\t<AxoneUnderTest Class="NAxoneChainAndDelay">
\t\t\t\t<Parameters>
\t\t\t\t\t<Activity Type="b" PType="257" IoType="17">1</Activity>
\t\t\t\t\t<MaxCalculationDuration Type="x" PType="257" IoType="17">-1</MaxCalculationDuration>
\t\t\t\t\t<CalculationDurationThreshold Type="x" PType="257" IoType="17">-1</CalculationDurationThreshold>
\t\t\t\t\t<Coord Type="MVector&lt;d&gt;" Size="3" PType="257" IoType="17">12 5.5 0</Coord>
\t\t\t\t\t<DebugSysEventsMask Type="j" PType="769" IoType="17">2147483647</DebugSysEventsMask>
\t\t\t\t\t<ActionPeriod Type="j" PType="257" IoType="17">0</ActionPeriod>
\t\t\t\t\t<NumNodes Type="i" PType="257" IoType="17">1</NumNodes>
\t\t\t\t\t<InternodeDelayTime Type="d" PType="257" IoType="17">0.002</InternodeDelayTime>
\t\t\t\t\t<MembraneClassName Type="std::string" PType="257" IoType="17">NPMembraneBio</MembraneClassName>
\t\t\t\t\t<LTZoneClassName Type="std::string" PType="257" IoType="17">NPulseLTZoneThreshold</LTZoneClassName>
\t\t\t\t\t<PosGeneratorClassName Type="std::string" PType="257" IoType="17">NPNeuronPosCGenerator</PosGeneratorClassName>
\t\t\t\t</Parameters>
\t\t\t\t<Components/>
\t\t\t</AxoneUnderTest>
"""

WATCH_TAB = """\
\t<UGEngineControllWidget.UWatch.tab_1>
\t\t<schemaVersion>2</schemaVersion>
\t\t<GridColCount>1</GridColCount>
\t\t<GridRowCount>1</GridRowCount>
\t\t<GraphCount>1</GraphCount>
\t\t<ColSplitterCount>1</ColSplitterCount>
\t\t<ColSplitter_0>502</ColSplitter_0>
\t\t<RowSplitterRowCount>1</RowSplitterRowCount>
\t\t<RowSplitterCount_0>1</RowSplitterCount_0>
\t\t<RowSplitter_0_0>1097</RowSplitter_0_0>
\t\t<graph_0>
\t\t\t<VizKind>TimeSeries</VizKind>
\t\t\t<ChartTitle>TITLE_PLACEHOLDER</ChartTitle>
\t\t\t<AxisXName>time, sec</AxisXName>
\t\t\t<AxisYName>Output parameter</AxisYName>
\t\t\t<AxisYmin>-0.10000000000000001</AxisYmin>
\t\t\t<AxisYmax>2</AxisYmax>
\t\t\t<AxisXmin>0</AxisXmin>
\t\t\t<AxisXmax>2</AxisXmax>
\t\t\t<AxisXrange>2</AxisXrange>
\t\t\t<LegendVisible>1</LegendVisible>
\t\t\t<TitleVisible>1</TitleVisible>
\t\t\t<TrackLatest>1</TrackLatest>
\t\t\t<InteractionMode>0</InteractionMode>
\t\t\t<UpdateIntervalMs>200</UpdateIntervalMs>
\t\t\t<SeriesCount>2</SeriesCount>
\t\t\t<serie_0>
\t\t\t\t<SerieName>PGenerator.Output</SerieName>
\t\t\t\t<SerieWidth>1</SerieWidth>
\t\t\t\t<SerieLineType>1</SerieLineType>
\t\t\t\t<SerieColor>-10777105</SerieColor>
\t\t\t\t<SerieYShift>0</SerieYShift>
\t\t\t\t<SerieEnabled>1</SerieEnabled>
\t\t\t\t<SerieChannel>0</SerieChannel>
\t\t\t\t<SerieWindowSize>8192</SerieWindowSize>
\t\t\t\t<SerieXyMinIntervalMs>0</SerieXyMinIntervalMs>
\t\t\t\t<SerieXyMinDistance>0</SerieXyMinDistance>
\t\t\t\t<SerieNameComponent>PGenerator</SerieNameComponent>
\t\t\t\t<SerieNameProperty>Output</SerieNameProperty>
\t\t\t\t<SerieJx>0</SerieJx>
\t\t\t\t<SerieJy>0</SerieJy>
\t\t\t\t<SerieXKind>0</SerieXKind>
\t\t\t\t<SerieXComponent></SerieXComponent>
\t\t\t\t<SerieXProperty></SerieXProperty>
\t\t\t\t<SerieXJx>-1</SerieXJx>
\t\t\t\t<SerieXJy>-1</SerieXJy>
\t\t\t\t<SerieXSlice>0</SerieXSlice>
\t\t\t\t<SerieYKind>1</SerieYKind>
\t\t\t\t<SerieYComponent>PGenerator</SerieYComponent>
\t\t\t\t<SerieYProperty>Output</SerieYProperty>
\t\t\t\t<SerieYJx>0</SerieYJx>
\t\t\t\t<SerieYJy>0</SerieYJy>
\t\t\t\t<SerieYSlice>0</SerieYSlice>
\t\t\t</serie_0>
\t\t\t<serie_1>
\t\t\t\t<SerieName>AxoneUnderTest.Output</SerieName>
\t\t\t\t<SerieWidth>1</SerieWidth>
\t\t\t\t<SerieLineType>1</SerieLineType>
\t\t\t\t<SerieColor>-15681151</SerieColor>
\t\t\t\t<SerieYShift>0</SerieYShift>
\t\t\t\t<SerieEnabled>1</SerieEnabled>
\t\t\t\t<SerieChannel>0</SerieChannel>
\t\t\t\t<SerieWindowSize>8192</SerieWindowSize>
\t\t\t\t<SerieXyMinIntervalMs>0</SerieXyMinIntervalMs>
\t\t\t\t<SerieXyMinDistance>0</SerieXyMinDistance>
\t\t\t\t<SerieNameComponent>AxoneUnderTest</SerieNameComponent>
\t\t\t\t<SerieNameProperty>Output</SerieNameProperty>
\t\t\t\t<SerieJx>0</SerieJx>
\t\t\t\t<SerieJy>0</SerieJy>
\t\t\t\t<SerieXKind>0</SerieXKind>
\t\t\t\t<SerieXComponent></SerieXComponent>
\t\t\t\t<SerieXProperty></SerieXProperty>
\t\t\t\t<SerieXJx>-1</SerieXJx>
\t\t\t\t<SerieXJy>-1</SerieXJy>
\t\t\t\t<SerieXSlice>0</SerieXSlice>
\t\t\t\t<SerieYKind>1</SerieYKind>
\t\t\t\t<SerieYComponent>AxoneUnderTest</SerieYComponent>
\t\t\t\t<SerieYProperty>Output</SerieYProperty>
\t\t\t\t<SerieYJx>0</SerieYJx>
\t\t\t\t<SerieYJy>0</SerieYJy>
\t\t\t\t<SerieYSlice>0</SerieYSlice>
\t\t\t</serie_1>
\t\t</graph_0>
\t</UGEngineControllWidget.UWatch.tab_1>
"""


def write_model_params(dst: Path, axon_xml: str) -> None:
    comps = f"\t\t<Components>\n{PGEN}{axon_xml}{STAT_BLOCK}"
    (dst / "Model_00.xml").write_text(
        MODEL_HEADER + LINKS + comps + FOOTER, encoding="utf-8"
    )
    (dst / "Parameters_00.xml").write_text(
        PARAMS_HEADER + comps + PARAMS_FOOTER, encoding="utf-8"
    )


def write_interface(dst: Path, base_if: Path, title: str) -> None:
    text = base_if.read_text(encoding="utf-8")
    watch = WATCH_TAB.replace("TITLE_PLACEHOLDER", title)
    if re.search(r"<UGEngineControllWidget\.UWatch\.tab_1>.*?</UGEngineControllWidget\.UWatch\.tab_1>", text, re.DOTALL):
        text = re.sub(
            r"<UGEngineControllWidget\.UWatch\.tab_1>.*?</UGEngineControllWidget\.UWatch\.tab_1>",
            watch.strip(),
            text,
            count=1,
            flags=re.DOTALL,
        )
    else:
        text = text.replace("</Interfaces>", watch + "</Interfaces>")
    (dst / "Interface.xml").write_text(text, encoding="utf-8")


def patch_project_name(dst: Path, name: str) -> None:
    p = dst / "project.ini"
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"<ProjectName>[^<]*</ProjectName>", f"<ProjectName>{name}</ProjectName>", text)
    p.write_text(text, encoding="utf-8")


def main() -> None:
    # delay
    d = STUDY / "templates" / "delay"
    write_model_params(d, DELAY_AXON)
    write_interface(d, AX_DELAY / "Interface.xml", "AxoneLengthDelay: NAxoneDelay")
    patch_project_name(d, "AxoneLengthDelayStudy_delay")
    print(f"built {d}")

    # chain
    c = STUDY / "templates" / "chain"
    write_model_params(c, CHAIN_AXON)
    write_interface(c, AX_CHAIN / "Interface.xml", "AxoneLengthDelay: NAxoneChain")
    patch_project_name(c, "AxoneLengthDelayStudy_chain")
    print(f"built {c}")

    # chain_and_delay
    cad = STUDY / "templates" / "chain_and_delay"
    write_model_params(cad, CAD_AXON)
    write_interface(cad, AX_CMP / "Interface.xml", "AxoneLengthDelay: NAxoneChainAndDelay")
    patch_project_name(cad, "AxoneLengthDelayStudy_cad")
    print(f"built {cad}")

    # Expand empty Segment trees (chain/cad Num*=1) via 2→1 + prune.
    # A single -S at N=1 does not reliably persist Segment1 for NAxoneChain.
    import os
    import subprocess
    import sys

    ne_scripts = NE / "scripts"
    sys.path.insert(0, str(STUDY / "scripts"))
    from ensure_watch import ensure_watch

    nm = os.environ.get("NM", "/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole")
    patch = ne_scripts / "patch_param.py"
    titles = {
        c: "AxoneLengthDelay: NAxoneChain",
        cad: "AxoneLengthDelay: NAxoneChainAndDelay",
    }
    length_tag = {c: "NumSegments", cad: "NumNodes"}

    def prune_n1_extras(cell: Path) -> None:
        for fname in ("Model_00.xml", "Parameters_00.xml"):
            p = cell / fname
            if not p.is_file():
                continue
            text = p.read_text(encoding="utf-8")
            text = re.sub(
                r'\n\t+<Segment2 Class="NAxoneSegment">.*?</Segment2>',
                "",
                text,
                count=1,
                flags=re.DOTALL,
            )
            text = re.sub(
                r'\n\t+<Delay1 Class="NAxoneDelay">.*?</Delay1>',
                "",
                text,
                count=1,
                flags=re.DOTALL,
            )

            def drop_link(m: re.Match[str]) -> str:
                b = m.group(0)
                return "" if ("Segment2" in b or "Delay1" in b) else b

            if "<Links" in text:
                text = re.sub(
                    r'\n\t\t\t<elem Type="ULink">.*?</elem>',
                    drop_link,
                    text,
                    flags=re.DOTALL,
                )
                elems = len(re.findall(r'<elem Type="ULink">', text))
                text = re.sub(
                    r'<Links Type="ULinksList" Size="\d+">',
                    f'<Links Type="ULinksList" Size="{elems}">',
                    text,
                    count=1,
                )
            p.write_text(text, encoding="utf-8")

    def expand_template_n1(tmpl: Path, tag: str) -> None:
        print(f"structural 2→1 {tmpl.name} ({tag}) ...")
        for val in (2, 1):
            for xml in (tmpl / "Model_00.xml", tmpl / "Parameters_00.xml"):
                subprocess.run(
                    [sys.executable, str(patch), str(xml), "--set", tag, str(val)],
                    check=True,
                )
            subprocess.run(
                [nm, "-c", str(tmpl / "project.ini"), "-s", "-t", "0.05", "-x", "-S"],
                check=True,
                cwd=str(tmpl),
            )
        prune_n1_extras(tmpl)
        got = (tmpl / "Model_00.xml").read_text(encoding="utf-8").count(
            'Class="NAxoneSegment"'
        )
        if got < 1:
            raise SystemExit(f"FAIL {tmpl.name}: expected >=1 Segment after 2→1, got {got}")
        ensure_watch(tmpl, title=titles[tmpl])
        print(f"expanded {tmpl} segments={got}")

    for tmpl in (c, cad):
        expand_template_n1(tmpl, length_tag[tmpl])


if __name__ == "__main__":
    main()

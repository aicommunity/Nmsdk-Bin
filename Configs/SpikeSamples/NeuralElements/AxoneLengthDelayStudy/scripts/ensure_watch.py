#!/usr/bin/env python3
"""Ensure Watch schemaVersion=2 with PGenerator + AxoneUnderTest series."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

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
\t\t\t<ChartTitle>{title}</ChartTitle>
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


def resolve_title(cell: Path, title: str | None) -> str:
    if title:
        return title
    meta = cell / "meta.json"
    if meta.is_file():
        m = json.loads(meta.read_text(encoding="utf-8"))
        lp = m.get("length_param", "")
        lv = m.get("length_value", "")
        model = m.get("model", "")
        if lp == "DelayTime":
            return f"AxoneLengthDelay: DelayTime={float(lv)*1000:g}ms"
        if lp == "NumSegments":
            return f"AxoneLengthDelay: NumSegments={lv}"
        if lp == "NumNodes":
            return f"AxoneLengthDelay: NumNodes={lv} Internode=2ms"
        return f"AxoneLengthDelay: {model}"
    return "AxoneLengthDelay: PGenerator vs AxoneUnderTest"


def ensure_watch(cell: Path, title: str | None = None) -> None:
    iface = cell / "Interface.xml"
    if not iface.is_file():
        raise SystemExit(f"missing Interface.xml in {cell}")
    text = iface.read_text(encoding="utf-8")
    watch = WATCH_TAB.format(title=resolve_title(cell, title)).strip()
    pat = r"<UGEngineControllWidget\.UWatch\.tab_1>.*?</UGEngineControllWidget\.UWatch\.tab_1>"
    if re.search(pat, text, re.DOTALL):
        text = re.sub(pat, watch, text, count=1, flags=re.DOTALL)
    else:
        if "</Interfaces>" not in text:
            raise SystemExit(f"no </Interfaces> in {iface}")
        text = text.replace("</Interfaces>", watch + "\n</Interfaces>")
    iface.write_text(text, encoding="utf-8")
    if "<schemaVersion>2</schemaVersion>" not in text:
        raise SystemExit(f"missing schemaVersion=2 in {iface}")
    if "<SerieYComponent>PGenerator</SerieYComponent>" not in text:
        raise SystemExit(f"missing PGenerator serie in {iface}")
    if "<SerieYComponent>AxoneUnderTest</SerieYComponent>" not in text:
        raise SystemExit(f"missing AxoneUnderTest serie in {iface}")
    print(f"Watch OK: {iface}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cell", type=Path)
    ap.add_argument("--title", default=None)
    args = ap.parse_args()
    ensure_watch(args.cell, args.title)


if __name__ == "__main__":
    main()

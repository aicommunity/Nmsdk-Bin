#!/usr/bin/env python3
"""Switch LTZone to NPulseLTZone integration mode in test Parameters + Model."""
import re
import sys
from pathlib import Path


def patch_file(path: Path, time_constant: str, threshold: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"<LTZoneClassName Type=\"std::string\" PType=\"257\" IoType=\"17\">[^<]*</LTZoneClassName>",
        '<LTZoneClassName Type="std::string" PType="257" IoType="17">NPulseLTZone</LTZoneClassName>',
        text,
    )
    text = text.replace(
        '<LTZone Class="NPulseLTZoneThreshold">',
        '<LTZone Class="NPulseLTZone">',
    )
    if "<TimeConstant" not in text:
        text = text.replace(
            '<Threshold Type="d" PType="257" IoType="17">0.0115</Threshold>\n'
            '\t\t\t\t\t\t\t\t\t<ThresholdOff',
            f'<Threshold Type="d" PType="257" IoType="17">{threshold}</Threshold>\n'
            f'\t\t\t\t\t\t\t\t\t<TimeConstant Type="d" PType="257" IoType="17">{time_constant}</TimeConstant>\n'
            f'\t\t\t\t\t\t\t\t\t<UseLTZIntegtation Type="b" PType="257" IoType="17">1</UseLTZIntegtation>\n'
            f'\t\t\t\t\t\t\t\t\t<UseSpikeStabilizer Type="b" PType="257" IoType="17">1</UseSpikeStabilizer>\n'
            '\t\t\t\t\t\t\t\t\t<ThresholdOff',
            1,
        )
    else:
        text = re.sub(
            r"<TimeConstant Type=\"d\" PType=\"257\" IoType=\"17\">[^<]*</TimeConstant>",
            f'<TimeConstant Type="d" PType="257" IoType="17">{time_constant}</TimeConstant>',
            text,
        )
    text = re.sub(
        r"(<LTZone Class=\"NPulseLTZone\">[\s\S]*?<Threshold Type=\"d\" PType=\"257\" IoType=\"17\">)[^<]*(</Threshold>)",
        rf"\g<1>{threshold}\2",
        text,
        count=1,
    )
    text = re.sub(
        r"<FixedLTZThreshold Type=\"d\" PType=\"257\" IoType=\"17\">[^<]*</FixedLTZThreshold>",
        f'<FixedLTZThreshold Type="d" PType="257" IoType="17">{threshold}</FixedLTZThreshold>',
        text,
        count=1,
    )
    text = re.sub(
        r"<LTZThreshold Type=\"d\" PType=\"257\" IoType=\"17\">[^<]*</LTZThreshold>",
        f'<LTZThreshold Type="d" PType="257" IoType="17">{threshold}</LTZThreshold>',
        text,
        count=1,
    )
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    d = Path(sys.argv[1])
    tc, thr = sys.argv[2], sys.argv[3]
    patch_file(d / "Parameters_00.xml", tc, thr)
    patch_file(d / "Model_00.xml", tc, thr)

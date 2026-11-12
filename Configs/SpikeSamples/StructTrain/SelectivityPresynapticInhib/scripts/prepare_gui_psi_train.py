#!/usr/bin/env python3
"""Prepare PSI Train Parameters_00.xml for a GUI cold train with autothr.

No extra property edits needed: open Train/Project.ini in NeuroModeler and Start.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_autothr import patch as patch_autothr  # noqa: E402

LEARNER_FIRST = 1


def sub1(text: str, pattern: str, repl: str) -> str:
    new, n = re.subn(pattern, repl, text, count=LEARNER_FIRST)
    if n != 1:
        raise SystemExit(f"replace failed ({n}): {pattern}")
    return new


def upsert_after_need_to_train(text: str) -> str:
    if re.search(
        r'<ResetToUntrainedState Type="b" PType="257" IoType="17">[01]</ResetToUntrainedState>',
        text,
    ):
        return sub1(
            text,
            r'<ResetToUntrainedState Type="b" PType="257" IoType="17">[01]</ResetToUntrainedState>',
            '<ResetToUntrainedState Type="b" PType="257" IoType="17">1</ResetToUntrainedState>',
        )
    return sub1(
        text,
        r'(<IsNeedToTrain Type="b" PType="257" IoType="17">1</IsNeedToTrain>)',
        r'\1\n\t\t\t\t\t<ResetToUntrainedState Type="b" PType="257" IoType="17">1</ResetToUntrainedState>',
    )


def prepare(path: Path) -> None:
    patch_autothr(path)
    text = path.read_text(encoding="utf-8")
    text = sub1(
        text,
        r'<IsNeedToTrain Type="b" PType="257" IoType="17">[01]</IsNeedToTrain>',
        '<IsNeedToTrain Type="b" PType="257" IoType="17">1</IsNeedToTrain>',
    )
    text = upsert_after_need_to_train(text)
    text = sub1(
        text,
        r'<StructureBuildMode Type="i" PType="257" IoType="17">[0-9]</StructureBuildMode>',
        '<StructureBuildMode Type="i" PType="257" IoType="17">1</StructureBuildMode>',
    )
    text = sub1(
        text,
        r'<LTZThreshold Type="d" PType="257" IoType="17">[^<]*</LTZThreshold>',
        '<LTZThreshold Type="d" PType="257" IoType="17">100</LTZThreshold>',
    )
    text = sub1(
        text,
        r'<UseFixedLTZThreshold Type="b" PType="257" IoType="17">[01]</UseFixedLTZThreshold>',
        '<UseFixedLTZThreshold Type="b" PType="257" IoType="17">0</UseFixedLTZThreshold>',
    )
    text = sub1(
        text,
        r'<FixedLTZThreshold Type="d" PType="257" IoType="17">[^<]*</FixedLTZThreshold>',
        '<FixedLTZThreshold Type="d" PType="257" IoType="17">0.0115</FixedLTZThreshold>',
    )
    text = sub1(
        text,
        r'<AttenuationGamma Type="d" PType="257" IoType="17">[^<]*</AttenuationGamma>',
        '<AttenuationGamma Type="d" PType="257" IoType="17">-1</AttenuationGamma>',
    )
    text = sub1(
        text,
        r'<TipSynapseResistance Type="simplevector" Size="4" elemType="d" PType="259" IoType="33">[^<]*</TipSynapseResistance>',
        '<TipSynapseResistance Type="simplevector" Size="4" elemType="d" PType="259" IoType="33">86000000 86000000 86000000 86000000</TipSynapseResistance>',
    )
    text = sub1(
        text,
        r'<DendriteLength Type="simplevector" Size="4" elemType="i" PType="257" IoType="33">[^<]*</DendriteLength>',
        '<DendriteLength Type="simplevector" Size="4" elemType="i" PType="257" IoType="33">1 1 1 1</DendriteLength>',
    )
    text = sub1(
        text,
        r'<InitialSomaPotential Type="simplevector" Size="4" elemType="d" PType="257" IoType="33">[^<]*</InitialSomaPotential>',
        '<InitialSomaPotential Type="simplevector" Size="4" elemType="d" PType="257" IoType="33">0 0 0 0</InitialSomaPotential>',
    )
    if re.search(r'<TrainingPhase Type="i" PType="257" IoType="17">', text):
        text = sub1(
            text,
            r'<TrainingPhase Type="i" PType="257" IoType="17">[^<]*</TrainingPhase>',
            '<TrainingPhase Type="i" PType="257" IoType="17">0</TrainingPhase>',
        )
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        prepare(Path(arg))
        print(f"prepared {arg}")

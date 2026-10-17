#!/usr/bin/env python3
"""Cold-reset a *Dspan* AsymRm EXP copy and set SynapseDissociationTC only.

Never intended for the original 18 EXP — pass DST Train paths only.
SecretionTC / Cap / Rm / Rsyn left as-is (pack A baseline), only Dissoc changes.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def set_tag(text: str, tag: str, value: str, count: int = 1) -> str:
    return re.sub(
        rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)",
        rf"\g<1>{value}\2",
        text,
        count=count,
    )


def cold_and_d(text: str, neuron: str, dissoc: str) -> str:
    tip = "86000000"
    tip4 = f"{tip} {tip} {tip} {tip}"
    t = text
    t = set_tag(t, "IsNeedToTrain", "1", count=1)
    t = set_tag(t, "StructureBuildMode", "1", count=1)
    t = set_tag(t, "NeuronClassName", neuron, count=1)
    t = set_tag(t, "TipSynapseResistance", tip4, count=1)
    t = set_tag(t, "DendriteLength", "1 1 1 1", count=1)
    t = set_tag(t, "NumDendriteMembranePartsVec", "1 1 1 1", count=0)
    t = set_tag(t, "InitialSomaPotential", "0 0 0 0", count=1)
    t = set_tag(t, "UseFixedLTZThreshold", "0", count=1)
    t = set_tag(t, "FixedLTZThreshold", "0.0115", count=1)
    t = set_tag(t, "AutoCalibrateFixedLTZThreshold", "1", count=1)
    # Keep UseElementDefaults=1 so Cap/Rm come from learner params; Dissoc re-applied
    # after each train step (class D001 would otherwise snap Dissoc back to 0.001).
    t = set_tag(t, "UseElementDefaults", "1", count=0)
    if re.search(r"<ResetToUntrainedState\b", t):
        t = set_tag(t, "ResetToUntrainedState", "1", count=1)
    # Only DissociationTC; Secretion unchanged
    t = set_tag(t, "SynapseDissociationTC", dissoc, count=0)
    t = set_tag(t, "DissociationTC", dissoc, count=0)
    return t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-dir", type=Path, required=True)
    ap.add_argument("--dissoc", type=float, required=True)
    ap.add_argument(
        "--neuron",
        default="NSPNeuronGenAsymRmD001C25e12",
    )
    ap.add_argument(
        "--allow-original",
        action="store_true",
        help="Dangerous: allow paths that look like original 18 EXP names",
    )
    args = ap.parse_args()
    train = args.train_dir.resolve()
    exp_name = train.parent.name
    forbidden = re.match(
        r"^EXP_span(25|50|100)ms_pack[ABC]_(gen|preinh)$",
        exp_name,
    )
    if forbidden and not args.allow_original:
        print(
            f"Refuse: looks like original EXP ({exp_name}). "
            "Use a clone (*_Dspan) or --allow-original.",
            file=sys.stderr,
        )
        return 2

    params = train / "Parameters_00.xml"
    model = train / "Model_00.xml"
    if not params.is_file() or not model.is_file():
        print(f"Missing Parameters/Model under {train}", file=sys.stderr)
        return 1

    dissoc = f"{args.dissoc:g}"
    for path in (params, model):
        t = path.read_text(encoding="utf-8")
        t = cold_and_d(t, args.neuron, dissoc)
        if path.name.startswith("Model"):
            t = re.sub(
                r'(<Neuron Class=")[^"]+(">)',
                rf"\g<1>{args.neuron}\2",
                t,
                count=1,
            )
        path.write_text(t, encoding="utf-8")
        print(f"patched {path} Dissoc={dissoc} cold Need=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

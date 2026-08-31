#!/usr/bin/env python3
"""LtzCal reference DendriteLength floors and JSON export for verify/run scripts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Done-state L from AsymRmLtzCal (Pack A span25). span100: no Done ref yet.
REFERENCE_L: dict[str, list[int]] = {
    "EXP_span25ms_packA_gen": [6, 5, 4, 1],
    "EXP_span25ms_packA_preinh": [6, 5, 4, 1],
}

LTZCAL_ROOT = Path(__file__).resolve().parents[2] / "SelectivityLtzCalibrate" / "AsymRmLtzCal"


def load_l_from_params(path: Path) -> list[int] | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<DendriteLength\b[^>]*>([^<]*)</DendriteLength>", text)
    if not m:
        return None
    return [int(float(x.replace(",", "."))) for x in m.group(1).split() if x.strip()]


def build_reference_map() -> dict[str, list[int]]:
    out = dict(REFERENCE_L)
    if LTZCAL_ROOT.is_dir():
        for exp_dir in LTZCAL_ROOT.iterdir():
            if not exp_dir.is_dir():
                continue
            p = exp_dir / "Train" / "Parameters_00.xml"
            l = load_l_from_params(p)
            if l and exp_dir.name.startswith("EXP_"):
                # Only use if Done (IsNeedToTrain=0) or explicit in REFERENCE_L
                text = p.read_text(encoding="utf-8", errors="replace")
                if 'IsNeedToTrain Type="b"' in text or "<IsNeedToTrain" in text:
                    m = re.search(r"<IsNeedToTrain\b[^>]*>([^<]*)</IsNeedToTrain>", text)
                    if m and m.group(1).strip() == "0":
                        out[exp_dir.name] = l
    return out


def get_reference_l(exp: str) -> list[int] | None:
    return build_reference_map().get(exp)


def export_reference_json(path: Path) -> dict[str, list[int]]:
    data = build_reference_map()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def patch_params_floor(params_path: Path, l_ref: list[int], *, dry_run: bool = False) -> list[int]:
    """Raise any non-ref dendrite L below l_ref (does not lower L). Returns new L vector."""
    text = params_path.read_text(encoding="utf-8")
    m = re.search(r"<DendriteLength\b[^>]*>([^<]*)</DendriteLength>", text)
    if not m:
        return []
    l_actual = [int(float(x.replace(",", "."))) for x in m.group(1).split() if x.strip()]
    changed = False
    new_l = list(l_actual)
    for i in range(min(len(new_l), len(l_ref), 3)):  # non-ref 0..2
        if new_l[i] < l_ref[i]:
            new_l[i] = l_ref[i]
            changed = True
    if changed and not dry_run:
        new_s = " ".join(str(x) for x in new_l)
        text = re.sub(
            r"(<DendriteLength\b[^>]*>)[^<]*(</DendriteLength>)",
            rf"\g<1>{new_s}\g<2>",
            text,
            count=1,
        )
        params_path.write_text(text, encoding="utf-8")
    return new_l


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--export", type=Path, help="Write l_reference.json")
    ap.add_argument("--exp", type=str, help="Print reference L for EXP")
    ap.add_argument("params", nargs="*", type=Path, help="Patch Parameters_00.xml floors")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.export:
        data = export_reference_json(args.export)
        print(f"Wrote {args.export} ({len(data)} EXP)")
    if args.exp:
        l = get_reference_l(args.exp)
        print(l if l else "no reference")
    for p in args.params:
        exp = p.parent.parent.name
        l_ref = get_reference_l(exp)
        if not l_ref:
            print(f"skip {exp}: no reference")
            continue
        new_l = patch_params_floor(p, l_ref, dry_run=args.dry_run)
        print(f"{'dry-run ' if args.dry_run else ''}{exp} L -> {new_l}")


if __name__ == "__main__":
    main()

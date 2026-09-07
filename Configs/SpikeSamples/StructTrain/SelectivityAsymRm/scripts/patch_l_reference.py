#!/usr/bin/env python3
"""LtzCal reference DendriteLength floors and JSON export for verify/run scripts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Done-state L from AsymRm Pack A pilots / formula.
# span50: actual Train Done (not historical LtzCal partial floors).
# span100: EstDelay≈0.005 formula for needed [0.1, 0.08333, 0.05] — never Test [1,1,1,1].
REFERENCE_L: dict[str, list[int]] = {
    "EXP_span25ms_packA_gen": [6, 5, 4, 1],
    "EXP_span25ms_packA_preinh": [6, 5, 4, 1],
    "EXP_span50ms_packA_gen": [11, 9, 7, 1],
    "EXP_span50ms_packA_preinh": [11, 9, 6, 1],
    "EXP_span100ms_packA_gen": [20, 17, 10, 1],
    "EXP_span100ms_packA_preinh": [20, 17, 10, 1],
}

LTZCAL_ROOT = Path(__file__).resolve().parents[2] / "SelectivityLtzCalibrate" / "AsymRmLtzCal"
ASYMRM_ROOT = Path(__file__).resolve().parents[1]
GRID_CELLS = ASYMRM_ROOT / "grid_cells.tsv"


def pack_a_alias(exp: str) -> str:
    """Map Pack B/C EXP name to same span+kind Pack A (LtzCal exists only for A)."""
    return exp.replace("_packB_", "_packA_").replace("_packC_", "_packA_")


def is_trivial_l(l: list[int] | None) -> bool:
    """Reject cold/Test Done vectors that are all non-ref ones."""
    if not l or len(l) < 3:
        return True
    return all(x <= 1 for x in l[:3])


def load_l_from_params(path: Path) -> list[int] | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<DendriteLength\b[^>]*>([^<]*)</DendriteLength>", text)
    if not m:
        return None
    return [int(float(x.replace(",", "."))) for x in m.group(1).split() if x.strip()]


def is_need_to_train(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<IsNeedToTrain\b[^>]*>([^<]*)</IsNeedToTrain>", text)
    return m.group(1).strip() if m else None


def build_reference_map() -> dict[str, list[int]]:
    out = {k: list(v) for k, v in REFERENCE_L.items()}
    if not LTZCAL_ROOT.is_dir():
        return out
    for exp_dir in LTZCAL_ROOT.iterdir():
        if not exp_dir.is_dir() or not exp_dir.name.startswith("EXP_"):
            continue
        exp = exp_dir.name
        if exp in out:
            continue
        for sub in ("Train", "Test"):
            p = exp_dir / sub / "Parameters_00.xml"
            if not p.is_file():
                continue
            need = is_need_to_train(p)
            if need != "0":
                continue
            l = load_l_from_params(p)
            if l and not is_trivial_l(l):
                out[exp] = l
                break
    return out


def get_reference_l(exp: str) -> list[int] | None:
    data = build_reference_map()
    if exp in data:
        return list(data[exp])
    alias = pack_a_alias(exp)
    if alias != exp and alias in data:
        return list(data[alias])
    if alias != exp and alias in REFERENCE_L:
        return list(REFERENCE_L[alias])
    return None


def effective_l_target(l_formula: list[int], l_reference: list[int] | None) -> list[int]:
    """Cable sync target: L_reference overrides formula on non-ref dendrites when set."""
    if not l_reference or len(l_reference) != len(l_formula):
        return list(l_formula)
    out = list(l_formula)
    for i in range(min(len(out), len(l_reference))):
        if i >= 3:
            break
        out[i] = l_reference[i]
    return out


def at_l_reference(l_actual: list[int], l_reference: list[int] | None) -> bool:
    """True when every non-ref dendrite is at least L_reference (growth above floor is OK)."""
    if not l_reference or len(l_reference) != len(l_actual):
        return False
    for i in range(min(len(l_actual), 3)):
        if l_actual[i] < l_reference[i]:
            return False
    return True


def grid_exp_names() -> list[str]:
    if not GRID_CELLS.is_file():
        return list(REFERENCE_L.keys())
    names: list[str] = []
    for line in GRID_CELLS.read_text(encoding="utf-8").splitlines()[1:]:
        if not line.strip():
            continue
        names.append(line.split("\t")[0])
    return names


def export_reference_json(path: Path) -> dict[str, list[int]]:
    """Export Pack A refs plus Pack B/C resolved via pack_a_alias."""
    data: dict[str, list[int]] = {}
    for exp in grid_exp_names():
        l = get_reference_l(exp)
        if l:
            data[exp] = l
    # Ensure hardcoded Pack A keys present even if missing from grid.
    for exp, l in REFERENCE_L.items():
        data.setdefault(exp, list(l))
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
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

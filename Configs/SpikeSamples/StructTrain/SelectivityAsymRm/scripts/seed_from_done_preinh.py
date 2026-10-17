#!/usr/bin/env python3
"""Seed TipR + Initial(d0-2) from Done Pack C preinh into Pack C gen (Parameters+Model).

Optional --surgical Rmin / TipR lowering from AmpDtTrace. Never writes preinh or non-gen.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asymrm_train_common import (
    K_NUM_DENDRITES,
    REF_DENDRITE,
    load_trace_vectors,
    load_train_params,
)
from seed_initial_from_ltzcal import format_xml_floats, set_simplevector

CAMPAIGN_ROOT = Path(__file__).resolve().parents[1]
AMP_DT_SURGICAL = 0.05
RMIN_NEAR_MULT = 10.0


def exp_name_from_train_path(train_dir: Path) -> str:
    if train_dir.name in ("Train", "Test"):
        return train_dir.parent.name
    return train_dir.name


def preinh_source_exp(exp: str) -> str:
    if "_packC_gen" not in exp:
        raise ValueError(f"expected packC_gen exp, got {exp!r}")
    return exp.replace("_packC_gen", "_packC_preinh")


def need_train(params_path: Path) -> str | None:
    text = params_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<IsNeedToTrain\b[^>]*>([^<]*)</IsNeedToTrain>", text)
    return m.group(1).strip() if m else None


def patch_vector(path: Path, tag: str, values: list[float], *, dry_run: bool) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if f"<{tag}" not in text:
        return False
    new_text = set_simplevector(text, tag, values)
    if new_text == text:
        return False
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return True


def apply_surgical(
    tip: list[float],
    *,
    preinh_tip: list[float],
    rmin: float,
    amp_dt: list[float],
) -> tuple[list[float], list[str]]:
    out = list(tip)
    notes: list[str] = []
    for i in range(min(len(out), K_NUM_DENDRITES)):
        if i == REF_DENDRITE:
            continue
        ad = abs(float(amp_dt[i])) if i < len(amp_dt) else 0.0
        if ad < AMP_DT_SURGICAL:
            continue
        cur = out[i]
        pref = preinh_tip[i] if i < len(preinh_tip) else cur
        if cur <= rmin * RMIN_NEAR_MULT:
            if cur > rmin * (1.0 + 1e-9):
                out[i] = rmin
                notes.append(f"d{i}: TipR->{rmin:g} (near-Rmin clamp, |amp_dt|={ad:.4g})")
        elif cur > pref > 0.0:
            out[i] = pref
            notes.append(f"d{i}: TipR->{pref:.4g} (preinh lower, |amp_dt|={ad:.4g})")
    return out, notes


def seed_train_dir(
    train_dir: Path,
    *,
    dry_run: bool = False,
    surgical: bool = False,
) -> dict:
    train_dir = train_dir.resolve()
    if train_dir.name == "Parameters_00.xml":
        train_dir = train_dir.parent
    if train_dir.name != "Train":
        train_dir = train_dir / "Train" if (train_dir / "Train").is_dir() else train_dir

    exp = exp_name_from_train_path(train_dir)
    if "_packC_gen" not in exp:
        return {"exp": exp, "ok": False, "error": "target must be *_packC_gen"}

    src_exp = preinh_source_exp(exp)
    src_train = CAMPAIGN_ROOT / src_exp / "Train"
    src_params = src_train / "Parameters_00.xml"
    if not src_params.is_file():
        return {"exp": exp, "ok": False, "error": f"missing source {src_params}"}

    src_need = need_train(src_params)
    if src_need != "0":
        return {
            "exp": exp,
            "ok": False,
            "error": f"source {src_exp} IsNeedToTrain={src_need!r} (want 0)",
        }

    dst_params = train_dir / "Parameters_00.xml"
    if not dst_params.is_file():
        return {"exp": exp, "ok": False, "error": f"missing {dst_params}"}

    # Refuse writing outside packC_gen Train
    resolved = str(train_dir.resolve())
    if "/EXP_" not in resolved or "_packC_gen/Train" not in resolved.replace("\\", "/"):
        # also accept .../EXP_span50ms_packC_gen/Train
        if "_packC_gen" not in resolved or not resolved.endswith("Train"):
            return {"exp": exp, "ok": False, "error": f"refuse write path {train_dir}"}

    src = load_train_params(src_params)
    dst = load_train_params(dst_params)
    tip = list(src.get("TipSynapseResistance") or [])
    while len(tip) < K_NUM_DENDRITES:
        tip.append(tip[-1] if tip else 0.0)
    tip = tip[:K_NUM_DENDRITES]

    init_src = list(src.get("InitialSomaPotential") or [])
    init_dst = list(dst.get("InitialSomaPotential") or [0.0] * K_NUM_DENDRITES)
    while len(init_dst) < K_NUM_DENDRITES:
        init_dst.append(0.0)
    init_after = list(init_dst)
    for i in range(3):  # d0-d2 only
        if i < len(init_src) and init_src[i] > 0.0:
            init_after[i] = init_src[i]

    surgical_notes: list[str] = []
    if surgical:
        rmin = float(dst.get("ResistanceMin") or src.get("ResistanceMin") or 1e6)
        try:
            tr = load_trace_vectors(train_dir)
            amp_dt = tr.get("AmpDtTrace") or []
        except Exception:
            amp_dt = []
        tip, surgical_notes = apply_surgical(
            tip, preinh_tip=list(src.get("TipSynapseResistance") or tip), rmin=rmin, amp_dt=amp_dt
        )

    patched: list[str] = []
    for name in ("Parameters_00.xml", "Model_00.xml"):
        path = train_dir / name
        if patch_vector(path, "TipSynapseResistance", tip, dry_run=dry_run):
            patched.append(f"{path}:TipR")
        if patch_vector(path, "InitialSomaPotential", init_after, dry_run=dry_run):
            patched.append(f"{path}:Initial")

    return {
        "exp": exp,
        "ok": True,
        "source_exp": src_exp,
        "dry_run": dry_run,
        "surgical": surgical,
        "surgical_notes": surgical_notes,
        "tip_before": dst.get("TipSynapseResistance"),
        "tip_after": tip,
        "initial_before": dst.get("InitialSomaPotential"),
        "initial_after": init_after,
        "patched": patched,
        "action": "noop" if not patched else ("dry-run" if dry_run else "patched"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Seed TipR+Initial(d0-2) from Done Pack C preinh into Pack C gen"
    )
    ap.add_argument("train_dirs", nargs="+", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--surgical", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    fail = 0
    for d in args.train_dirs:
        try:
            r = seed_train_dir(d, dry_run=args.dry_run, surgical=args.surgical)
        except Exception as exc:
            r = {"exp": exp_name_from_train_path(d), "ok": False, "error": str(exc)}
        if not r.get("ok"):
            fail += 1
        if args.json:
            print(json.dumps(r))
        else:
            if not r.get("ok"):
                print(f"{r.get('exp')}: FAIL {r.get('error')}", file=sys.stderr)
            else:
                print(
                    f"{r['exp']}: {r['action']} from {r['source_exp']} "
                    f"TipR={r['tip_after']} Init012={r['initial_after'][:3]}"
                )
                for note in r.get("surgical_notes") or []:
                    print(f"  surgical: {note}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

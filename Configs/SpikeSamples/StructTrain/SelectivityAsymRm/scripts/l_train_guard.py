#!/usr/bin/env python3
"""Post-train-step L rollback and L-reference floor guard for adaptive_train_exp."""
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
    initials_ready,
    load_train_params,
    load_trace_vectors,
)
from patch_l_reference import get_reference_l, patch_params_floor


def read_state(train_dir: Path) -> dict:
    p = load_train_params(train_dir / "Parameters_00.xml")
    tr = load_trace_vectors(train_dir)
    return {
        "L": list(p["DendriteLength"]),
        "last_abs_dt": list(tr.get("LastAbsDtTrace", [])),
        "sync_tol": p["SyncTolerance"],
    }


def write_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state), encoding="utf-8")


def patch_dendrite_length(params_path: Path, new_l: list[int]) -> None:
    text = params_path.read_text(encoding="utf-8")
    new_s = " ".join(str(x) for x in new_l)
    text = re.sub(
        r"(<DendriteLength\b[^>]*>)[^<]*(</DendriteLength>)",
        rf"\g<1>{new_s}\g<2>",
        text,
        count=1,
    )
    params_path.write_text(text, encoding="utf-8")


def guard_after_step(
    train_dir: Path,
    prev_state_path: Path,
    *,
    use_l_reference: bool,
    rollback_factor: float = 1.2,
) -> dict:
    """Compare prev vs current; rollback L if decrease worsened sync. Apply L-ref floor."""
    params = train_dir / "Parameters_00.xml"
    exp = train_dir.parent.name
    cur = read_state(train_dir)
    result = {"action": "none", "exp": exp, "L_before": cur["L"], "L_after": cur["L"]}

    if prev_state_path.is_file():
        prev = json.loads(prev_state_path.read_text(encoding="utf-8"))
        tol = cur["sync_tol"]
        new_l = list(cur["L"])
        rolled = False
        for i in range(K_NUM_DENDRITES):
            if i == REF_DENDRITE:
                continue
            pl = prev["L"][i] if i < len(prev["L"]) else 1
            cl = cur["L"][i] if i < len(cur["L"]) else 1
            pdt = prev["last_abs_dt"][i] if i < len(prev.get("last_abs_dt", [])) else 0.0
            cdt = cur["last_abs_dt"][i] if i < len(cur.get("last_abs_dt", [])) else 0.0
            if cl < pl and cdt > max(pdt * 0.99, tol * rollback_factor):
                new_l[i] = pl
                rolled = True
        if rolled:
            patch_dendrite_length(params, new_l)
            patch_continue_train(params)
            result["action"] = "rollback"
            result["L_after"] = new_l
            cur = read_state(train_dir)

    if use_l_reference:
        l_ref = get_reference_l(exp)
        if l_ref:
            p = load_train_params(params)
            if initials_ready(p.get("InitialSomaPotential") or []):
                before = list(cur["L"])
                after = patch_params_floor(params, l_ref)
                if after != before:
                    patch_continue_train(params)
                    result["action"] = "l_floor" if result["action"] == "none" else result["action"] + "+l_floor"
                    result["L_after"] = after
            elif result["action"] == "none":
                result["action"] = "floor_skipped_no_initial"

    write_state(prev_state_path, read_state(train_dir))
    return result


def patch_continue_train(params_path: Path) -> None:
    text = params_path.read_text(encoding="utf-8")

    def set_tag(t: str, tag: str, value: str, count: int = 0) -> str:
        return re.sub(
            rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)",
            rf"\g<1>{value}\g<2>",
            t,
            count=count or 0,
        )

    text = set_tag(text, "ResetToUntrainedState", "0", 0)
    text = set_tag(text, "IsNeedToTrain", "1", 1)
    text = set_tag(text, "StructureBuildMode", "1", 1)
    params_path.write_text(text, encoding="utf-8")


def apply_l_reference_floor(train_dir: Path, *, use_l_reference: bool) -> dict:
    """Raise L to L_reference floor when non-ref Initial anchors are ready."""
    if not use_l_reference:
        return {"action": "none", "L_after": None}
    params = train_dir / "Parameters_00.xml"
    exp = train_dir.parent.name
    l_ref = get_reference_l(exp)
    if not l_ref:
        return {"action": "none", "L_after": None}
    p = load_train_params(params)
    if not initials_ready(p.get("InitialSomaPotential") or []):
        return {
            "action": "floor_skipped_no_initial",
            "exp": exp,
            "L_after": list(p["DendriteLength"]),
        }
    before = p["DendriteLength"]
    after = patch_params_floor(params, l_ref)
    if after != before:
        patch_continue_train(params)
        return {"action": "l_floor", "exp": exp, "L_after": after}
    return {"action": "none", "exp": exp, "L_after": after}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("train_dir", type=Path)
    ap.add_argument("--state", type=Path, default=None, help="JSON state file (prev snapshot)")
    ap.add_argument("--save-before", action="store_true", help="Save current state only")
    ap.add_argument("--apply-floor", action="store_true", help="Raise L to L_reference before train")
    ap.add_argument("--l-reference", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.apply_floor:
        r = apply_l_reference_floor(args.train_dir, use_l_reference=args.l_reference)
        if args.json:
            print(json.dumps(r))
        else:
            print(f"{r.get('action', 'floor')}: L -> {r.get('L_after')}")
        return

    if not args.state:
        ap.error("--state required unless --apply-floor")

    if args.save_before:
        write_state(args.state, read_state(args.train_dir))
        if args.json:
            print(json.dumps({"action": "saved"}))
        return

    r = guard_after_step(args.train_dir, args.state, use_l_reference=args.l_reference)
    if args.json:
        print(json.dumps(r))
    else:
        print(f"{r['exp']}: {r['action']} L={r['L_after']}")


if __name__ == "__main__":
    main()

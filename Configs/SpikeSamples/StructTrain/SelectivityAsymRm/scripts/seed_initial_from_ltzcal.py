#!/usr/bin/env python3
"""Seed InitialSomaPotential (and optionally TipSynapseResistance) from LtzCal reference EXP."""
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
    REF_INITIAL_ANOMALY,
    initials_ready,
    load_train_params,
)

LTZCAL_ROOT = Path(__file__).resolve().parents[2] / "SelectivityLtzCalibrate" / "AsymRmLtzCal"

def exp_name_from_train_path(train_dir: Path) -> str:
    if train_dir.name in ("Train", "Test"):
        return train_dir.parent.name
    return train_dir.name


def ltzcal_ref_params(exp: str, *, prefer_done: bool = True) -> Path | None:
    """Resolve LtzCal params for Initial: prefer Train with valid Initial, else Done Test."""
    train = LTZCAL_ROOT / exp / "Train" / "Parameters_00.xml"
    test = LTZCAL_ROOT / exp / "Test" / "Parameters_00.xml"

    def has_valid_initial(path: Path) -> bool:
        try:
            init = load_train_params(path).get("InitialSomaPotential") or []
            return len(init) >= 3 and all(v > 0.0 for v in init[:3])
        except Exception:
            return False

    if train.is_file() and has_valid_initial(train):
        return train
    if prefer_done and test.is_file():
        text = test.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"<IsNeedToTrain\b[^>]*>([^<]*)</IsNeedToTrain>", text)
        if m and m.group(1).strip() == "0" and has_valid_initial(test):
            return test
    if test.is_file() and has_valid_initial(test):
        return test
    return train if train.is_file() else None


def ltzcal_tip_r_source(exp: str) -> Path | None:
    """Prefer Done Model TipR (preinh Test Model often has tuned TipR)."""
    candidates = [
        LTZCAL_ROOT / exp / "Train" / "Parameters_00.xml",
        LTZCAL_ROOT / exp / "Train" / "Model_00.xml",
        LTZCAL_ROOT / exp / "Test" / "Model_00.xml",
        LTZCAL_ROOT / exp / "Test" / "Parameters_00.xml",
    ]
    best: Path | None = None
    best_score = -1
    for p in candidates:
        if not p.is_file():
            continue
        try:
            tip = load_train_params(p).get("TipSynapseResistance") or []
        except Exception:
            continue
        if len(tip) < 3:
            continue
        # Prefer Done + finite tip R away from Rmax
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"<IsNeedToTrain\b[^>]*>([^<]*)</IsNeedToTrain>", text)
        done = 1 if (m and m.group(1).strip() == "0") else 0
        ok_tips = sum(1 for i in range(3) if tip[i] > 1e6 and tip[i] < 5e10)
        score = done * 10 + ok_tips
        if score > best_score:
            best_score = score
            best = p
    return best


def format_xml_floats(values: list[float]) -> str:
    parts: list[str] = []
    for v in values:
        s = f"{v:.17g}".replace(".", ",")
        parts.append(s)
    return " ".join(parts)


def set_simplevector(text: str, tag: str, values: list[float]) -> str:
    new_s = format_xml_floats(values)
    return re.sub(
        rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)",
        rf"\g<1>{new_s}\g<2>",
        text,
        count=1,
    )


def needs_initial_seed(current: list[float], ref: list[float], *, force: bool) -> list[bool]:
    out = [False] * K_NUM_DENDRITES
    for i in range(K_NUM_DENDRITES):
        cur = current[i] if i < len(current) else 0.0
        r = ref[i] if i < len(ref) else 0.0
        if r <= 0.0:
            continue
        if force:
            out[i] = True
            continue
        if i != REF_DENDRITE:
            if cur <= 0.0:
                out[i] = True
        else:
            if cur <= 0.0 or cur > REF_INITIAL_ANOMALY:
                out[i] = True
    return out


def seed_train_dir(
    train_dir: Path,
    *,
    seed_tip_r: bool = False,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    train_dir = train_dir.resolve()
    params_path = train_dir / "Parameters_00.xml"
    if not params_path.is_file():
        raise FileNotFoundError(params_path)

    exp = exp_name_from_train_path(train_dir)
    ref_path = ltzcal_ref_params(exp)
    if ref_path is None:
        return {"exp": exp, "ok": False, "error": f"LtzCal ref not found for {exp}"}

    cur = load_train_params(params_path)
    ref = load_train_params(ref_path)

    ref_init = ref.get("InitialSomaPotential") or []
    if len(ref_init) < K_NUM_DENDRITES or any(v <= 0.0 for v in ref_init[:3]):
        return {
            "exp": exp,
            "ok": False,
            "error": f"LtzCal Initial invalid in {ref_path}",
            "ref_initial": ref_init,
        }

    want = needs_initial_seed(cur.get("InitialSomaPotential") or [], ref_init, force=force)
    new_init = list(cur.get("InitialSomaPotential") or [0.0] * K_NUM_DENDRITES)
    while len(new_init) < K_NUM_DENDRITES:
        new_init.append(0.0)
    changed_init = False
    for i in range(K_NUM_DENDRITES):
        if want[i]:
            new_init[i] = ref_init[i]
            changed_init = True

    changed_tip = False
    new_tip = list(cur.get("TipSynapseResistance") or [])
    ref_tip = ref.get("TipSynapseResistance") or []
    tip_src = ltzcal_tip_r_source(exp)
    if tip_src is not None:
        try:
            tip_ref_params = load_train_params(tip_src)
            tip_cand = tip_ref_params.get("TipSynapseResistance") or []
            if tip_cand:
                ref_tip = tip_cand
                result_tip_src = str(tip_src)
            else:
                result_tip_src = str(ref_path)
        except Exception:
            result_tip_src = str(ref_path)
    else:
        result_tip_src = str(ref_path)
    if seed_tip_r and ref_tip:
        while len(new_tip) < K_NUM_DENDRITES:
            new_tip.append(0.0)
        for i in range(K_NUM_DENDRITES):
            if i < len(ref_tip) and ref_tip[i] > 0.0:
                if force or new_tip[i] <= cur["ResistanceMin"] * (1 + 1e-6):
                    new_tip[i] = ref_tip[i]
                    changed_tip = True

    result = {
        "exp": exp,
        "ok": True,
        "ref_path": str(ref_path),
        "tip_r_source": result_tip_src if seed_tip_r else None,
        "dry_run": dry_run,
        "changed_initial": changed_init,
        "changed_tip_r": changed_tip,
        "initial_before": cur.get("InitialSomaPotential"),
        "initial_after": new_init if changed_init else cur.get("InitialSomaPotential"),
        "seed_mask": want,
    }

    if (changed_init or changed_tip) and not dry_run:
        text = params_path.read_text(encoding="utf-8")
        if changed_init:
            text = set_simplevector(text, "InitialSomaPotential", new_init)
        if changed_tip:
            text = set_simplevector(text, "TipSynapseResistance", new_tip)
        params_path.write_text(text, encoding="utf-8")
        result["patched"] = str(params_path)
    elif not changed_init and not changed_tip:
        result["action"] = "noop"

    return result


def initials_ready_path(params_path: Path) -> bool:
    p = load_train_params(params_path)
    return initials_ready(p.get("InitialSomaPotential") or [])


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed InitialSomaPotential from LtzCal Done ref")
    ap.add_argument("train_dirs", nargs="+", type=Path, help="EXP .../Train directories")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed-tip-r", action="store_true")
    ap.add_argument("--force", action="store_true", help="Overwrite all Initial (and tip if --seed-tip-r)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check-ready", action="store_true", help="Exit 0 if all dirs have Initial>0 on d0-2")
    args = ap.parse_args()

    if args.check_ready:
        all_ok = True
        for d in args.train_dirs:
            train_dir = d.parent if d.name == "Parameters_00.xml" else d
            if not initials_ready_path(train_dir / "Parameters_00.xml"):
                all_ok = False
        sys.exit(0 if all_ok else 1)

    results = []
    fail = 0
    for d in args.train_dirs:
        train_dir = d
        if d.name == "Parameters_00.xml":
            train_dir = d.parent
        try:
            r = seed_train_dir(
                train_dir,
                seed_tip_r=args.seed_tip_r,
                dry_run=args.dry_run,
                force=args.force,
            )
        except Exception as exc:
            r = {"exp": exp_name_from_train_path(train_dir), "ok": False, "error": str(exc)}
        results.append(r)
        if not r.get("ok"):
            fail += 1
        elif args.json:
            print(json.dumps(r))
        else:
            exp = r["exp"]
            if r.get("action") == "noop":
                print(f"{exp}: noop (Initial already set)")
            elif r.get("dry_run"):
                print(f"{exp}: dry-run would seed Initial -> {r.get('initial_after')}")
            else:
                print(f"{exp}: seeded Initial -> {r.get('initial_after')}")

    if args.json and len(results) > 1:
        print(json.dumps(results, indent=2))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Force-copy TipSynapseResistance from Done Pack B sibling into Pack C (Parameters+Model).

Does not touch Initial, L, SyncTol, FixedLTZ, or UseFixedLTZThreshold.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asymrm_train_common import K_NUM_DENDRITES, load_train_params
from seed_initial_from_ltzcal import format_xml_floats, set_simplevector

CAMPAIGN_ROOT = Path(__file__).resolve().parents[1]


def exp_name_from_train_path(train_dir: Path) -> str:
    if train_dir.name in ("Train", "Test"):
        return train_dir.parent.name
    return train_dir.name


def sibling_pack_b(exp: str) -> str:
    if "_packC_" not in exp:
        raise ValueError(f"expected packC exp, got {exp!r}")
    return exp.replace("_packC_", "_packB_")


def need_train(params_path: Path) -> str | None:
    text = params_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<IsNeedToTrain\b[^>]*>([^<]*)</IsNeedToTrain>", text)
    return m.group(1).strip() if m else None


def read_tip_r(train_dir: Path) -> tuple[list[float], Path]:
    params = train_dir / "Parameters_00.xml"
    model = train_dir / "Model_00.xml"
    if params.is_file():
        tip = load_train_params(params).get("TipSynapseResistance") or []
        if tip and all(v > 0.0 for v in tip[:K_NUM_DENDRITES]):
            return list(tip), params
    if model.is_file():
        tip = load_train_params(model).get("TipSynapseResistance") or []
        if tip:
            return list(tip), model
    raise FileNotFoundError(f"no TipSynapseResistance in {train_dir}")


def patch_tip_r(path: Path, tip: list[float], *, dry_run: bool) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if "<TipSynapseResistance" not in text:
        return False
    new_text = set_simplevector(text, "TipSynapseResistance", tip)
    if new_text == text:
        return False
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return True


def seed_train_dir(train_dir: Path, *, dry_run: bool = False) -> dict:
    train_dir = train_dir.resolve()
    if train_dir.name == "Parameters_00.xml":
        train_dir = train_dir.parent
    exp = exp_name_from_train_path(train_dir)
    src_exp = sibling_pack_b(exp)
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

    tip, tip_src = read_tip_r(src_train)
    while len(tip) < K_NUM_DENDRITES:
        tip.append(tip[-1] if tip else 0.0)
    tip = tip[:K_NUM_DENDRITES]

    before = load_train_params(train_dir / "Parameters_00.xml").get("TipSynapseResistance")
    patched: list[str] = []
    for name in ("Parameters_00.xml", "Model_00.xml"):
        path = train_dir / name
        if patch_tip_r(path, tip, dry_run=dry_run):
            patched.append(str(path))

    return {
        "exp": exp,
        "ok": True,
        "source_exp": src_exp,
        "tip_r_source": str(tip_src),
        "dry_run": dry_run,
        "tip_before": before,
        "tip_after": tip,
        "tip_formatted": format_xml_floats(tip),
        "patched": patched,
        "action": "noop" if not patched else ("dry-run" if dry_run else "patched"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Force TipR from Done Pack B sibling into Pack C Train (Parameters+Model)"
    )
    ap.add_argument("train_dirs", nargs="+", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    results = []
    fail = 0
    for d in args.train_dirs:
        try:
            r = seed_train_dir(d, dry_run=args.dry_run)
        except Exception as exc:
            r = {"exp": exp_name_from_train_path(d), "ok": False, "error": str(exc)}
        results.append(r)
        if not r.get("ok"):
            fail += 1
        if args.json:
            print(json.dumps(r))
        else:
            if not r.get("ok"):
                print(f"{r.get('exp')}: FAIL {r.get('error')}", file=sys.stderr)
            elif r.get("action") == "noop":
                print(f"{r['exp']}: noop (TipR already matched)")
            else:
                print(
                    f"{r['exp']}: {r['action']} TipR from {r['source_exp']} -> {r['tip_after']}"
                )

    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

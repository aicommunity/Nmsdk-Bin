#!/usr/bin/env python3
"""Patch EstDelayPerSeg in SoftCold-source PhaseA/PSI archives (plan §1).

SoftCold with default EstDelay=0.005 grows L to ~1+T/0.005 (often ~97) while gold
DendriteLength is shorter. Set EstDelay = T/(L_gold-1) with T inferred from the
known SoftCold runaway length under default EstDelay (W4 observations).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from posttune_verify import CASES  # noqa: E402
from repro_cold_lib import get_tag, set_tag_all  # noqa: E402

# SoftCold dend0 L under EstDelay default 0.005 (W4 matrix). Missing → 97.
SOFTCOLD_L0_DEFAULT_EST = {
    "pa00_baseline": 97,
    "pa01_ltz_sweep": 97,
    "pa02_ltzone_avg": 97,
    "pa06_ltzone_int": 97,
    "psi01_050": 97,
    "psi14_260": 100,
    "psi15_270": 100,
    "psi21_100": 20,
    "psi31_200": 41,
    "psi32_300": 63,
    "psi33_300": 67,
    "psi34_400": 79,
    "psi35_400": 89,
}
K_DELAY_DEFAULT = 0.005

ESTDELAY_BLOCK = (
    '<EstDelayPerSeg Type="d" PType="257" IoType="17">{value}</EstDelayPerSeg>'
)


def parse_len0(params_text: str) -> int:
    raw = get_tag(params_text, "DendriteLength")
    if not raw:
        raise ValueError("DendriteLength missing")
    parts = [int(float(x)) for x in raw.replace(",", " ").split()]
    if not parts or parts[0] <= 1:
        raise ValueError(f"bad DendriteLength: {raw!r}")
    return parts[0]


def insert_estdelay(text: str, value: str) -> str:
    if re.search(r"<EstDelayPerSeg\b", text):
        return set_tag_all(text, "EstDelayPerSeg", value)
    block = ESTDELAY_BLOCK.format(value=value)
    if re.search(r"</DendriteLength>", text):
        return re.sub(r"(</DendriteLength>)", rf"\1\n\t\t\t\t\t{block}", text, count=1)
    if re.search(r"</ResistanceMax>", text):
        return re.sub(r"(</ResistanceMax>)", rf"\1\n\t\t\t\t\t{block}", text, count=1)
    raise ValueError("no insertion anchor for EstDelayPerSeg")


def patch_case(case_name: str, *, dry_run: bool) -> dict:
    case = CASES[case_name]
    archive: Path = case["root"]
    gold: Path = case.get("gold") or archive
    gold_params = (gold / "Train" / "Parameters_00.xml").read_text(encoding="utf-8")
    L0 = parse_len0(gold_params)
    L_soft = SOFTCOLD_L0_DEFAULT_EST.get(case_name, 97)
    T = (L_soft - 1) * K_DELAY_DEFAULT
    est = T / (L0 - 1)
    est_s = f"{est:.16g}"
    rows = []
    for rel in ("Train/Parameters_00.xml", "Train/Model_00.xml"):
        path = archive / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        new = insert_estdelay(text, est_s)
        if new != text and not dry_run:
            path.write_text(new, encoding="utf-8")
        rows.append({"path": str(path.relative_to(ROOT)), "changed": new != text})
    return {
        "case": case_name,
        "L0_gold": L0,
        "L_soft_obs": L_soft,
        "T": T,
        "EstDelayPerSeg": est,
        "files": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--case", action="append", default=[])
    args = ap.parse_args()
    names = args.case or sorted(
        n for n in CASES if n.startswith("pa") or n.startswith("psi")
    )
    # Never touch phase6_* here
    names = [n for n in names if not n.startswith("phase6")]
    print("| case | L0_gold | L_soft | T | EstDelayPerSeg | files |")
    print("|------|--------:|-------:|--:|---------------:|-------|")
    for name in names:
        info = patch_case(name, dry_run=args.dry_run)
        files = ",".join(
            ("*" if f["changed"] else ".") + Path(f["path"]).name for f in info["files"]
        )
        print(
            f"| {info['case']} | {info['L0_gold']} | {info['L_soft_obs']} | "
            f"{info['T']:.6g} | {info['EstDelayPerSeg']:.8g} | {files} |"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

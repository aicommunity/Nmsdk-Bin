#!/usr/bin/env python3
"""Fingerprint Done EXP Train Parameters for anti-regression checks."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asymrm_train_common import load_train_params

CAMPAIGN_ROOT = Path(__file__).resolve().parents[1]


def need_train(params_path: Path) -> str | None:
    text = params_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<IsNeedToTrain\b[^>]*>([^<]*)</IsNeedToTrain>", text)
    return m.group(1).strip() if m else None


def use_fixed(params_path: Path) -> str | None:
    text = params_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<UseFixedLTZThreshold\b[^>]*>([^<]*)</UseFixedLTZThreshold>", text)
    return m.group(1).strip() if m else None


def round_floats(vals: list[float] | None, n: int = 6) -> list[float]:
    if not vals:
        return []
    return [round(float(v), n) for v in vals]


def fingerprint_exp(train_params: Path) -> dict | None:
    need = need_train(train_params)
    if need != "0":
        return None
    p = load_train_params(train_params)
    tip = round_floats(p.get("TipSynapseResistance") or [], 4)
    init = round_floats((p.get("InitialSomaPotential") or [])[:3], 6)
    L = p.get("DendriteLength") or []
    fltz = p.get("FixedLTZThreshold")
    try:
        fltz_r = round(float(fltz), 9) if fltz is not None else None
    except (TypeError, ValueError):
        fltz_r = fltz
    row = {
        "IsNeedToTrain": need,
        "UseFixedLTZThreshold": use_fixed(train_params),
        "FixedLTZThreshold": fltz_r,
        "DendriteLength": list(L),
        "TipSynapseResistance": tip,
        "InitialSomaPotential_d012": init,
    }
    blob = json.dumps(row, sort_keys=True, separators=(",", ":"))
    row["sha256"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return row


def collect(campaign_root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for params in sorted(campaign_root.glob("EXP_*/Train/Parameters_00.xml")):
        exp = params.parent.parent.name
        row = fingerprint_exp(params)
        if row is not None:
            out[exp] = row
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Fingerprint Done AsymRm EXP for regression checks")
    ap.add_argument("--campaign-root", type=Path, default=CAMPAIGN_ROOT)
    ap.add_argument("--write", type=Path, help="Write fingerprint JSON")
    ap.add_argument("--diff", type=Path, help="Compare against prior fingerprint JSON; exit 1 on regression")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    current = collect(args.campaign_root)
    if args.write:
        args.write.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.write} ({len(current)} Done EXP)")

    if args.diff:
        if not args.diff.is_file():
            print(f"missing baseline {args.diff}", file=sys.stderr)
            sys.exit(2)
        baseline = json.loads(args.diff.read_text(encoding="utf-8"))
        regressions: list[str] = []
        for exp, base_row in baseline.items():
            cur = current.get(exp)
            if cur is None:
                regressions.append(f"{exp}: was Done, now missing/Need!=0")
                continue
            if cur.get("sha256") != base_row.get("sha256"):
                regressions.append(f"{exp}: fingerprint changed")
        for exp in current:
            if exp not in baseline:
                # Newly Done is OK (progress), not a regression of prior Done
                pass
        if regressions:
            print("REGRESSION:", file=sys.stderr)
            for line in regressions:
                print(f"  {line}", file=sys.stderr)
            sys.exit(1)
        print(f"OK: {len(baseline)} Done fingerprints unchanged")
        sys.exit(0)

    if args.json and not args.write:
        print(json.dumps(current, indent=2))
    elif not args.write and not args.diff:
        print(f"Done EXP: {len(current)}")
        for exp in sorted(current):
            print(f"  {exp} {current[exp]['sha256'][:12]} FixedLTZ={current[exp]['FixedLTZThreshold']}")


if __name__ == "__main__":
    main()

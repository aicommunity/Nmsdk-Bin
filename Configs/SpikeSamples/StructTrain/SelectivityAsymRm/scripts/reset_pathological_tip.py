#!/usr/bin/env python3
"""Reset pathological TipSynapseResistance on Pack C gen only (H1 lever).

Criteria (non-ref dendrites):
  - TipR >= 0.99 * ResistanceMax, or
  - |AmpDtTrace[i]| > amp_dt_abs_threshold (default 1.0), or
  - NoImproveResistanceTrace[i] >= osc_no_improve (default 20) and |amp_dt| < 0.005
    (hard AMP_OSCILLATION without pathological |amp_dt|)

Replacement: median of healthy non-ref tips on the same EXP.
Falls back to ResistanceMin*50.

Writes Train Parameters + Model TipSynapseResistance. Never touches preinh or Done EXP.
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asymrm_train_common import REF_DENDRITE, load_trace_vectors, load_train_params
from seed_initial_from_ltzcal import set_simplevector

ALLOWED = {"EXP_span50ms_packC_gen", "EXP_span100ms_packC_gen"}


def exp_from_train(train_dir: Path) -> str:
    return train_dir.parent.name if train_dir.name == "Train" else train_dir.name


def patch_tip(path: Path, tip: list[float], *, dry_run: bool) -> bool:
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


def healthy_median(
    tip: list[float],
    bad: set[int],
    rmax: float,
    no_improve: list[float],
    amp_dt: list[float],
    osc_ni: float,
) -> float | None:
    vals = []
    for i, v in enumerate(tip):
        if i == REF_DENDRITE or i in bad:
            continue
        if v >= rmax * 0.99:
            continue
        ni = float(no_improve[i]) if i < len(no_improve) else 0.0
        ad = abs(float(amp_dt[i])) if i < len(amp_dt) else 0.0
        if ni >= osc_ni and ad < 0.005:
            continue
        vals.append(float(v))
    if not vals:
        return None
    return float(statistics.median(vals))


def reset_exp(
    train_dir: Path,
    *,
    amp_dt_thr: float,
    osc_no_improve: float,
    dry_run: bool,
) -> dict:
    exp = exp_from_train(train_dir)
    if exp not in ALLOWED:
        raise SystemExit(f"refuse non-whitelist exp: {exp}")
    params = train_dir / "Parameters_00.xml"
    model = train_dir / "Model_00.xml"
    p = load_train_params(params)
    tip = list(p.get("TipSynapseResistance") or [])
    rmax = float(p.get("ResistanceMax") or 1e11)
    rmin = float(p.get("ResistanceMin") or 1e6)
    traces = load_trace_vectors(train_dir) or {}
    amp_dt = list(traces.get("AmpDtTrace") or [0.0] * len(tip))
    no_improve = list(traces.get("NoImproveResistanceTrace") or [0.0] * len(tip))
    notes: list[str] = []
    bad: set[int] = set()
    for i in range(len(tip)):
        if i == REF_DENDRITE:
            continue
        ad = abs(float(amp_dt[i])) if i < len(amp_dt) else 0.0
        ni = float(no_improve[i]) if i < len(no_improve) else 0.0
        at_rmax = float(tip[i]) >= rmax * 0.99
        hard_osc = ni >= osc_no_improve and ad < 0.005
        if at_rmax or ad > amp_dt_thr or hard_osc:
            bad.add(i)
            reason = []
            if at_rmax:
                reason.append("Rmax")
            if ad > amp_dt_thr:
                reason.append(f"|amp|={ad:.4g}")
            if hard_osc:
                reason.append(f"hard_OSC ni={ni:g}")
            notes.append(
                f"d{i}: TipR={tip[i]:.6g} amp_dt={amp_dt[i] if i < len(amp_dt) else 'n/a'} "
                f"({','.join(reason)})"
            )
    if not bad:
        return {"exp": exp, "changed": False, "notes": ["no pathological tip"]}

    repl = healthy_median(tip, bad, rmax, no_improve, amp_dt, osc_no_improve)
    if repl is None:
        repl = rmin * 50.0
    new_tip = list(tip)
    for i in bad:
        notes.append(f"d{i}: TipR {tip[i]:.6g} -> {repl:.6g}")
        new_tip[i] = repl

    wrote_p = patch_tip(params, new_tip, dry_run=dry_run)
    wrote_m = patch_tip(model, new_tip, dry_run=dry_run)
    return {
        "exp": exp,
        "changed": wrote_p or wrote_m or dry_run,
        "wrote_params": wrote_p,
        "wrote_model": wrote_m,
        "tip_before": tip,
        "tip_after": new_tip,
        "notes": notes,
        "dry_run": dry_run,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("trains", nargs="+", type=Path, help="Train dirs or EXP roots")
    ap.add_argument("--amp-dt-thr", type=float, default=1.0)
    ap.add_argument("--osc-no-improve", type=float, default=20.0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    results = []
    for t in args.trains:
        train = t / "Train" if (t / "Train").is_dir() else t
        results.append(
            reset_exp(
                train,
                amp_dt_thr=args.amp_dt_thr,
                osc_no_improve=args.osc_no_improve,
                dry_run=args.dry_run,
            )
        )

    if args.json:
        import json

        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(r["exp"], "changed=" + str(r["changed"]))
            for n in r["notes"]:
                print(" ", n)


if __name__ == "__main__":
    main()

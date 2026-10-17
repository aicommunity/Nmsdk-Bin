#!/usr/bin/env python3
"""Verify Train Parameters after -S: Done + AutoCalibrate applied (not cold FixedLTZ)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

COLD_FIXED_LTZ = 0.0115


def read_tag(path: Path, tag: str) -> str | None:
    t = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", t)
    return m.group(1).strip() if m else None


def parse_ints(s: str) -> list[int]:
    return [int(float(x.replace(",", "."))) for x in re.split(r"\s+", s.strip()) if x]


def load_peak_sync_json(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return data
    out: dict[str, dict] = {}
    for row in data:
        exp = row.get("exp") or Path(row.get("train_dir", "")).parent.name
        out[exp] = row
    return out


def load_l_target_json(path: Path) -> dict[str, list[int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        out: dict[str, list[int]] = {}
        for row in data:
            exp = row.get("exp") or Path(row.get("params", "")).parent.parent.name
            out[exp] = row.get("L_target", [])
        return out
    return data


def load_l_reference_json(path: Path) -> dict[str, list[int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
        return data
    return {}


def check_params(
    path: Path,
    *,
    require_calibrated: bool = False,
    l_target: list[int] | None = None,
    require_sync_ok: bool = False,
    l_sync_peak: list[int] | None = None,
    l_reference: list[int] | None = None,
) -> dict:
    fails: list[str] = []
    warns: list[str] = []
    need = read_tag(path, "IsNeedToTrain")
    phase = read_tag(path, "TrainingPhase")
    L = read_tag(path, "DendriteLength") or ""
    flt_s = read_tag(path, "FixedLTZThreshold") or "0"
    cal_s = read_tag(path, "CalibratedFixedLTZThreshold")
    auto = read_tag(path, "AutoCalibrateFixedLTZThreshold")
    tip = read_tag(path, "TipSynapseResistance") or ""

    try:
        flt = float(flt_s)
    except ValueError:
        flt = float("nan")
        fails.append(f"FixedLTZThreshold unparseable: {flt_s!r}")
    try:
        cal = float(cal_s) if cal_s is not None else 0.0
    except ValueError:
        cal = 0.0
        warns.append(f"CalibratedFixedLTZThreshold unparseable: {cal_s!r}")

    if need != "0":
        fails.append(f"IsNeedToTrain={need!r} (want 0)")
    if phase is not None and phase != "2":
        fails.append(f"TrainingPhase={phase!r} (want 2)")
    if abs(flt - COLD_FIXED_LTZ) < 1e-9:
        fails.append(f"FixedLTZThreshold still cold default {COLD_FIXED_LTZ}")
    if L.strip() == "1 1 1 1":
        fails.append(f"DendriteLength still cold {L!r}")
    if l_target is not None:
        l_actual = parse_ints(L)
        if l_actual != l_target:
            fails.append(
                f"DendriteLength {l_actual} != L_target {l_target}"
            )
    if require_sync_ok:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / "SelectivityAsymRm/scripts"))
            from asymrm_train_common import all_non_ref_sync_ok, load_trace_vectors

            traces = load_trace_vectors(path.parent)
            sync_tol = float(read_tag(path, "SyncTolerance") or "0.02")
            last_dt = traces.get("LastAbsDtTrace", [])
            if not all_non_ref_sync_ok(last_dt, sync_tol):
                fails.append(f"Not all non-ref dendrites sync_ok (LastAbsDt={last_dt})")
        except Exception as exc:
            warns.append(f"sync_ok check failed: {exc}")
    if l_sync_peak is not None:
        l_actual = parse_ints(L)
        if l_actual != l_sync_peak:
            warns.append(f"DendriteLength {l_actual} != L_sync_peak {l_sync_peak}")
    if l_reference is not None:
        l_actual = parse_ints(L)
        for i, (la, lr) in enumerate(zip(l_actual, l_reference)):
            if i >= 3:
                break
            if la < lr:
                warns.append(f"DendriteLength dend{i}={la} < L_reference={lr}")
    if require_calibrated or cal_s is not None:
        if cal <= 0 and abs(flt - COLD_FIXED_LTZ) < 1e-9:
            fails.append("CalibratedFixedLTZThreshold missing/<=0 with cold FixedLTZ")
        elif cal <= 0 and cal_s is None:
            warns.append("CalibratedFixedLTZThreshold tag absent")
        elif cal <= 0:
            if require_calibrated:
                fails.append(f"CalibratedFixedLTZThreshold={cal_s!r} <= 0")
            else:
                warns.append(f"CalibratedFixedLTZThreshold={cal_s!r} <= 0")
    if auto is not None and auto != "1":
        warns.append(f"AutoCalibrateFixedLTZThreshold={auto!r}")
    tip0 = tip.replace(",", ".").split()
    if tip0 and tip0[0] in ("86000000", "86000000.0"):
        warns.append("TipSynapseResistance tip0 still 86e6 (may be ok if train early)")

    ok = len(fails) == 0
    return {
        "path": str(path),
        "ok": ok,
        "fails": fails,
        "warns": warns,
        "IsNeedToTrain": need,
        "TrainingPhase": phase,
        "DendriteLength": L,
        "FixedLTZThreshold": flt_s,
        "CalibratedFixedLTZThreshold": cal_s,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("params", nargs="*", type=Path, help="Train Parameters_00.xml")
    ap.add_argument("--meta", type=Path, default=None)
    ap.add_argument("--grid", type=Path, default=None, help="Grid root with EXP_*/Train")
    ap.add_argument("--strict", action="store_true", help="Treat warns as fails")
    ap.add_argument("--require-calibrated", action="store_true")
    ap.add_argument("--diagnose", action="store_true", help="Run analyze_train_stall on FAIL")
    ap.add_argument("--require-sync-ok", action="store_true", help="Require all non-ref LastAbsDt sync_ok")
    ap.add_argument("--peak-sync", type=Path, default=None, help="JSON from analyze_peak_sync.py")
    ap.add_argument("--L-target", type=Path, default=None, help="JSON from check_timing_feasibility")
    ap.add_argument("--L-reference", type=Path, default=None, help="JSON from patch_l_reference.py --export")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    l_targets: dict[str, list[int]] = {}
    l_references: dict[str, list[int]] = {}
    peak_sync: dict[str, dict] = {}
    if args.L_target and args.L_target.exists():
        l_targets = load_l_target_json(args.L_target)
    if args.L_reference and args.L_reference.exists():
        l_references = load_l_reference_json(args.L_reference)
    if args.peak_sync and args.peak_sync.exists():
        peak_sync = load_peak_sync_json(args.peak_sync)

    diagnose_script = Path(__file__).resolve().parents[1].parent / "SelectivityAsymRm/scripts/analyze_train_stall.py"

    paths: list[Path] = list(args.params)
    if args.meta and args.grid:
        lines = args.meta.read_text(encoding="utf-8").strip().splitlines()[1:]
        for ln in lines:
            if not ln.strip():
                continue
            exp = ln.split("\t")[0]
            paths.append(args.grid / exp / "Train" / "Parameters_00.xml")

    if not paths:
        ap.error("provide Parameters paths or --meta + --grid")

    results = []
    exit_fail = False
    for p in paths:
        if not p.exists():
            r = {"path": str(p), "ok": False, "fails": ["missing file"], "warns": []}
        else:
            exp = p.parent.parent.name
            lt = l_targets.get(exp)
            lr = l_references.get(exp)
            ps = peak_sync.get(exp, {})
            lsp = ps.get("L_sync_peak") or ps.get("L_actual")
            r = check_params(
                p,
                require_calibrated=args.require_calibrated,
                l_target=lt,
                require_sync_ok=args.require_sync_ok,
                l_sync_peak=lsp,
                l_reference=lr,
            )
            if args.strict and r["warns"]:
                r["fails"].extend(r["warns"])
                r["warns"] = []
                r["ok"] = False
        results.append(r)
        if not r["ok"]:
            exit_fail = True
            if args.diagnose and diagnose_script.is_file() and p.exists():
                import subprocess

                subprocess.run(
                    [sys.executable, str(diagnose_script), str(p.parent)],
                    check=False,
                )
        status = "OK" if r["ok"] else "FAIL"
        print(f"{status} {p}")
        print(f"  L={r.get('DendriteLength')} FixedLTZ={r.get('FixedLTZThreshold')} "
              f"NeedTrain={r.get('IsNeedToTrain')} Phase={r.get('TrainingPhase')}")
        for f in r.get("fails", []):
            print(f"  FAIL: {f}")
        for w in r.get("warns", []):
            print(f"  WARN: {w}")

    if args.json:
        print(json.dumps(results, indent=2))
    sys.exit(1 if exit_fail else 0)


if __name__ == "__main__":
    main()

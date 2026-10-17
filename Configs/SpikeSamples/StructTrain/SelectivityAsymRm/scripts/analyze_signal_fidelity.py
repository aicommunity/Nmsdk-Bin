#!/usr/bin/env python3
"""Signal shape / fidelity metrics vs reference JSON for AsymRm train runs."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from asymrm_train_common import (
    K_NUM_DENDRITES,
    REF_DENDRITE,
    all_non_ref_sync_ok,
    analyze_peak_shape,
    compute_needed_delays,
    delay_len_of,
    estimate_est_delay_from_l,
    length_sync_ok,
    list_statistic_dirs,
    load_train_params,
    load_trace_vectors,
    parse_console_iterations,
    parse_trace_tail_rows,
    resolve_trace_path,
)

PEAK_INVALID_SENTINEL = 1.501


def count_l_oscillations(rows: list[tuple[float, list[float]]], dend: int) -> int:
    if not rows or dend < 0:
        return 0
    prev: int | None = None
    transitions = 0
    for _, vals in rows:
        if len(vals) <= dend:
            continue
        cur = int(round(vals[dend]))
        if prev is not None and cur != prev:
            transitions += 1
        prev = cur
    return transitions


def count_local_maxima(amps: list[float]) -> int:
    if len(amps) < 3:
        return 0 if len(amps) < 2 else (1 if amps[0] > amps[1] else 0)
    n = 0
    for i in range(1, len(amps) - 1):
        if amps[i] >= amps[i - 1] and amps[i] >= amps[i + 1]:
            n += 1
    return n


def tip_r_headroom(tip_r: float, rmin: float, rmax: float) -> dict[str, float]:
    if rmax <= rmin:
        return {"ratio_min": 0.0, "ratio_max": 0.0, "at_rmin": 0.0, "at_rmax": 0.0}
    return {
        "ratio_min": tip_r / rmin if rmin > 0 else 0.0,
        "ratio_max": tip_r / rmax if rmax > 0 else 0.0,
        "at_rmin": 1.0 if tip_r <= rmin * 1.01 else 0.0,
        "at_rmax": 1.0 if tip_r >= rmax * 0.99 else 0.0,
    }


def peak_valid_from_console(train_dir: Path, dend: int) -> bool | None:
    iters = parse_console_iterations(train_dir / "run_console.log")
    if not iters:
        return None
    last = iters[-1]
    pv = last.get("peak_valid") or []
    if dend >= len(pv):
        return None
    return bool(pv[dend])


def analyze_run(
    train_dir: Path,
    *,
    stat_dir: Path | None = None,
    reference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    train_dir = Path(train_dir)
    params_path = train_dir / "Parameters_00.xml"
    p = load_train_params(params_path)
    exp = train_dir.parent.name
    stat = stat_dir or (list_statistic_dirs(train_dir)[-1] if list_statistic_dirs(train_dir) else None)

    traces = load_trace_vectors(train_dir, stat_dir=stat) if stat else {}
    last_abs_dt = traces.get("LastAbsDtTrace", [0.0] * K_NUM_DENDRITES)
    tip_r = traces.get("TipSynapseResistanceTrace", [])
    l_trace_tail: list[tuple[float, list[float]]] = []
    if stat:
        lp = resolve_trace_path(stat, "DendriteLengthTrace")
        if lp:
            l_trace_tail = parse_trace_tail_rows(lp, tail_rows=5000)

    soma_rows: list[tuple[float, list[float]]] = []
    if stat:
        sp = resolve_trace_path(stat, "SomaNeuronAmplitude")
        if sp:
            soma_rows = parse_trace_tail_rows(sp, tail_rows=2000)
    shapes = analyze_peak_shape(soma_rows)

    expected = p["Expected"]
    est = estimate_est_delay_from_l(expected, p["DendriteLength"]) or 0.005
    needed = compute_needed_delays(expected)

    dend_metrics: list[dict[str, Any]] = []
    for i in range(K_NUM_DENDRITES):
        amps = [vals[i] for _, vals in soma_rows if len(vals) > i]
        dt = last_abs_dt[i] if i < len(last_abs_dt) else PEAK_INVALID_SENTINEL
        pv_console = peak_valid_from_console(train_dir, i)
        peak_valid = pv_console if pv_console is not None else (dt < PEAK_INVALID_SENTINEL)
        if i == REF_DENDRITE:
            sync_ok = True
        else:
            sync_ok = length_sync_ok(dt, p["SyncTolerance"]) and peak_valid

        shape = shapes[i] if i < len(shapes) else {"peak_shape": "invalid"}
        tr = tip_r[i] if i < len(tip_r) else 0.0
        hr = tip_r_headroom(tr, p["ResistanceMin"], float(p["ResistanceMax"]))

        row: dict[str, Any] = {
            "dendrite": i,
            "L": p["DendriteLength"][i] if i < len(p["DendriteLength"]) else 1,
            "needed_delay": needed[i] if i < len(needed) else 0.0,
            "delay_len": delay_len_of(p["DendriteLength"][i] if i < len(p["DendriteLength"]) else 1, est),
            "last_abs_dt": dt,
            "sync_ok": sync_ok,
            "peak_valid": peak_valid,
            "peak_shape": shape.get("peak_shape", "invalid"),
            "peak_amp_max": shape.get("max_amp", 0.0),
            "n_extrema": count_local_maxima(amps),
            "L_oscillation_count": count_l_oscillations(l_trace_tail, i),
            "tip_R": tr,
            **hr,
        }
        if i < len(amps) - 1 and amps[i + 1] > 1e-12:
            row["amp_ratio_next"] = amps[i] / amps[i + 1] if amps[i] > 0 else 0.0
        dend_metrics.append(row)

    integrity: dict[str, Any] = {"stat_dir": str(stat) if stat else None}
    if stat:
        for name in ("LastAbsDtTrace", "DendriteLengthTrace", "SomaNeuronAmplitude"):
            tp = resolve_trace_path(stat, name)
            if tp and tp.is_file():
                integrity[f"{name}_lines"] = sum(1 for _ in tp.open("rb"))
                integrity[f"{name}_bytes"] = tp.stat().st_size

    out: dict[str, Any] = {
        "exp": exp,
        "train_dir": str(train_dir),
        "IsNeedToTrain": p.get("IsNeedToTrain"),
        "SyncTolerance": p["SyncTolerance"],
        "DendriteLength": p["DendriteLength"],
        "all_non_ref_sync_ok": all_non_ref_sync_ok(last_abs_dt, p["SyncTolerance"]),
        "dendrites": dend_metrics,
        "integrity": integrity,
    }

    if reference:
        out["fidelity"] = compare_to_reference(out, reference)
    return out


def compare_to_reference(run: dict[str, Any], ref: dict[str, Any]) -> dict[str, Any]:
    tol_dt = float(ref.get("sync_tolerance_max", run.get("SyncTolerance", 0.02)))
    tol_l_osc = int(ref.get("L_oscillation_max", 0))
    shapes_ok = set(ref.get("peak_shapes_ok", ["sharp", "moderate"]))
    dend_ref = ref.get("dendrites", {})
    issues: list[str] = []
    ok = True

    for d in run.get("dendrites", []):
        idx = str(d["dendrite"])
        if d["dendrite"] == REF_DENDRITE:
            continue
        if not d.get("peak_valid"):
            issues.append(f"d{d['dendrite']}:peak_invalid")
            ok = False
        if not d.get("sync_ok"):
            issues.append(f"d{d['dendrite']}:sync_fail dt={d.get('last_abs_dt')}")
            ok = False
        if d.get("peak_shape") not in shapes_ok:
            ref_d = dend_ref.get(idx, {})
            if ref_d.get("peak_shape") != d.get("peak_shape"):
                issues.append(f"d{d['dendrite']}:shape={d.get('peak_shape')}")
                ok = False
        if d.get("L_oscillation_count", 0) > tol_l_osc:
            issues.append(f"d{d['dendrite']}:L_osc={d.get('L_oscillation_count')}")
            ok = False
        r = dend_ref.get(idx, {})
        if "L" in r and d.get("L") != r["L"]:
            issues.append(f"d{d['dendrite']}:L={d.get('L')} want={r['L']}")
            ok = False

    return {"signal_fidelity_ok": ok, "issues": issues, "tolerance_dt": tol_dt}


def build_reference_from_run(run: dict[str, Any], *, exp: str) -> dict[str, Any]:
    dend_ref = {}
    for d in run.get("dendrites", []):
        dend_ref[str(d["dendrite"])] = {
            "L": d["L"],
            "last_abs_dt_max": d["last_abs_dt"],
            "peak_shape": d["peak_shape"],
        }
    return {
        "exp": exp,
        "source": run.get("train_dir"),
        "sync_tolerance_max": run.get("SyncTolerance"),
        "L_oscillation_max": 0,
        "peak_shapes_ok": ["sharp", "moderate"],
        "dendrites": dend_ref,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("train_dir", type=Path, nargs="+")
    ap.add_argument("--stat-dir", type=Path, default=None)
    ap.add_argument("--reference", type=Path, default=None)
    ap.add_argument("--export-reference", type=Path, default=None, help="Write reference JSON from first run")
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    ref_doc: dict[str, Any] | None = None
    if args.reference and args.reference.is_file():
        ref_doc = json.loads(args.reference.read_text(encoding="utf-8"))
        if "dendrites" not in ref_doc and args.train_dir:
            exp = args.train_dir[0].parent.name
            ref_doc = ref_doc.get(exp, ref_doc) if isinstance(ref_doc, dict) else ref_doc

    results: list[dict[str, Any]] = []
    for td in args.train_dir:
        td = Path(td)
        exp_ref = None
        if ref_doc:
            if "dendrites" in ref_doc:
                exp_ref = ref_doc
            else:
                exp_ref = ref_doc.get(td.parent.name)
        r = analyze_run(td, stat_dir=args.stat_dir, reference=exp_ref)
        results.append(r)
        if args.export_reference and td == args.train_dir[0]:
            exp = td.parent.name
            out_ref = build_reference_from_run(r, exp=exp)
            args.export_reference.parent.mkdir(parents=True, exist_ok=True)
            args.export_reference.write_text(json.dumps(out_ref, indent=2), encoding="utf-8")
            print(f"Wrote reference {args.export_reference}", file=sys.stderr)

    if args.json_out:
        args.json_out.write_text(json.dumps(results, indent=2), encoding="utf-8")

    if args.report:
        lines = ["# Signal Fidelity Report", ""]
        for r in results:
            lines.append(f"## {r['exp']}")
            lines.append(f"- IsNeedToTrain: {r.get('IsNeedToTrain')}")
            lines.append(f"- all_non_ref_sync_ok: {r.get('all_non_ref_sync_ok')}")
            fid = r.get("fidelity", {})
            if fid:
                lines.append(f"- signal_fidelity_ok: {fid.get('signal_fidelity_ok')}")
                if fid.get("issues"):
                    lines.append(f"- issues: {', '.join(fid['issues'])}")
            for d in r.get("dendrites", []):
                if d["dendrite"] == REF_DENDRITE:
                    continue
                lines.append(
                    f"  - d{d['dendrite']}: L={d['L']} sync={d['sync_ok']} "
                    f"dt={d['last_abs_dt']:.4f} shape={d['peak_shape']} "
                    f"L_osc={d['L_oscillation_count']}"
                )
            lines.append("")
        args.report.write_text("\n".join(lines), encoding="utf-8")

    if len(results) == 1:
        print(json.dumps(results[0], indent=2))
    else:
        print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

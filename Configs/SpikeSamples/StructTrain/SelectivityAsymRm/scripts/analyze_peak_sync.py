#!/usr/bin/env python3
"""Peak-sync audit: L_formula vs L_sync_peak vs L_actual, shape, sync_ok."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from asymrm_train_common import (
    K_DELAY_PER_SEG_DEFAULT,
    K_NUM_DENDRITES,
    REF_DENDRITE,
    all_non_ref_sync_ok,
    analyze_peak_shape,
    compute_l_target,
    compute_needed_delays,
    delay_len_of,
    estimate_est_delay_from_l,
    length_sync_ok,
    list_statistic_dirs,
    load_train_params,
    load_trace_vectors,
    parse_trace_tail_rows,
    read_gts_from_ini,
    resolve_trace_path,
)


def classify_dend_verdict(
    *,
    sync_ok: bool,
    l_actual: int,
    l_formula: int,
    l_sync_peak: int,
    peak_shape: str,
    need_train: str | None,
) -> str:
    if peak_shape == "invalid" and need_train == "1":
        return "PEAK_SHAPE_SUSPECT"
    if sync_ok and l_actual == l_sync_peak:
        if l_actual != l_formula:
            return "FORMULA_OFF"
        return "SYNC_OK"
    if sync_ok and l_actual != l_formula:
        return "FORMULA_OFF"
    if not sync_ok:
        return "PEAK_MISALIGNED"
    return "PEAK_MISMATCH"


def overall_peak_verdict(dend_verdicts: list[str], l_actual: list[int], l_formula: list[int]) -> str:
    if all(v in ("SYNC_OK", "FORMULA_OFF") for v in dend_verdicts[: REF_DENDRITE]):
        if any(v == "FORMULA_OFF" for v in dend_verdicts):
            return "PEAK_PREFERS_L_ACTUAL"
        return "FORMULA_OK"
    if any(v == "PEAK_SHAPE_SUSPECT" for v in dend_verdicts):
        return "PEAK_SHAPE_SUSPECT"
    if all(a == f for a, f in zip(l_actual, l_formula)):
        return "FORMULA_OK"
    mism = sum(1 for a, f in zip(l_actual, l_formula) if a != f)
    if mism and all(v == "FORMULA_OFF" for v in dend_verdicts[: REF_DENDRITE] if v != "SYNC_OK"):
        return "PEAK_PREFERS_L_ACTUAL"
    return "PEAK_MISMATCH"


def analyze_train_dir(train_dir: Path, *, stat_dir: Path | None = None) -> dict[str, Any]:
    params_path = train_dir / "Parameters_00.xml"
    p = load_train_params(params_path)
    l_actual = p["DendriteLength"]
    expected = p["Expected"]
    sync_tol = p["SyncTolerance"]

    est_cold = K_DELAY_PER_SEG_DEFAULT
    est_post = estimate_est_delay_from_l(expected, l_actual) or est_cold
    l_formula_cold = compute_l_target(expected, est_cold)
    l_formula_post = compute_l_target(expected, est_post)
    l_sync_peak_cold = compute_l_target(expected, est_cold, ref_peak=expected[-1] if expected else None)
    l_sync_peak_post = compute_l_target(expected, est_post, ref_peak=expected[-1] if expected else None)

    stat = stat_dir or (list_statistic_dirs(train_dir)[-1] if list_statistic_dirs(train_dir) else None)
    traces = load_trace_vectors(train_dir, stat_dir=stat) if stat else {}

    last_abs_dt = traces.get("LastAbsDtTrace", [0.0] * K_NUM_DENDRITES)
    soma_path = resolve_trace_path(stat, "SomaNeuronAmplitude") if stat else None
    soma_rows = parse_trace_tail_rows(soma_path, tail_rows=2000) if soma_path else []
    shapes = analyze_peak_shape(soma_rows)

    dend_rows: list[dict[str, Any]] = []
    dend_verdicts: list[str] = []

    ref_peak = expected[-1] if expected else 0.0
    needed = compute_needed_delays(expected, ref_peak)

    for i in range(K_NUM_DENDRITES):
        L = l_actual[i] if i < len(l_actual) else 1
        lt_cold = l_formula_cold[i] if i < len(l_formula_cold) else 1
        lt_post = l_formula_post[i] if i < len(l_formula_post) else 1
        lsp = l_sync_peak_post[i] if i < len(l_sync_peak_post) else 1
        dt = last_abs_dt[i] if i < len(last_abs_dt) else 0.0
        sync_ok = length_sync_ok(dt, sync_tol) if i != REF_DENDRITE else False
        delay_len = delay_len_of(L, est_post)
        nd = needed[i] if i < len(needed) else 0.0

        shape_info = shapes[i] if i < len(shapes) else {"peak_shape": "invalid"}
        if i == REF_DENDRITE:
            dv = "SYNC_OK" if L == 1 else "PEAK_MISMATCH"
        else:
            dv = classify_dend_verdict(
                sync_ok=sync_ok,
                l_actual=L,
                l_formula=lt_cold,
                l_sync_peak=lsp,
                peak_shape=shape_info.get("peak_shape", "invalid"),
                need_train=p["IsNeedToTrain"],
            )
        dend_verdicts.append(dv)
        dend_rows.append(
            {
                "dend": i,
                "L_actual": L,
                "L_formula_cold": lt_cold,
                "L_formula_post": lt_post,
                "L_sync_peak": lsp,
                "last_abs_dt": dt,
                "sync_ok": sync_ok,
                "needed": nd,
                "delay_len": delay_len,
                "peak_shape": shape_info.get("peak_shape"),
                "max_amp": shape_info.get("max_amp"),
                "plateau_ratio": shape_info.get("plateau_ratio"),
                "verdict_dend": dv,
            }
        )

    overall = overall_peak_verdict(dend_verdicts, l_actual, l_formula_cold)
    if p["IsNeedToTrain"] == "0" and all_non_ref_sync_ok(last_abs_dt, sync_tol):
        if overall == "FORMULA_OK" and l_actual != l_formula_cold:
            overall = "PEAK_PREFERS_L_ACTUAL"

    return {
        "exp": train_dir.parent.name,
        "train_dir": str(train_dir),
        "stat_dir": str(stat) if stat else None,
        "GTS": read_gts_from_ini(train_dir),
        "EstDelayPerSeg_cold": est_cold,
        "EstDelayPerSeg_post": est_post,
        "L_actual": l_actual,
        "L_formula_cold": l_formula_cold,
        "L_formula_post": l_formula_post,
        "L_sync_peak": l_sync_peak_post,
        "Expected": expected,
        "SyncTolerance": sync_tol,
        "PeakMeasureMargin": p["PeakMeasureMargin"],
        "DelayAgreeMarginMin": p.get("DelayAgreeMarginMin", 0.03),
        "IsNeedToTrain": p["IsNeedToTrain"],
        "FixedLTZ": p["FixedLTZThreshold"],
        "all_non_ref_sync_ok": all_non_ref_sync_ok(last_abs_dt, sync_tol),
        "verdict": overall,
        "dendrites": dend_rows,
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = ["# PEAK_SYNC_REPORT — SelectivityAsymRm\n"]
    for r in results:
        exp = r.get("exp", "?")
        lines.append(f"## {exp}\n")
        lines.append(f"- **verdict:** `{r.get('verdict')}`")
        lines.append(f"- **IsNeedToTrain:** {r.get('IsNeedToTrain')}")
        lines.append(f"- **all_non_ref_sync_ok:** {r.get('all_non_ref_sync_ok')}")
        lines.append(f"- **GTS:** {r.get('GTS')}")
        la = r.get("L_actual", [])
        lc = r.get("L_formula_cold", [])
        lp = r.get("L_formula_post", [])
        lsp = r.get("L_sync_peak", [])
        lines.append(
            f"- **L:** actual=`{' '.join(map(str, la))}` "
            f"formula_cold=`{' '.join(map(str, lc))}` "
            f"formula_post=`{' '.join(map(str, lp))}` "
            f"sync_peak=`{' '.join(map(str, lsp))}`"
        )
        lines.append(f"- **EstDelay:** cold={r.get('EstDelayPerSeg_cold')} post={r.get('EstDelayPerSeg_post')}")
        lines.append("")
        lines.append("| dend | L | L_formula | L_sync | sync_ok | last_abs_dt | shape | verdict |")
        lines.append("|:----:|:-:|:---------:|:------:|:-------:|:-----------:|:-----:|:-------:|")
        for d in r.get("dendrites", []):
            lines.append(
                f"| {d['dend']} | {d['L_actual']} | {d['L_formula_cold']} | {d['L_sync_peak']} | "
                f"{d['sync_ok']} | {d['last_abs_dt']:.4g} | {d.get('peak_shape','?')} | {d['verdict_dend']} |"
            )
        lines.append("")
    lines.append("## Summary\n")
    lines.append("| EXP | verdict | all_sync_ok | L_actual | L_formula_cold |")
    lines.append("|-----|---------|-------------|----------|------------------|")
    for r in results:
        la = " ".join(str(x) for x in r.get("L_actual", []))
        lc = " ".join(str(x) for x in r.get("L_formula_cold", []))
        lines.append(
            f"| {r.get('exp')} | {r.get('verdict')} | {r.get('all_non_ref_sync_ok')} | {la} | {lc} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("train_dirs", nargs="*", type=Path)
    ap.add_argument("--stat-dir", type=Path, default=None)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--md", type=Path, help="Write markdown report")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.train_dirs:
        ap.error("provide train dirs")

    results = []
    for d in args.train_dirs:
        if not (d / "Parameters_00.xml").exists():
            results.append({"train_dir": str(d), "verdict": "MISSING", "error": "no Parameters"})
            continue
        results.append(analyze_train_dir(d, stat_dir=args.stat_dir))

    if args.output:
        args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    if args.md:
        args.md.write_text(render_markdown(results), encoding="utf-8")

    if not args.json:
        for r in results:
            print(
                f"{r.get('exp','?')}: verdict={r.get('verdict')} "
                f"sync_ok_all={r.get('all_non_ref_sync_ok')} "
                f"L={r.get('L_actual')} formula={r.get('L_formula_cold')}"
            )
    else:
        print(json.dumps(results, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Sync tolerance audit: dt/tol, delay decomposition, tol_min_for_sync, classification."""
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
    compute_l_target,
    compute_needed_delays,
    delay_len_of,
    estimate_est_delay_from_l,
    length_sync_ok,
    load_meta_exps,
    load_train_params,
    load_trace_vectors,
)


def tol_min_l_for_sync(
    needed: float,
    est_delay: float,
    sync_tol: float,
    l_current: int,
    *,
    l_min: int = 1,
    l_max: int = 100,
) -> int | None:
    """Minimum L in [l_min, l_max] s.t. |needed - (L-1)*est| <= tol."""
    if est_delay <= 1e-12:
        return None
    best: int | None = None
    for L in range(l_min, l_max + 1):
        residual = abs(needed - (L - 1) * est_delay)
        if residual <= sync_tol + 1e-12:
            if best is None or L < best:
                best = L
    if best is not None:
        return best
    # Fallback: search around current L
    for delta in range(0, 6):
        for L in (l_current - delta, l_current + delta):
            if L < l_min or L > l_max:
                continue
            residual = abs(needed - (L - 1) * est_delay)
            if residual <= sync_tol + 1e-12:
                return L
    return None


def classify_dend(
    *,
    sync_ok: bool,
    dt_over_tol: float,
    l_actual: int,
    l_target: int,
    l_ref: int | None,
    tol_min_l: int | None,
) -> str:
    if l_ref is not None and l_actual < l_ref and l_actual == l_target:
        return "L_FORMULA_OFF"
    if l_actual < l_target:
        return "LENGTH_UNDER"
    if sync_ok:
        return "SYNC_OK"
    if dt_over_tol <= 1.2:
        return "BORDERLINE"
    if tol_min_l is not None and tol_min_l > l_actual:
        return "L_FORMULA_OFF"
    return "MISALIGNED"


def load_reference_l(ref_path: Path) -> list[int] | None:
    if not ref_path.is_file():
        return None
    p = load_train_params(ref_path)
    return p.get("DendriteLength")


def analyze_train_dir(
    train_dir: Path,
    *,
    reference_l: list[int] | None = None,
    est_delay: float | None = None,
) -> dict[str, Any]:
    params_path = train_dir / "Parameters_00.xml"
    p = load_train_params(params_path)
    l_actual = p["DendriteLength"]
    expected = p["Expected"]
    sync_tol = p["SyncTolerance"]
    est = est_delay or estimate_est_delay_from_l(expected, l_actual) or K_DELAY_PER_SEG_DEFAULT
    l_target = compute_l_target(expected, est)
    needed = compute_needed_delays(expected)
    traces = load_trace_vectors(train_dir)
    last_abs_dt = traces.get("LastAbsDtTrace", [0.0] * K_NUM_DENDRITES)

    dend_rows: list[dict[str, Any]] = []
    classes: list[str] = []

    for i in range(K_NUM_DENDRITES):
        L = l_actual[i] if i < len(l_actual) else 1
        lt = l_target[i] if i < len(l_target) else 1
        nd = needed[i] if i < len(needed) else 0.0
        dt = last_abs_dt[i] if i < len(last_abs_dt) else 0.0
        sync_ok = length_sync_ok(dt, sync_tol) if i != REF_DENDRITE else (L == 1)
        dt_over = dt / sync_tol if sync_tol > 1e-12 else 0.0
        dlen = delay_len_of(L, est)
        residual = nd - dlen
        l_ref = reference_l[i] if reference_l and i < len(reference_l) else None
        tol_min_l = None
        if i != REF_DENDRITE:
            tol_min_l = tol_min_l_for_sync(nd, est, sync_tol, L)
        cls = classify_dend(
            sync_ok=sync_ok,
            dt_over_tol=dt_over,
            l_actual=L,
            l_target=lt,
            l_ref=l_ref,
            tol_min_l=tol_min_l,
        )
        classes.append(cls)
        dend_rows.append(
            {
                "dend": i,
                "L_actual": L,
                "L_target": lt,
                "L_ref": l_ref,
                "delta_L_vs_ref": (L - l_ref) if l_ref is not None else None,
                "needed": nd,
                "delay_len": dlen,
                "delay_residual": residual,
                "last_abs_dt": dt,
                "dt_over_tol": dt_over,
                "sync_ok": sync_ok,
                "tol_min_for_sync": tol_min_l,
                "class": cls,
            }
        )

    non_ref_classes = [c for i, c in enumerate(classes) if i != REF_DENDRITE]
    if all(c == "SYNC_OK" for c in non_ref_classes):
        overall = "SYNC_OK"
    elif "L_FORMULA_OFF" in non_ref_classes:
        overall = "L_FORMULA_OFF"
    elif "LENGTH_UNDER" in non_ref_classes:
        overall = "LENGTH_UNDER"
    elif "MISALIGNED" in non_ref_classes:
        overall = "MISALIGNED"
    elif "BORDERLINE" in non_ref_classes:
        overall = "BORDERLINE"
    else:
        overall = non_ref_classes[0] if non_ref_classes else "UNKNOWN"

    return {
        "exp": train_dir.parent.name,
        "train_dir": str(train_dir),
        "SyncTolerance": sync_tol,
        "EstDelayPerSeg": est,
        "L_actual": l_actual,
        "L_target": l_target,
        "L_reference": reference_l,
        "all_non_ref_sync_ok": all(
            dend_rows[i]["sync_ok"] for i in range(K_NUM_DENDRITES) if i != REF_DENDRITE
        ),
        "overall_class": overall,
        "dendrites": dend_rows,
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = ["# SYNC_TOL_REPORT — SelectivityAsymRm\n"]
    for r in results:
        exp = r.get("exp", "?")
        lines.append(f"## {exp}\n")
        lines.append(f"- **overall_class:** `{r.get('overall_class')}`")
        lines.append(f"- **SyncTolerance:** {r.get('SyncTolerance')} s")
        lines.append(f"- **EstDelayPerSeg:** {r.get('EstDelayPerSeg')}")
        lines.append(f"- **all_non_ref_sync_ok:** {r.get('all_non_ref_sync_ok')}")
        la = r.get("L_actual", [])
        lt = r.get("L_target", [])
        lr = r.get("L_reference")
        lines.append(
            f"- **L:** actual=`{' '.join(map(str, la))}` "
            f"target=`{' '.join(map(str, lt))}`"
            + (f" ref=`{' '.join(map(str, lr))}`" if lr else "")
        )
        lines.append("")
        lines.append(
            "| dend | L | L_tgt | L_ref | needed | delay_len | residual | "
            "last_abs_dt | dt/tol | tol_min_L | class |"
        )
        lines.append(
            "|:----:|:-:|:-----:|:-----:|:------:|:---------:|:--------:|"
            ":-----------:|:------:|:---------:|:-----:|"
        )
        for d in r.get("dendrites", []):
            lref = d.get("L_ref")
            lref_s = str(lref) if lref is not None else "—"
            tol_min = d.get("tol_min_for_sync")
            tol_s = str(tol_min) if tol_min is not None else "—"
            lines.append(
                f"| {d['dend']} | {d['L_actual']} | {d['L_target']} | {lref_s} | "
                f"{d['needed']:.4g} | {d['delay_len']:.4g} | {d['delay_residual']:.4g} | "
                f"{d['last_abs_dt']:.4g} | {d['dt_over_tol']:.2f}× | {tol_s} | `{d['class']}` |"
            )
        lines.append("")

    lines.append("## Summary\n")
    lines.append("| EXP | overall_class | all_sync_ok | blocker dend | dt/tol max |")
    lines.append("|-----|---------------|-------------|--------------|------------|")
    for r in results:
        dends = r.get("dendrites", [])
        max_dt = 0.0
        blocker = "—"
        for d in dends:
            if d["dend"] == REF_DENDRITE:
                continue
            if not d["sync_ok"] and d["dt_over_tol"] >= max_dt:
                max_dt = d["dt_over_tol"]
                blocker = f"d{d['dend']}"
        lines.append(
            f"| {r.get('exp')} | `{r.get('overall_class')}` | "
            f"{r.get('all_non_ref_sync_ok')} | {blocker} | {max_dt:.2f}× |"
        )
    lines.append("")
    return "\n".join(lines)


REFERENCE_MAP = {
    "EXP_span25ms_packA_gen": "SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Train/Parameters_00.xml",
    "EXP_span25ms_packA_preinh": "SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Train/Parameters_00.xml",
}


def resolve_reference(train_dir: Path, reference_root: Path | None) -> list[int] | None:
    exp = train_dir.parent.name
    if reference_root:
        rel = REFERENCE_MAP.get(exp)
        if rel:
            ref_path = reference_root / rel
            if not ref_path.is_file():
                # try relative to StructTrain
                alt = reference_root.parent / rel.split("/", 1)[-1] if "/" in rel else ref_path
                for cand in (ref_path, alt):
                    if cand.is_file():
                        return load_reference_l(cand)
            else:
                return load_reference_l(ref_path)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("train_dirs", nargs="*", type=Path)
    ap.add_argument("--meta", type=Path)
    ap.add_argument("--grid", type=Path)
    ap.add_argument(
        "--reference",
        type=Path,
        default=None,
        help="Root for LtzCal reference (StructTrain or repo); loads L from Done EXP",
    )
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--md", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    dirs: list[Path] = list(args.train_dirs)
    if args.meta and args.grid:
        for row in load_meta_exps(args.meta, args.grid):
            dirs.append(Path(row["train_dir"]))

    if not dirs:
        ap.error("provide train dirs or --meta + --grid")

    ref_root = args.reference
    if ref_root is None:
        # default: StructTrain parent of SelectivityAsymRm
        ref_root = Path(__file__).resolve().parents[2]

    results = []
    for d in dirs:
        if not (d / "Parameters_00.xml").exists():
            results.append({"train_dir": str(d), "overall_class": "MISSING"})
            continue
        ref_l = resolve_reference(d, ref_root)
        results.append(analyze_train_dir(d, reference_l=ref_l))

    if args.output:
        args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    if args.md:
        args.md.write_text(render_markdown(results), encoding="utf-8")

    if not args.json:
        for r in results:
            print(
                f"{r.get('exp','?')}: class={r.get('overall_class')} "
                f"sync_all={r.get('all_non_ref_sync_ok')}"
            )
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

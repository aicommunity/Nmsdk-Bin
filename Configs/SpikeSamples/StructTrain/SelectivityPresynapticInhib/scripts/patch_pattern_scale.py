#!/usr/bin/env python3
"""Scale ISI MatrixData/InputPattern/TrainingPattern and set timing margins.

Usage:
  patch_pattern_scale.py <xml...> --span-ms 100
  patch_pattern_scale.py <xml...> --sync-tol 0.004 --peak-margin 0.0058 --agree-min 0.0058
  patch_pattern_scale.py <xml...> --span-ms 100 --no-scale   # margins only
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

REF_SPAN = 0.48
FLOOR = 0.0015
TAG_DOUBLE = r'Type="d" PType="257" IoType="17"'


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def compute_initial(span_s: float) -> dict[str, float]:
    alpha = span_s / REF_SPAN
    sync0 = max(FLOOR, 0.02 * alpha)
    delta_min = max(FLOOR, 0.08 * alpha)
    peak0 = clamp(0.35 * delta_min, 0.002, 0.06)
    agree0 = max(sync0, min(0.03, peak0))
    return {
        "alpha": alpha,
        "sync_tol": sync0,
        "delta_min": delta_min,
        "peak_margin": peak0,
        "agree_min": agree0,
        "floor": FLOOR,
    }


def scale_matrix_block(body: str, alpha: float, floor: float) -> tuple[str, bool]:
    """Scale whitespace-separated floats in a matrix tag body. Returns (new, used_floor)."""
    used_floor = False
    parts: list[str] = []
    for tok in re.split(r"(\s+)", body):
        if not tok or tok.isspace():
            parts.append(tok)
            continue
        try:
            v = float(tok)
        except ValueError:
            parts.append(tok)
            continue
        nv = max(floor, v * alpha)
        if nv == floor and v * alpha < floor:
            used_floor = True
        # Keep compact float formatting
        parts.append(f"{nv:.6g}")
    return "".join(parts), used_floor


def scale_named_matrices(text: str, alpha: float, floor: float) -> tuple[str, bool]:
    used_any = False
    names = ("InputPattern", "TrainingPattern", "MatrixData")

    def repl(m: re.Match[str]) -> str:
        nonlocal used_any
        open_tag, body, close = m.group(1), m.group(2), m.group(3)
        new_body, used = scale_matrix_block(body, alpha, floor)
        used_any = used_any or used
        return f"{open_tag}{new_body}{close}"

    for name in names:
        # Match each occurrence (train has 1 MatrixData; test has 1 large)
        pat = re.compile(
            rf"(<{name}\b[^>]*>)(.*?)(</{name}>)",
            re.DOTALL,
        )
        text, n = pat.subn(repl, text)
        if n == 0 and name != "MatrixData":
            # AdditionalInputPattern stays zeros — ok if InputPattern missing
            pass
    return text, used_any


def set_or_insert_double(text: str, tag: str, value: float) -> str:
    val_s = f"{value:.6g}"
    pat = re.compile(
        rf'(<{tag} {TAG_DOUBLE}>)[^<]*(</{tag}>)'
    )
    new, n = pat.subn(rf"\g<1>{val_s}\g<2>", text)
    if n >= 1:
        return new
    # Insert after a related sibling so Peak→Agree order stays stable.
    insert = f'<{tag} {TAG_DOUBLE}>{val_s}</{tag}>'
    anchors = {
        "PeakMeasureMargin": ("SyncTolerance", "IterationGap", "NeuronClassName"),
        "DelayAgreeMarginMin": (
            "PeakMeasureMargin",
            "SyncTolerance",
            "IterationGap",
            "NeuronClassName",
        ),
        "SyncTolerance": ("IterationGap", "NeuronClassName"),
    }.get(tag, ("SyncTolerance", "IterationGap", "NeuronClassName"))
    for anchor in anchors:
        ap = re.compile(
            rf'(<{anchor} {TAG_DOUBLE}>[^<]*</{anchor}>)'
        )
        m = ap.search(text)
        if m:
            line_start = text.rfind("\n", 0, m.start()) + 1
            indent = text[line_start : m.start()]
            return text[: m.end()] + "\n" + indent + insert + text[m.end() :]
    raise SystemExit(f"cannot insert <{tag}>: no suitable anchor")


def patch_file(
    path: Path,
    *,
    alpha: float | None,
    sync_tol: float | None,
    peak_margin: float | None,
    agree_min: float | None,
    do_scale: bool,
) -> dict:
    text = path.read_text(encoding="utf-8")
    info: dict = {"path": str(path), "floor": False}
    if do_scale:
        if alpha is None:
            raise SystemExit("--span-ms required for scaling")
        text, used = scale_named_matrices(text, alpha, FLOOR)
        info["floor"] = used
        info["alpha"] = alpha
    if sync_tol is not None:
        text = set_or_insert_double(text, "SyncTolerance", sync_tol)
        info["SyncTolerance"] = sync_tol
    if peak_margin is not None:
        text = set_or_insert_double(text, "PeakMeasureMargin", peak_margin)
        info["PeakMeasureMargin"] = peak_margin
    if agree_min is not None:
        text = set_or_insert_double(text, "DelayAgreeMarginMin", agree_min)
        info["DelayAgreeMarginMin"] = agree_min
    path.write_text(text, encoding="utf-8")
    return info


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xmls", nargs="+", type=Path)
    ap.add_argument("--span-ms", type=float, default=None)
    ap.add_argument("--sync-tol", type=float, default=None)
    ap.add_argument("--peak-margin", type=float, default=None)
    ap.add_argument("--agree-min", type=float, default=None)
    ap.add_argument("--no-scale", action="store_true")
    args = ap.parse_args()

    alpha = None
    sync = args.sync_tol
    peak = args.peak_margin
    agree = args.agree_min
    if args.span_ms is not None:
        init = compute_initial(args.span_ms / 1000.0)
        alpha = init["alpha"]
        if sync is None:
            sync = init["sync_tol"]
        if peak is None:
            peak = init["peak_margin"]
        if agree is None:
            agree = init["agree_min"]
        print(
            f"span={args.span_ms}ms alpha={alpha:.6g} "
            f"SyncTol={sync:.6g} PeakMargin={peak:.6g} AgreeMin={agree:.6g} "
            f"dmin={init['delta_min']:.6g}",
            file=sys.stderr,
        )

    do_scale = not args.no_scale and alpha is not None
    for p in args.xmls:
        info = patch_file(
            p,
            alpha=alpha,
            sync_tol=sync,
            peak_margin=peak,
            agree_min=agree,
            do_scale=do_scale,
        )
        floor_s = "floor=yes" if info.get("floor") else "floor=no"
        print(f"patched {p} {floor_s}")


if __name__ == "__main__":
    main()

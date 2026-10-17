#!/usr/bin/env python3
"""Scale ISI patterns from canonical refs (idempotent) and set timing margins.

Usage:
  patch_pattern_scale.py <xml...> --span-ms 100
  patch_pattern_scale.py <xml...> --span-ms 100 --dry-run
  patch_pattern_scale.py <xml...> --sync-tol 0.004 --peak-margin 0.0058 --agree-min 0.0058
  patch_pattern_scale.py <xml...> --span-ms 100 --no-scale   # margins only
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REF_SPAN_SEC = 0.48  # sum(InputPattern rows 1..3) of canonical train pattern
REF_TRAIN = [0.01, 0.08, 0.16, 0.24]
REF_TEST_MATRIX = [
    0.01, 0.08, 0.16, 0.24,
    0.01, 0.24, 0.16, 0.08,
    0.01, 0.16, 0.08, 0.24,
    0.01, 0.16, 0.16, 0.16,
    0.01, 0.02, 0.22, 0.24,
    0.01, 0.24, 0.22, 0.02,
    0.01, 0.04, 0.04, 0.40,
    0.01, 0.40, 0.04, 0.04,
]
FLOOR_SEC = 0.0005
TAG_DOUBLE = r'Type="d" PType="257" IoType="17"'


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def scale_ref_values(ref: list[float], alpha: float, floor: float = FLOOR_SEC) -> list[float]:
    return [max(floor, v * alpha) for v in ref]


def learner_span_sec(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return sum(values[1:])


def compute_initial(span_s: float) -> dict[str, float]:
    alpha = span_s / REF_SPAN_SEC
    sync0 = max(FLOOR_SEC, 0.02 * alpha)
    delta_min = max(FLOOR_SEC, 0.08 * alpha)
    peak0 = clamp(0.35 * delta_min, 0.002, 0.06)
    agree0 = max(sync0, min(0.03, peak0))
    return {
        "alpha": alpha,
        "sync_tol": sync0,
        "delta_min": delta_min,
        "peak_margin": peak0,
        "agree_min": agree0,
    }


def fmt_matrix_body(values: list[float]) -> str:
    return "\n".join(f"{v:.6g}" for v in values)


def parse_matrix_rows(open_tag: str) -> int | None:
    m = re.search(r'Rows="(\d+)"', open_tag)
    return int(m.group(1)) if m else None


def replace_matrix_tag(
    text: str,
    name: str,
    ref_values: list[float],
    *,
    only_if_rows: int | None = None,
) -> tuple[str, bool]:
    pat = re.compile(rf"(<{name}\b[^>]*>)(.*?)(</{name}>)", re.DOTALL)

    def repl(m: re.Match[str]) -> str:
        open_tag, _, close = m.group(1), m.group(2), m.group(3)
        rows = parse_matrix_rows(open_tag)
        if only_if_rows is not None and rows != only_if_rows:
            return m.group(0)
        if rows is not None and rows != len(ref_values):
            raise ValueError(
                f"{name}: Rows={rows} but ref has {len(ref_values)} values"
            )
        body = fmt_matrix_body(ref_values)
        return f"{open_tag}{body}{close}"

    new_text, n = pat.subn(repl, text, count=1)
    return new_text, n > 0


def apply_pattern_scale(text: str, alpha: float) -> tuple[str, dict]:
    train_scaled = scale_ref_values(REF_TRAIN, alpha)
    test_scaled = scale_ref_values(REF_TEST_MATRIX, alpha)
    info = {
        "train_span_ms": learner_span_sec(train_scaled) * 1000,
        "train_pattern": train_scaled,
        "floor_used": any(
            v == FLOOR_SEC and r * alpha < FLOOR_SEC
            for v, r in zip(train_scaled, REF_TRAIN, strict=True)
        ),
    }

    text, ok = replace_matrix_tag(text, "InputPattern", train_scaled)
    if not ok:
        raise SystemExit("InputPattern tag not found")

    # MatrixData: Train 4×1, Test 32×1 — pick ref by Rows attribute
    def repl_matrix(m: re.Match[str]) -> str:
        open_tag, _, close = m.group(1), m.group(2), m.group(3)
        rows = parse_matrix_rows(open_tag)
        if rows == 4:
            vals = train_scaled
        elif rows == 32:
            vals = test_scaled
        else:
            raise ValueError(f"MatrixData: unexpected Rows={rows}")
        return f"{open_tag}{fmt_matrix_body(vals)}{close}"

    pat = re.compile(r"(<MatrixData\b[^>]*>)(.*?)(</MatrixData>)", re.DOTALL)
    text, n = pat.subn(repl_matrix, text, count=1)
    if n == 0:
        raise SystemExit("MatrixData tag not found")

    # TrainingPattern — only if non-empty
    tp_pat = re.compile(r"(<TrainingPattern\b[^>]*>)(.*?)(</TrainingPattern>)", re.DOTALL)
    tp_m = tp_pat.search(text)
    if tp_m:
        rows = parse_matrix_rows(tp_m.group(1))
        if rows and rows > 0:
            text = tp_pat.sub(
                lambda m: f"{m.group(1)}{fmt_matrix_body(train_scaled)}{m.group(3)}",
                text,
                count=1,
            )

    return text, info


def set_or_insert_double(text: str, tag: str, value: float) -> str:
    val_s = f"{value:.6g}"
    pat = re.compile(rf"(<{tag} {TAG_DOUBLE}>)[^<]*(</{tag}>)")
    new, n = pat.subn(rf"\g<1>{val_s}\g<2>", text)
    if n >= 1:
        return new
    insert = f"<{tag} {TAG_DOUBLE}>{val_s}</{tag}>"
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
        ap = re.compile(rf"(<{anchor} {TAG_DOUBLE}>[^<]*</{anchor}>)")
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
    dry_run: bool,
) -> dict:
    text = path.read_text(encoding="utf-8")
    info: dict = {"path": str(path)}
    if do_scale:
        if alpha is None:
            raise SystemExit("--span-ms required for scaling")
        text, scale_info = apply_pattern_scale(text, alpha)
        info.update(scale_info)
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
    if not dry_run and (do_scale or sync_tol or peak_margin or agree_min):
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
    ap.add_argument("--dry-run", action="store_true")
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
            f"expected_train_span={args.span_ms}ms",
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
            dry_run=args.dry_run,
        )
        floor_s = "floor=yes" if info.get("floor_used") else "floor=no"
        span_s = ""
        if "train_span_ms" in info:
            span_s = f" span={info['train_span_ms']:.3f}ms"
        action = "dry-run" if args.dry_run else "patched"
        print(f"{action} {p} {floor_s}{span_s}")


if __name__ == "__main__":
    main()

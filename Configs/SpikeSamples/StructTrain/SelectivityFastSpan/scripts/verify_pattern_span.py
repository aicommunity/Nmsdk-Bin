#!/usr/bin/env python3
"""Verify InputPattern/MatrixData learner spans match grid_cells.tsv targets."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TOL_MS = 0.5
SPIKES_PER_SAMPLE = 4


def parse_matrix(tag: str, text: str) -> list[float]:
    m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", text, re.DOTALL)
    if not m:
        raise ValueError(f"{tag} not found")
    return [float(x) for x in m.group(1).split()]


def learner_span_ms(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return sum(values[1:]) * 1000.0


def sample_spans_ms(matrix: list[float], spikes: int = SPIKES_PER_SAMPLE) -> list[float]:
    if len(matrix) % spikes != 0:
        raise ValueError(f"MatrixData length {len(matrix)} not divisible by {spikes}")
    spans = []
    for s in range(len(matrix) // spikes):
        block = matrix[s * spikes : (s + 1) * spikes]
        spans.append(learner_span_ms(block))
    return spans


def load_meta(meta_path: Path) -> dict[str, float]:
    meta: dict[str, float] = {}
    lines = meta_path.read_text(encoding="utf-8").splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            meta[parts[0]] = float(parts[2])
    return meta


def exp_from_path(path: Path) -> str | None:
    for part in path.parts:
        if part.startswith("EXP_"):
            return part
    return None


def check_file(path: Path, target_ms: float) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    is_test = "/Test/" in str(path) or path.parts[-2] == "Test"

    if is_test:
        matrix = parse_matrix("MatrixData", text)
        spans = sample_spans_ms(matrix)
        bad = [(i, s) for i, s in enumerate(spans) if abs(s - target_ms) > TOL_MS]
        if bad:
            detail = ", ".join(f"sample{i}={s:.2f}ms" for i, s in bad[:4])
            return False, f"MatrixData spans FAIL ({detail})"
        ip = parse_matrix("InputPattern", text)
        ip_span = learner_span_ms(ip)
        if abs(ip_span - target_ms) > TOL_MS:
            return False, f"InputPattern span={ip_span:.2f}ms (target {target_ms})"
        return True, f"MatrixData 8×span OK ({spans[0]:.2f}ms), InputPattern={ip_span:.2f}ms"
    else:
        ip = parse_matrix("InputPattern", text)
        span = learner_span_ms(ip)
        if abs(span - target_ms) > TOL_MS:
            return False, f"InputPattern span={span:.2f}ms (target {target_ms})"
        md = parse_matrix("MatrixData", text)
        md_span = learner_span_ms(md)
        if abs(md_span - target_ms) > TOL_MS:
            return False, f"MatrixData span={md_span:.2f}ms (target {target_ms})"
        return True, f"InputPattern={span:.2f}ms MatrixData={md_span:.2f}ms"


def main() -> int:
    global TOL_MS
    ap = argparse.ArgumentParser()
    ap.add_argument("xmls", nargs="+", type=Path)
    ap.add_argument("--meta", type=Path, required=True)
    ap.add_argument("--tol-ms", type=float, default=TOL_MS)
    args = ap.parse_args()
    TOL_MS = args.tol_ms

    meta = load_meta(args.meta)
    fails = 0
    for p in args.xmls:
        exp = exp_from_path(p)
        if not exp or exp not in meta:
            print(f"SKIP {p} (no meta for {exp!r})")
            continue
        target = meta[exp]
        try:
            ok, msg = check_file(p, target)
        except Exception as e:
            ok, msg = False, str(e)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {p.relative_to(p.parents[3]) if len(p.parents) > 3 else p}: {msg} (target {target}ms)")
        if not ok:
            fails += 1

    if fails:
        print(f"\n{ fails} failure(s)", file=sys.stderr)
        return 1
    print(f"\nAll {len(args.xmls)} file(s) PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

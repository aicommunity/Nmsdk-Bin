#!/usr/bin/env python3
"""LTZ/soma separability analysis for SelectivityLtzCalibrate results.csv."""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ltz_roc(rows: list[dict]) -> dict:
    if not rows:
        return {"best_acc": 0, "best_thr": None, "target_ltz": [], "dist_ltz": []}
    targets = [float(r["ltz_potential_max"]) for r in rows if r.get("target_class") == "1"]
    dists = [float(r["ltz_potential_max"]) for r in rows if r.get("target_class") == "0"]
    all_ltz = sorted(set(targets + dists))
    best_acc, best_thr = 0, None
    for thr in all_ltz:
        tp = sum(1 for v in targets if v >= thr)
        tn = sum(1 for v in dists if v < thr)
        acc = tp + tn
        if acc > best_acc:
            best_acc, best_thr = acc, thr
    return {
        "best_acc": best_acc,
        "best_thr": best_thr,
        "n": len(rows),
        "target_ltz": targets,
        "dist_ltz": dists,
    }


def soma_template_acc(rows: list[dict]) -> dict:
    if not rows:
        return {"acc": 0}
    t0 = rows[0]
    ref = [float(t0.get(f"soma_amp_{i}", 0) or 0) for i in range(4)]
    ref_sum = sum(ref)
    if ref_sum <= 0:
        return {"acc": 0, "note": "zero ref"}
    correct = 0
    for r in rows:
        vec = [float(r.get(f"soma_amp_{i}", 0) or 0) for i in range(4)]
        s = sum(vec)
        dist_ref = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec, ref)))
        # compare to permuted self-distance baseline (same sum)
        is_target = r.get("target_class") == "1"
        pred_target = dist_ref < 0.05 * max(s, ref_sum)  # crude: closest to trial0 profile
        if (is_target and pred_target) or (not is_target and not pred_target):
            correct += 1
    return {"acc": correct, "n": len(rows)}


def isi_exact_acc(rows: list[dict]) -> dict:
    if not rows:
        return {"acc": 0}
    ref_isi = []
    for i in range(4):
        k = f"isi{i}"
        if k in rows[0] and rows[0][k]:
            ref_isi.append(float(rows[0][k]))
    if not ref_isi:
        return {"acc": 0, "note": "no isi"}
    correct = 0
    for r in rows:
        isi = []
        for i in range(4):
            k = f"isi{i}"
            if k in r and r[k]:
                isi.append(float(r[k]))
        match = len(isi) == len(ref_isi) and all(abs(a - b) < 1e-6 for a, b in zip(isi, ref_isi))
        is_target = r.get("target_class") == "1"
        if (is_target and match) or (not is_target and not match):
            correct += 1
    return {"acc": correct, "n": len(rows)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path, nargs="+")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    lines: list[str] = ["exp,ltz_best_acc,ltz_best_thr,isi_template_acc,soma_template_acc"]
    for p in args.csv:
        rows = load_rows(p)
        exp = p.parent.parent.name
        roc = ltz_roc(rows)
        isi = isi_exact_acc(rows)
        soma = soma_template_acc(rows)
        line = f"{exp},{roc['best_acc']}/{roc.get('n',0)},{roc['best_thr']},{isi['acc']}/{isi.get('n',0)},{soma['acc']}/{soma.get('n',0)}"
        lines.append(line)
        print(f"{exp}: LTZ ROC {roc['best_acc']}/{roc.get('n',0)} thr={roc['best_thr']}")
        print(f"  ISI exact template: {isi['acc']}/{isi.get('n',0)}")
        print(f"  soma profile: {soma['acc']}/{soma.get('n',0)}")
        if roc.get("target_ltz") and roc.get("dist_ltz"):
            print(f"  target LTZ {min(roc['target_ltz']):.4f}..{max(roc['target_ltz']):.4f}  dist {min(roc['dist_ltz']):.4f}..{max(roc['dist_ltz']):.4f}")
    text = "\n".join(lines) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}")
    sys.exit(0)


if __name__ == "__main__":
    main()

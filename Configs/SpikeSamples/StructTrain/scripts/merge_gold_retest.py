#!/usr/bin/env python3
"""Merge partial GoldTest log + resume CSV(s) into one GOLD_RETEST CSV for apply_gold_retest."""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys_path_note = ROOT / "scripts"


def load_manifest(path: Path) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        kind, name, test_rel = line.split("\t")[:3]
        out[name] = (kind, test_rel)
    return out


def classify_csv(test_rel: str) -> dict:
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from selectivity_metrics import classify

    csv_path = ROOT / test_rel / "SelectivityLog" / "results.csv"
    if not csv_path.exists():
        return {}
    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return classify(rows)


def verdict(metrics: dict, err: str = "") -> str:
    acc = int(metrics.get("acc", 0) or 0)
    n = int(metrics.get("n", 0) or 0)
    target = int(metrics.get("target_hit", 0) or 0)
    mode = str(metrics.get("mode", "") or "")
    fires = str(metrics.get("fires", "") or "")
    if n < 8 or err == "timeout":
        return "FAIL"
    if mode == "selective" and acc == 8 and fires == "10000000":
        return "PASS"
    if mode == "selective" and acc >= 7 and fires.startswith("1"):
        return "PASS"
    if n == 8 and target == 1 and acc >= 4 and mode in ("selective", "partial_FA"):
        return "PASS"
    return "FAIL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=ROOT / "_repro" / "NOT_RETESTED_manifest_20260925.txt")
    ap.add_argument("--log", type=Path, default=ROOT / "_repro" / "GOLD_RETEST_20260925_run.log")
    ap.add_argument("--csvs", nargs="*", type=Path, default=[])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--console-sha16", default="")
    args = ap.parse_args()

    man = load_manifest(args.manifest)
    by_name: dict[str, dict] = {}

    # From resume CSVs (preferred)
    for p in args.csvs:
        if not p.exists():
            continue
        with p.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                by_name[row["name"]] = row

    # Re-score from disk CSV for names that have fresh SelectivityLog after PASS in log
    for line in args.log.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\[\d+/\d+\] (\S+) (PASS|FAIL) Acc=(\S+) fires=(\S+)", line)
        if not m:
            continue
        name, head, acc, fires = m.group(1), m.group(2), m.group(3), m.group(4)
        if name in by_name:
            continue
        if name not in man:
            continue
        kind, test_rel = man[name]
        metrics = classify_csv(test_rel)
        if metrics:
            head = verdict(metrics)
            acc_s = f"{int(metrics.get('acc',0))}/{int(metrics.get('n',0))}"
            target = "да" if int(metrics.get("target_hit", 0) or 0) else "нет"
            mode = str(metrics.get("mode", "") or "—")
            fires = str(metrics.get("fires", "") or "—")
            ok_audit = str(int(metrics.get("ok_audit", 0) or 0))
        else:
            acc_s, target, mode, ok_audit = acc, "—", "—", "0"
        by_name[name] = {
            "kind": kind,
            "name": name,
            "test_rel": test_rel,
            "acc": acc_s,
            "target": target,
            "mode": mode,
            "fires": fires,
            "ok_audit": ok_audit,
            "head": head,
            "rc": "",
            "err": "from_log",
            "sim_t": "",
            "elapsed_s": "",
            "console_sha16": args.console_sha16,
            "utc": "",
        }

    # Fill any remaining NOT_RETESTED from disk
    for name, (kind, test_rel) in man.items():
        if name in by_name or kind == "OUT":
            continue
        metrics = classify_csv(test_rel)
        if not metrics or int(metrics.get("n", 0) or 0) < 1:
            continue
        head = verdict(metrics)
        by_name[name] = {
            "kind": kind,
            "name": name,
            "test_rel": test_rel,
            "acc": f"{int(metrics.get('acc',0))}/{int(metrics.get('n',0))}",
            "target": "да" if int(metrics.get("target_hit", 0) or 0) else "нет",
            "mode": str(metrics.get("mode", "") or "—"),
            "fires": str(metrics.get("fires", "") or "—"),
            "ok_audit": str(int(metrics.get("ok_audit", 0) or 0)),
            "head": head,
            "rc": "",
            "err": "disk_csv",
            "sim_t": "",
            "elapsed_s": "",
            "console_sha16": args.console_sha16,
            "utc": "",
        }

    fields = [
        "kind", "name", "test_rel", "acc", "target", "mode", "fires", "ok_audit",
        "head", "rc", "err", "sim_t", "elapsed_s", "console_sha16", "utc",
    ]
    rows = sorted(by_name.values(), key=lambda r: (r.get("kind", ""), r.get("test_rel", "")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print(
        f"merged {len(rows)} PASS={sum(1 for r in rows if r['head']=='PASS')} "
        f"FAIL={sum(1 for r in rows if r['head']=='FAIL')} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

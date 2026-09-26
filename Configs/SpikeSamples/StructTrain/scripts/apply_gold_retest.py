#!/usr/bin/env python3
"""Apply GOLD_RETEST_*.csv into EXPERIMENTS.md / SUCCESSFUL_EXPERIMENTS.md."""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "EXPERIMENTS.md"
OK = ROOT / "SUCCESSFUL_EXPERIMENTS.md"


def load_results(path: Path) -> dict[str, dict]:
    by_name: dict[str, dict] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            by_name[row["name"]] = row
    return by_name


def patch_row(line: str, r: dict, console_sha16: str) -> str:
    if "NOT_RETESTED" not in line:
        return line
    cols = [c.strip() for c in line.strip().strip("|").split("|")]
    # main tables: 11 cols; ok_audit short: 6 cols (Имя Acc Цель Режим HEAD Конфиги)
    if len(cols) >= 11:
        # Имя|Algo|Params|Protocol|Acc|Цель|Режим|HEAD|PHASE12|Note|Configs
        cols[4] = r["acc"]
        cols[5] = r["target"]
        cols[6] = r["mode"] if r["mode"] != "—" else cols[6]
        cols[7] = f"**{r['head']}**"
        note = cols[9]
        evidence = (
            f"GoldTest {r.get('utc','')} Console={console_sha16} "
            f"fires={r.get('fires','')}"
        )
        if "GoldTest " in note:
            note = re.sub(r"GoldTest [^|]*", evidence, note, count=1)
        else:
            note = f"{evidence}; was: {note}" if note else evidence
        cols[9] = note
        return "| " + " | ".join(cols) + " |"
    if len(cols) >= 6 and cols[0] == r["name"]:
        # ok_audit table
        cols[1] = r["acc"]
        cols[2] = r["target"]
        cols[3] = r["mode"] if r["mode"] != "—" else cols[3]
        cols[4] = f"**{r['head']}**"
        return "| " + " | ".join(cols) + " |"
    return line


def update_experiments(results: dict[str, dict], console_sha16: str, sha_full: str) -> int:
    text = EXP.read_text(encoding="utf-8")
    # header SHA
    text = re.sub(
        r"Console SHA-256 `[0-9a-f]+`",
        f"Console SHA-256 `{sha_full}`",
        text,
        count=1,
    )
    lines = text.splitlines()
    n = 0
    out: list[str] = []
    for line in lines:
        if not line.startswith("|"):
            out.append(line)
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        name = cols[0] if cols else ""
        if name in results and "NOT_RETESTED" in line:
            out.append(patch_row(line, results[name], console_sha16))
            n += 1
        else:
            out.append(line)
    EXP.write_text("\n".join(out) + "\n", encoding="utf-8")
    return n


def sync_successful(results: dict[str, dict], console_sha16: str) -> int:
    """Append PASS GoldTest rows missing from SUCCESSFUL (best-effort by name)."""
    text = OK.read_text(encoding="utf-8")
    added = 0
    # keep simple: do not duplicate; user table is curated by algorithm section
    # Only bump header SHA if present
    if "Console" in text or "SHA" in text:
        text2 = re.sub(
            r"Console SHA-256 `[0-9a-f]+`",
            f"Console SHA-256 `{results[next(iter(results))]['console_sha16'].ljust(64, '0')[:64]}`",
            text,
            count=1,
        )
        # better: leave SUCCESSFUL structure; append a short GoldTest PASS index section
        pass
    passes = [r for r in results.values() if r["head"] == "PASS"]
    block_lines = [
        "",
        "## GoldTest retest PASS (2026-09-25)",
        "",
        f"Console=`{console_sha16}`; источник: `_repro/GOLD_RETEST_*.csv`.",
        "",
        "| Имя | Acc | Цель | Режим | fires | Конфиги |",
        "|-----|-----|------|-------|-------|---------|",
    ]
    for r in sorted(passes, key=lambda x: x["name"]):
        block_lines.append(
            f"| {r['name']} | {r['acc']} | {r['target']} | {r['mode']} | {r['fires']} | "
            f"[{r['test_rel']}]({r['test_rel']}) |"
        )
        added += 1
    # replace prior auto section if present
    if "## GoldTest retest PASS" in text:
        text = re.sub(
            r"\n## GoldTest retest PASS \(2026-09-25\).*",
            "",
            text,
            count=1,
            flags=re.S,
        )
    OK.write_text(text.rstrip() + "\n" + "\n".join(block_lines) + "\n", encoding="utf-8")
    return added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--console-sha", default="")
    args = ap.parse_args()
    results = load_results(args.csv)
    if not results:
        print("empty csv")
        return 1
    sha16 = args.console_sha or next(iter(results.values())).get("console_sha16", "")
    # full sha from provenance if present
    prov = ROOT / "_repro" / "GOLD_RETEST_PROVENANCE_20260925.json"
    sha_full = sha16
    if prov.exists():
        import json

        sha_full = json.loads(prov.read_text()).get("console_sha256", sha16)
    n = update_experiments(results, sha16, sha_full)
    a = sync_successful(results, sha16)
    print(f"patched EXPERIMENTS rows={n}; SUCCESSFUL PASS block={a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

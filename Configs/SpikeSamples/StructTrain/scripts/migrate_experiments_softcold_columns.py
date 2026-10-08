#!/usr/bin/env python3
"""Migrate EXPERIMENTS/SUCCESSFUL tables: Working+Acc vs SoftCold+SoftColdDetail.

Replaces LastCheck/Режим with SoftCold / SoftColdDetail filled from RCS + SNAP
+ provenance for SoftCold-queue names (all rows sharing that Имя).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_softcold_rcs_to_registry import CASE_TO_NAME, RANK, parse_rcs  # noqa: E402

SNAP = Path(
    "/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/"
    "SOFTCOLD_FULL49_SNAP.md"
)
RUNS = ROOT / "_repro" / "runs"
RCS = ROOT / "_repro" / "SOFTCOLD_HEAD_rcs.txt"

OLD_HEADER = (
    "| Имя | Алгоритм | Параметры | Working | LastCheck | Acc | Цель | Режим | "
    "HEAD | PHASE12 | Примечание | Конфиги |"
)
NEW_HEADER = (
    "| Имя | Алгоритм | Параметры | Working | Acc | Цель | SoftCold | SoftColdDetail | "
    "HEAD | PHASE12 | Примечание | Конфиги |"
)
OLD_SEP = (
    "|-----|----------|-----------|---------|-----------|-----|------|-------|"
    "------|----------|------------|---------|"
)
NEW_SEP = (
    "|-----|----------|-----------|---------|-----|------|----------|----------------|"
    "------|----------|------------|---------|"
)


def name_to_cases() -> dict[str, list[str]]:
    m: dict[str, list[str]] = {}
    for case, name in CASE_TO_NAME.items():
        m.setdefault(name, []).append(case)
    return m


def latest_prov(case: str) -> dict:
    cands = sorted(RUNS.glob(f"{case}_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in cands:
        pj = p / "provenance.json"
        if pj.exists():
            try:
                return json.loads(pj.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
    return {}


def parse_snap_buckets() -> dict[str, str]:
    out: dict[str, str] = {}
    if not SNAP.exists():
        return out
    for line in SNAP.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| `([^`]+)` \| (\d+) \|.*\| \*\*([^*]+)\*\* \|", line)
        if m:
            out[m.group(1)] = m.group(3)
    return out


def build_softcold_index() -> dict[str, dict]:
    """name -> preferred SoftCold case info (PASS preferred if several cases share name)."""
    rcs = {c: rc for c, rc in parse_rcs(RCS)}
    buckets = parse_snap_buckets()
    by_name = name_to_cases()
    idx: dict[str, dict] = {}
    for name, cases in by_name.items():
        in_rcs = [c for c in cases if c in rcs]
        if not in_rcs:
            continue
        # Prefer primary SoftCold (not SoftColdOff *_off); among those prefer FAIL for visibility
        primary = [c for c in in_rcs if not c.endswith("_off")]
        pool = primary or in_rcs
        fails = [c for c in pool if rcs[c] != 0]
        case = (fails[0] if fails else pool[0])
        rc = rcs[case]
        prov = latest_prov(case)
        tipr = prov.get("tipr_class", "?")
        fc = prov.get("failure_class", "?")
        train = prov.get("train_status", "?")
        gate_rc = prov.get("gate_rc", "?")
        notes = prov.get("fail_notes") or []
        if isinstance(notes, list):
            notes_s = ",".join(str(x) for x in notes[:4])
        else:
            notes_s = str(notes)
        bucket = buckets.get(case, "?")
        if rc == 0:
            verdict = "PASS"
            detail = f"case={case}; tipr={tipr}; fc={fc}; train={train}; bucket={bucket}"
        else:
            verdict = "FAIL"
            detail = (
                f"case={case}; tipr={tipr}; fc={fc}; gate_rc={gate_rc}; "
                f"train={train}; notes={notes_s}; bucket={bucket}"
            )
        idx[name] = {
            "case": case,
            "rc": rc,
            "verdict": verdict,
            "detail": detail,
            "all_cases": [(c, rcs[c]) for c in cases if c in rcs],
        }
    return idx


def transform_row(cols: list[str], soft_idx: dict[str, dict]) -> list[str] | None:
    """Old 12-col row -> new 12-col row. Returns None if not a data row."""
    if len(cols) < 12:
        return None
    name, algo, params, working, lastcheck, acc, goal, _mode, head, phase, note, conf = cols[:12]
    if name == "Имя" or set(name) <= {"-"}:
        return None
    if working not in RANK:
        return None
    info = soft_idx.get(name)
    if info is None:
        # Multi-case same name already handled; names not in SoftCold queue
        soft = "—"
        detail = "—"
        # Keep last SoftCold hint if LastCheck already SoftCold
        if "SoftCold" in lastcheck:
            soft = "PASS" if "PASS" in lastcheck else "FAIL"
            detail = lastcheck
    else:
        soft = info["verdict"]
        detail = info["detail"]
        # Multiple SoftCold cases on same Имя (br25_on/off, br100_keep/search)
        extras = info["all_cases"]
        if len(extras) > 1:
            bits = [f"{c}:{'PASS' if r == 0 else 'FAIL'}" for c, r in extras]
            detail = detail + "; also " + ", ".join(bits)
    return [name, algo, params, working, acc, goal, soft, detail, head, phase, note, conf]


def migrate_text(text: str, soft_idx: dict[str, dict]) -> str:
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        if line.strip() == OLD_HEADER.strip() or line.startswith(
            "| Имя | Алгоритм | Параметры | Working | LastCheck |"
        ):
            out.append(NEW_HEADER)
            continue
        if line.startswith("|-----") and "LastCheck" in "".join(out[-3:]) or (
            line.startswith("|-----") and "-----------|" in line and len(line) > 40
        ):
            # separator under old header
            if out and "SoftCold |" in out[-1]:
                out.append(NEW_SEP)
                continue
        if not line.startswith("|"):
            out.append(line)
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        new_cols = transform_row(cols, soft_idx)
        if new_cols is None:
            out.append(line)
            continue
        out.append("| " + " | ".join(new_cols) + " |")
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


SUMMARY_MARKER = "## SoftCold last matrix (full49 HEAD)"


def build_summary(soft_idx: dict[str, dict], rcs: list[tuple[str, int]]) -> str:
    buckets = parse_snap_buckets()
    pass_n = sum(1 for _, rc in rcs if rc == 0)
    fail_n = len(rcs) - pass_n
    lines = [
        SUMMARY_MARKER,
        "",
        f"Срез Console `18f0ef414b1f9c06` · PulseLib `dc2866a` · **{pass_n} PASS / {fail_n} FAIL** · "
        f"RCS [`_repro/SOFTCOLD_HEAD_rcs.txt`](_repro/SOFTCOLD_HEAD_rcs.txt) · "
        f"SNAP [`SOFTCOLD_FULL49_SNAP.md`](../../../Docs/Audit/TimeLearner-2026-09-26-review/evidence/SOFTCOLD_FULL49_SNAP.md).",
        "",
        "Ниже — **последняя SoftCold-попытка** (cold Train с нуля) по каждому case. "
        "Колонка **Working** в таблицах секций — сильнейший *успешный* протокол (часто GoldTest); "
        "**SoftCold** / **SoftColdDetail** — итог этой матрицы.",
        "",
        "| case | Имя | SoftCold | bucket | SoftColdDetail |",
        "|------|-----|----------|--------|----------------|",
    ]
    name_of = {c: n for c, n in CASE_TO_NAME.items()}
    for case, rc in rcs:
        name = name_of.get(case, case)
        info = soft_idx.get(name, {})
        # detail specific to this case
        prov = latest_prov(case)
        tipr = prov.get("tipr_class", "?")
        fc = prov.get("failure_class", "?")
        train = prov.get("train_status", "?")
        gate_rc = prov.get("gate_rc", "?")
        bucket = buckets.get(case, "?")
        verdict = "PASS" if rc == 0 else "FAIL"
        detail = f"tipr={tipr}; fc={fc}; gate_rc={gate_rc}; train={train}"
        lines.append(f"| `{case}` | `{name}` | **{verdict}** | {bucket} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def patch_legend(text: str) -> str:
    old = """## Колонки

| Имя | Алгоритм | Параметры | Working | LastCheck | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |

- **Имя** — канонический короткий id алгоритма. Путь Train/Test/CSV и bundle — в **Конфиги**.
- **Working** — сильнейший протокол с HEAD **PASS** для этого Имени (см. лестницу).
- **LastCheck** — протокол **этой** строки + вердикт (`SoftCold FAIL (B_need1)`, `GoldTest PASS`, …).
- **Acc** — успешные пробы / 8. `—` если gate CSV нет.
- **Цель** — срабатывание на целевом примере (`да`/`нет`/`—`). При Acc&lt;8/8 обязательно.
"""
    new = """## Колонки

| Имя | Алгоритм | Параметры | Working | Acc | Цель | SoftCold | SoftColdDetail | HEAD | PHASE12 | Примечание | Конфиги |

- **Имя** — канонический короткий id алгоритма. Путь Train/Test/CSV и bundle — в **Конфиги**.
- **Working** + **Acc** + **Цель** — сильнейший *успешный* протокол (GoldTest / SoftCold / …) и его метрики.
- **SoftCold** — вердикт последней SoftCold-матрицы для этого Имени: `PASS` / `FAIL` / `—` (не в очереди SoftCold-49).
- **SoftColdDetail** — подробности последней SoftCold-попытки: `case`, `tipr_class`, `failure_class`, `gate_rc`, `train_status`, `bucket` (стадия/причина).
- Не путать: строка с Working=`GoldTest` всё равно может иметь SoftCold=`FAIL` — cold с нуля не прошёл, gold на диске проходил.
"""
    if old in text:
        return text.replace(old, new)
    # SUCCESSFUL may have shorter legend
    old2 = "| Имя | Алгоритм | Параметры | Working | LastCheck | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |"
    if old2 in text and NEW_HEADER.split("SoftCold")[0] not in text:
        text = text.replace(old2, NEW_HEADER)
    return text


def insert_summary(text: str, summary: str) -> str:
    if SUMMARY_MARKER in text:
        # replace existing block until next ## 
        pat = re.compile(
            r"## SoftCold last matrix \(full49 HEAD\).*?(?=\n## |\n---\n)",
            re.S,
        )
        text2, n = pat.subn(summary + "\n", text, count=1)
        if n:
            return text2
    # insert before first "## 1." section
    m = re.search(r"\n---\n\n## 1\.", text)
    if m:
        return text[: m.start()] + "\n\n" + summary + "\n---\n\n## 1." + text[m.end() :]
    return summary + "\n\n" + text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    soft_idx = build_softcold_index()
    rcs = parse_rcs(RCS)
    summary = build_summary(soft_idx, rcs)
    for path in (ROOT / "EXPERIMENTS.md", ROOT / "SUCCESSFUL_EXPERIMENTS.md"):
        text = path.read_text(encoding="utf-8")
        text = patch_legend(text)
        text = migrate_text(text, soft_idx)
        if path.name == "EXPERIMENTS.md":
            text = insert_summary(text, summary)
        # SUCCESSFUL: shorter note under header
        if path.name == "SUCCESSFUL_EXPERIMENTS.md" and SUMMARY_MARKER not in text:
            note = (
                "\n**SoftCold full49:** см. сводку в [`EXPERIMENTS.md`](EXPERIMENTS.md) "
                "(§ SoftCold last matrix). В таблицах ниже колонки **SoftCold** / **SoftColdDetail** "
                "— последняя cold-попытка; **Working**/Acc — успешный протокол.\n"
            )
            text = text.replace(
                "## Колонки\n",
                note + "\n## Колонки\n",
                1,
            )
        if args.dry_run:
            print(path, "softcold_names", len(soft_idx), "chars", len(text))
            continue
        path.write_text(text, encoding="utf-8")
        print(f"updated {path}")


if __name__ == "__main__":
    main()

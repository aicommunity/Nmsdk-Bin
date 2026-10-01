#!/usr/bin/env python3
"""One-shot: replace Протокол column with Working | LastCheck in registry tables."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

RANK = {
    "SoftCold": 40,
    "SoftColdOff": 30,
    "SkipTrainGold": 20,
    "GoldTest": 10,
    "MatrixClone": 10,
    "none": 0,
}


def proto_to_working_token(proto: str) -> str:
    p = proto.strip()
    if p.startswith("SoftCold+PostTuneOff"):
        return "SoftColdOff"
    if p.startswith("SoftCold"):
        return "SoftCold"
    if p.startswith("SkipTrainGold"):
        return "SkipTrainGold"
    if p.startswith("MatrixClone"):
        return "MatrixClone"
    if p.startswith("GoldTest"):
        return "GoldTest"
    return "none"


def lastcheck_from_row(proto: str, head: str) -> str:
    token = proto_to_working_token(proto)
    h = head.replace("**", "").strip()
    if token == "SoftColdOff":
        label = "SoftCold+PostTuneOff"
    elif token == "SoftCold":
        label = "SoftCold"
    else:
        label = token if token != "none" else proto.strip() or "—"
    if h == "PASS":
        return f"{label} PASS"
    if h == "FAIL":
        return f"{label} FAIL"
    if h == "NOT_RETESTED":
        return f"{label} NOT_RETESTED"
    return f"{label} {h}" if h else label


def split_row(line: str) -> list[str]:
    if not line.startswith("|"):
        return []
    parts = line.strip().split("|")
    # leading/trailing empty from split
    return [p.strip() for p in parts[1:-1]]


def join_row(cols: list[str]) -> str:
    return "| " + " | ".join(cols) + " |"


STD_HEADER = (
    "| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |"
)
NEW_HEADER = (
    "| Имя | Алгоритм | Параметры | Working | LastCheck | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |"
)
STD_SEP = "|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|"
NEW_SEP = (
    "|-----|----------|-----------|---------|-----------|-----|------|-------|------|----------|------------|---------|"
)

LEGEND_HEADER = STD_HEADER  # same shape in "Колонки" section


def collect_working(text: str) -> dict[str, str]:
    """Strongest PASS Working token per Имя across standard 11-col data rows."""
    best: dict[str, tuple[int, str]] = {}
    for line in text.splitlines():
        cols = split_row(line)
        if len(cols) != 11:
            continue
        if cols[0] in ("Имя", "-----") or cols[0].startswith("---"):
            continue
        if "Алгоритм" in cols[0]:
            continue
        name, proto, head = cols[0], cols[3], cols[7]
        if "PASS" not in head.replace(" ", ""):
            # allow **PASS**
            if "PASS" not in head:
                continue
        token = proto_to_working_token(proto)
        # MatrixClone rows sometimes labeled GoldTest in Протокол but PHASE12 VALIDATED_CLONE
        if "VALIDATED_CLONE" in cols[8] and token == "GoldTest":
            token = "MatrixClone"
        if "MatrixClone" in cols[9] and token == "GoldTest":
            token = "MatrixClone"
        rank = RANK.get(token, 0)
        cur = best.get(name)
        if cur is None or rank > cur[0]:
            best[name] = (rank, token)
    return {k: v[1] for k, v in best.items()}


def migrate_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    working_map = collect_working(text)
    out: list[str] = []
    for line in text.splitlines():
        if line.strip() == STD_HEADER.strip() or line == STD_HEADER:
            out.append(NEW_HEADER)
            continue
        if line.strip() == STD_SEP.strip() or line == STD_SEP:
            out.append(NEW_SEP)
            continue
        cols = split_row(line)
        if len(cols) == 11 and cols[0] != "Имя" and not cols[0].startswith("---"):
            # data row of standard registry table
            name, algo, params, proto = cols[0], cols[1], cols[2], cols[3]
            rest = cols[4:]  # Acc ... Конфиги
            head = cols[7]
            phase12 = cols[8]
            note = cols[9]
            w = working_map.get(name, "none")
            # If this row itself is PASS with stronger semantics for MatrixClone labeling
            if "PASS" in head:
                tok = proto_to_working_token(proto)
                if "VALIDATED_CLONE" in phase12 or "MatrixClone" in note:
                    if tok in ("GoldTest", "MatrixClone"):
                        tok = "MatrixClone"
                if RANK.get(tok, 0) >= RANK.get(w, 0):
                    w = tok
            # SoftCold FAIL rows: Working stays gold-level from map (may be GoldTest)
            if w == "none" and "PASS" in head:
                w = proto_to_working_token(proto)
            lc = lastcheck_from_row(proto, head)
            # Enrich SoftCold FAIL lastcheck with short basket hint from note
            if "FAIL" in head and proto.startswith("SoftCold"):
                if "NonSeparable" in note or "Landscape" in note:
                    lc = "SoftCold FAIL (A_nonseparable)"
                elif "AmpNorm" in note or "Need=1" in note or "TipR@Rmin" in note:
                    lc = "SoftCold FAIL (B_need1)"
                elif "runaway" in note.lower() or "EstDelay" in note:
                    lc = "SoftCold FAIL (EstDelay/B)"
            new_cols = [name, algo, params, w, lc, *rest]
            out.append(join_row(new_cols))
            continue
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"migrated {path}: {len(working_map)} names with Working")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    for name in ("EXPERIMENTS.md", "SUCCESSFUL_EXPERIMENTS.md"):
        migrate_file(root / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

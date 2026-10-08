#!/usr/bin/env python3
"""Build SoftCold FULL49 SNAP markdown from RCS + latest run provenance/tipr."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RCS = ROOT / "_repro" / "SOFTCOLD_HEAD_rcs.txt"
RUNS = ROOT / "_repro" / "runs"
OUT = Path(
    "/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/"
    "SOFTCOLD_FULL49_SNAP.md"
)

RMIN = 2.0e7
RMAX = 1.0e11


def parse_rcs() -> list[tuple[str, int, str]]:
    rows = []
    for line in RCS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        rows.append((parts[0], int(parts[1]), parts[2] if len(parts) > 2 else ""))
    return rows


def latest_run(case: str) -> Path | None:
    """Prefer finalized bundle (tipr_final) over live *_work."""
    cands = [p for p in RUNS.glob(f"{case}_*") if p.is_dir()]
    cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for p in cands:
        if (p / "Train" / "tipr_final.txt").exists():
            return p
    for p in cands:
        if (p / "Train" / "Parameters_00.xml").exists() or (p / "provenance.json").exists():
            return p
    return None


def tipr_bucket(case: str, tipr: str, failure_class: str, rc: int) -> str:
    if rc == 0:
        return "PASS"
    if case in ("br100_keep", "br100_search"):
        return "G"
    if case == "br25_on":
        return "N"
    nums = []
    for tok in tipr.replace(",", " ").replace("e07", "e7").split():
        try:
            nums.append(float(tok))
        except ValueError:
            pass
    active = nums[:3] if nums else []
    if case.endswith("_nextseg") and active and all(abs(x - 8.6e7) / 8.6e7 < 0.08 for x in active):
        return "A"
    if not active:
        return "D_unclassified"
    mx = max(active)
    mn = min(active)
    if mx >= 0.9 * RMAX:
        return "D"
    if all(abs(x - RMIN) / max(RMIN, 1.0) < 0.08 for x in active):
        return "E"
    if all(abs(x - 8.6e7) / 8.6e7 < 0.08 for x in active):
        return "A"
    # Branch / mid-band TipR
    if case.startswith("br480") or case == "br25_preinh":
        return "B"
    if mn > RMIN * 1.2 and mx < 0.5 * RMAX:
        return "B"
    if mx > RMIN * 3 and mx < 0.9 * RMAX:
        return "B"
    return "other"


def main() -> None:
    rows = parse_rcs()
    lines = [
        "# SoftCold FULL49 SNAP (HEAD 2026-10-07/08)",
        "",
        "Срез: Console `18f0ef414b1f9c06` · PulseLib `dc2866a` · PARALLEL=6 · "
        "RCS [`SOFTCOLD_HEAD_rcs.txt`](../../../Bin/Configs/SpikeSamples/StructTrain/_repro/SOFTCOLD_HEAD_rcs.txt).",
        "",
        "| case | rc | tipr_class | failure_class | Need | TipR | L | bucket |",
        "|------|----|------------|---------------|------|------|---|--------|",
    ]
    counts: dict[str, int] = {}
    for case, rc, _utc in rows:
        run = latest_run(case)
        tipr = need = L = tipr_class = failure_class = "?"
        if run:
            prov = run / "provenance.json"
            if prov.exists():
                try:
                    data = json.loads(prov.read_text(encoding="utf-8"))
                    tipr_class = str(data.get("tipr_class") or "?")
                    failure_class = str(data.get("failure_class") or "?")
                except json.JSONDecodeError:
                    pass
            tipr_path = run / "Train" / "tipr_final.txt"
            if tipr_path.exists():
                tipr = " ".join(tipr_path.read_text(encoding="utf-8").split()[:4])
            live = run / "Train" / "posttune_tipr_live.txt"
            if live.exists():
                text = live.read_text(encoding="utf-8")
                m = re.search(r"tipr=([^\n]+)", text)
                if m and tipr == "?":
                    tipr = " ".join(m.group(1).split()[:4])
                m = re.search(r"\bneed=(\S+)", text)
                if m:
                    need = m.group(1)
                m = re.search(r"\bL=([^\n]+)", text)
                if m:
                    L = " ".join(m.group(1).split()[:4])
            params = run / "Train" / "Parameters_00.xml"
            if params.exists():
                pt = params.read_text(encoding="utf-8", errors="replace")
                if need == "?":
                    m = re.search(r"<IsNeedToTrain>([^<]+)", pt)
                    if m:
                        need = m.group(1).strip()
                if tipr == "?":
                    m = re.search(r"<TipSynapseResistance>([^<]+)", pt)
                    if m:
                        tipr = " ".join(m.group(1).replace(",", " ").split()[:4])
                if L == "?":
                    m = re.search(r"<DendriteLength>([^<]+)", pt)
                    if m:
                        L = " ".join(m.group(1).replace(",", " ").split()[:4])
        bucket = tipr_bucket(case, tipr, failure_class, rc)
        counts[bucket] = counts.get(bucket, 0) + 1
        tipr_s = tipr.replace("|", " ")
        L_s = L.replace("|", " ")
        lines.append(
            f"| `{case}` | {rc} | {tipr_class} | {failure_class} | {need} | `{tipr_s}` | `{L_s}` | **{bucket}** |"
        )
    lines.extend(["", "## Counts", ""])
    for k in sorted(counts):
        lines.append(f"- **{k}**: {counts[k]}")
    lines.append("")
    lines.append(f"PASS+FAIL check: {sum(1 for _, rc, _ in rows if rc == 0)} PASS / "
                 f"{sum(1 for _, rc, _ in rows if rc != 0)} FAIL / {len(rows)} total.")
    lines.append("")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT} rows={len(rows)} counts={counts}")


if __name__ == "__main__":
    main()

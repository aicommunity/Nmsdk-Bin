#!/usr/bin/env bash
# Scan StatisticLog trees under SelectivityAsymRm and write statisticlog_manifest.json.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="${MANIFEST:-$ROOT/statisticlog_manifest.json}"

python3 - "$ROOT" "$MANIFEST" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])

# Protected snapshots for audit phases (relative to ROOT).
PROTECTED: list[dict] = [
    {
        "exp": "EXP_span25ms_packA_gen",
        "timestamp": "2026.09.02 09-13-20",
        "phase": "phase3_l_oscillation",
        "keep_until": "phase3_done",
        "note": "L oscillation audit",
    },
    {
        "exp": "EXP_span25ms_packA_gen",
        "timestamp": "2026.09.02 11-13-10",
        "phase": "phase3_finish",
        "keep_until": "phase3_done",
        "note": "finish_lref/amp",
    },
    {
        "exp": "EXP_span25ms_packA_preinh",
        "timestamp": "2026.09.02 09-13-20",
        "phase": "phase4_preinh_audit",
        "keep_until": "phase4b_done",
        "note": "preinh disk-full era",
    },
    {
        "exp": "EXP_span25ms_packA_preinh",
        "timestamp": "2026.09.02 11-13-09",
        "phase": "phase4_preinh_audit",
        "keep_until": "phase4b_done",
        "note": "finish_lref",
    },
    {
        "exp": "EXP_span25ms_packA_preinh",
        "timestamp": "2026.08.31 21-30-39",
        "phase": "phase4_preinh_audit",
        "keep_until": "phase4a_metrics_exported",
        "note": "pilot v3 preinh — prune only after preinh_audit_metrics.json",
    },
    {
        "exp": "EXP_span100ms_packA_preinh",
        "timestamp": "2026.09.01 01-34-18",
        "phase": "phase6_span100",
        "keep_until": "phase6_done",
        "note": "span100 plateau",
    },
    {
        "exp": "EXP_span100ms_packA_preinh",
        "timestamp": "2026.09.01 20-17-31",
        "phase": "phase6_span100",
        "keep_until": "phase6_done",
        "note": "span100 plateau",
    },
]


def dir_size(path: Path) -> int:
    try:
        out = subprocess.check_output(["du", "-sb", str(path)], text=True)
        return int(out.split()[0])
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        total = 0
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
        return total


entries: list[dict] = []
seen_paths: set[str] = set()

for item in PROTECTED:
    exp = item["exp"]
    ts = item["timestamp"]
    for sub in ("Train", "Test"):
        p = root / exp / sub / "StatisticLog" / ts
        if not p.is_dir():
            continue
        rel = str(p.relative_to(root))
        if rel in seen_paths:
            continue
        seen_paths.add(rel)
        entries.append(
            {
                "path": rel,
                "abs_path": str(p),
                "exp": exp,
                "timestamp": ts,
                "phase": item["phase"],
                "keep_until": item["keep_until"],
                "note": item.get("note", ""),
                "size_bytes": dir_size(p),
                "protected": True,
            }
        )

# All StatisticLog dirs under campaign
all_dirs: list[dict] = []
for stat_root in sorted(root.glob("EXP_*/Train/StatisticLog")) + sorted(
    root.glob("EXP_*/Test/StatisticLog")
):
    if not stat_root.is_dir():
        continue
    for ts_dir in sorted(stat_root.iterdir()):
        if not ts_dir.is_dir():
            continue
        rel = str(ts_dir.relative_to(root))
        sz = dir_size(ts_dir)
        protected = any(e["path"] == rel for e in entries)
        all_dirs.append(
            {
                "path": rel,
                "abs_path": str(ts_dir),
                "size_bytes": sz,
                "protected": protected,
            }
        )

doc = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "campaign_root": str(root),
    "protected": entries,
    "all_statistic_dirs": all_dirs,
    "total_bytes": sum(d["size_bytes"] for d in all_dirs),
    "protected_bytes": sum(e["size_bytes"] for e in entries),
    "prunable_bytes": sum(d["size_bytes"] for d in all_dirs if not d["protected"]),
}

manifest_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
print(f"Wrote {manifest_path}")
print(f"  dirs={len(all_dirs)} protected={len(entries)} total={doc['total_bytes']/1e9:.2f}GB prunable={doc['prunable_bytes']/1e9:.2f}GB")
PY

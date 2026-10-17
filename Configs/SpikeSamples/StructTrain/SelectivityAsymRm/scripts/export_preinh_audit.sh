#!/usr/bin/env bash
# Merge preinh audit JSONs into PREINH_INTEGRITY_REPORT.md and preinh_audit_metrics.json
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_JSON="$ROOT/preinh_audit_metrics.json"
OUT_MD="$ROOT/PREINH_INTEGRITY_REPORT.md"

python3 - "$ROOT" "$OUT_JSON" "$OUT_MD" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
out_json = Path(sys.argv[2])
out_md = Path(sys.argv[3])

runs = []
for p in sorted(root.glob("preinh_audit_*.json")):
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        runs.extend(data)
    else:
        runs.append(data)

doc = {"runs": runs, "verdict": "CORRUPT" if any(
    not r.get("all_non_ref_sync_ok") and any(
        d.get("last_abs_dt", 0) >= 1.5 for d in r.get("dendrites", []) if d.get("dendrite", 99) < 3
    ) for r in runs
) else "OK"}

out_json.write_text(json.dumps(doc, indent=2), encoding="utf-8")

lines = ["# Preinh Integrity Report", "", f"**Verdict:** {doc['verdict']}", ""]
for r in runs:
    stat = (r.get("integrity") or {}).get("stat_dir", "?")
    lines.append(f"## {stat}")
    lines.append(f"- all_non_ref_sync_ok: {r.get('all_non_ref_sync_ok')}")
    for d in r.get("dendrites", []):
        if d.get("dendrite", 99) >= 3:
            continue
        lines.append(
            f"  - d{d['dendrite']}: dt={d.get('last_abs_dt')} peak_valid={d.get('peak_valid')} "
            f"shape={d.get('peak_shape')}"
        )
    lines.append("")

if doc["verdict"] == "CORRUPT":
    lines.extend([
        "## Recommendation",
        "",
        "Traces show sentinel last_abs_dt=1.501 and invalid peaks — **cold reset preinh** required.",
        "",
    ])

out_md.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {out_json} and {out_md} verdict={doc['verdict']}")
PY

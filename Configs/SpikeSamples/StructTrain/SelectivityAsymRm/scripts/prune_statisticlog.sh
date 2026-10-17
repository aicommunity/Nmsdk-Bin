#!/usr/bin/env bash
# Remove StatisticLog timestamp dirs NOT listed as protected in statisticlog_manifest.json.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="${MANIFEST:-$ROOT/statisticlog_manifest.json}"
DRY_RUN=1
APPLY=0

usage() {
  echo "Usage: $0 [--dry-run|--apply] [--manifest PATH]" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; APPLY=0; shift ;;
    --apply) DRY_RUN=0; APPLY=1; shift ;;
    --manifest) MANIFEST="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown: $1" >&2; usage ;;
  esac
done

[[ -f "$MANIFEST" ]] || {
  echo "Manifest missing: $MANIFEST — run inventory_statisticlog.sh first" >&2
  exit 1
}

python3 - "$ROOT" "$MANIFEST" "$DRY_RUN" <<'PY'
import json
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
dry_run = sys.argv[3] == "1"

doc = json.loads(manifest_path.read_text(encoding="utf-8"))
protected = {e["path"] for e in doc.get("protected", [])}
to_remove: list[tuple[str, int]] = []

for d in doc.get("all_statistic_dirs", []):
    rel = d["path"]
    if d.get("protected") or rel in protected:
        continue
    to_remove.append((rel, int(d.get("size_bytes", 0))))

to_remove.sort()
total = sum(sz for _, sz in to_remove)
print(f"{'DRY-RUN' if dry_run else 'APPLY'}: {len(to_remove)} dirs, ~{total/1e9:.2f} GB")

for rel, sz in to_remove:
    p = root / rel
    print(f"  {'rm' if not dry_run else 'would rm'} {rel} ({sz/1e9:.2f} GB)")
    if not dry_run and p.is_dir():
        shutil.rmtree(p)

if dry_run:
    print("Re-run with --apply to delete.")
PY

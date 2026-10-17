#!/usr/bin/env bash
# Run analyze_separability.py + sweep_ltz_threshold.py on all results.csv under a grid root.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GRID="${1:-$ROOT/FastSpanLtzCal}"
OUT="${2:-$ROOT/separability_summary.csv}"
shopt -s nullglob
mapfile -t CSVS < <(find "$GRID" -path '*/Test/SelectivityLog/results.csv' | sort)
if ((${#CSVS[@]} == 0)); then
  echo "No results.csv under $GRID" >&2
  exit 1
fi
python3 "$ROOT/scripts/analyze_separability.py" "${CSVS[@]}" --out "$OUT"
echo "=== LTZ sweep ==="
python3 "$ROOT/scripts/sweep_ltz_threshold.py" "${CSVS[@]}"

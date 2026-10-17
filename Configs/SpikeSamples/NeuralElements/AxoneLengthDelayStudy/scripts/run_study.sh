#!/usr/bin/env bash
# Run all cells in parallel, extract latency, plot.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NE_SCRIPTS="$(cd "$ROOT/../scripts" && pwd)"
export MAX_JOBS="${MAX_JOBS:-4}"
SIM_T="${SIM_T:-0.5}"

# Clear previous StatisticLog for clean metrics
find "$ROOT/cells" -type d -name StatisticLog -prune -exec rm -rf {} + 2>/dev/null || true

"$NE_SCRIPTS/run_parallel.sh" "$ROOT/cells" "$SIM_T"
python3 "$ROOT/scripts/extract_latency.py" --batch "$ROOT/cells" --grid "$ROOT/grid_cells.tsv" --out "$ROOT/metrics.csv"
python3 "$ROOT/scripts/plot_latency.py" --metrics "$ROOT/metrics.csv" --outdir "$ROOT/plots"
echo "study complete: metrics.csv + plots/"

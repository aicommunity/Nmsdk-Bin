#!/usr/bin/env bash
# Train + sync + Test for BranchFastSpan (after regression PASS).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GRID="$ROOT/BranchFastSpan"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
COPY="$ROOT/scripts/copy_config_branch.sh"
META="$ROOT/grid_branch.tsv"
LOG="$ROOT/run_branch.log"
TRAIN_T="${TRAIN_T:-160}"
TEST_T="${TEST_T:-20}"

if [[ -f "$ROOT/REGRESSION.md" ]] && grep -q '\*\*FAIL\*\*' "$ROOT/REGRESSION.md"; then
  echo "Regression FAIL — branch grid blocked." >&2
  exit 1
fi

mapfile -t EXPS < <(awk -F'\t' 'NR>1{print $1}' "$META")

exec > >(tee "$LOG") 2>&1

for exp in "${EXPS[@]}"; do
  dir="$GRID/$exp/Train"
  echo "=== TRAIN $exp ==="
  (cd "$dir" && "$NM" -c Project.ini -s -t "$TRAIN_T" -x -S >run_console.log 2>&1)
done

for exp in "${EXPS[@]}"; do
  echo "=== SYNC $exp ==="
  "$COPY" sync "$GRID/$exp/Train" "$GRID/$exp/Test"
done

for exp in "${EXPS[@]}"; do
  dir="$GRID/$exp/Test"
  echo "=== TEST $exp ==="
  (cd "$dir" && "$NM" -c Project.ini -s -t "$TEST_T" -x >run_console.log 2>&1)
done

echo "Branch grid run complete."

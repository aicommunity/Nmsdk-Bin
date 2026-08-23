#!/usr/bin/env bash
# Train + sync + Test for RegressionFull480 (fail-hard).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REG="$ROOT/RegressionFull480"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
COPY="$ROOT/scripts/copy_config.sh"
META="$ROOT/grid_regression.tsv"
LOG="$ROOT/run_regression.log"
TRAIN_T="${TRAIN_T:-160}"
TEST_T="${TEST_T:-20}"

mapfile -t EXPS < <(awk -F'\t' 'NR>1{print $1}' "$META")

exec > >(tee "$LOG") 2>&1

for exp in "${EXPS[@]}"; do
  dir="$REG/$exp/Train"
  ini=Project.ini
  [[ -f "$dir/project.ini" ]] && ini=project.ini
  echo "=== TRAIN $exp ==="
  (cd "$dir" && "$NM" -c "$ini" -s -t "$TRAIN_T" -x -S >run_console.log 2>&1)
done

for exp in "${EXPS[@]}"; do
  echo "=== SYNC $exp ==="
  "$COPY" sync "$REG/$exp/Train" "$REG/$exp/Test"
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  python3 - "$REG/$exp/Test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
p = Path(sys.argv[1]); neuron = sys.argv[2]
t = p.read_text(encoding="utf-8")
t = re.sub(rf"(<NeuronClassName\b[^>]*>)[^<]*(</NeuronClassName>)", rf"\g<1>{neuron}\2", t, count=1)
p.write_text(t, encoding="utf-8")
PY
done

for exp in "${EXPS[@]}"; do
  dir="$REG/$exp/Test"
  ini=Project.ini
  [[ -f "$dir/project.ini" ]] && ini=project.ini
  echo "=== TEST $exp ==="
  (cd "$dir" && "$NM" -c "$ini" -s -t "$TEST_T" -x >run_console.log 2>&1)
done

python3 "$ROOT/scripts/verify_regression.py" --root "$ROOT"
echo "Regression run complete."

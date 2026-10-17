#!/usr/bin/env bash
set -euo pipefail
NM=/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole
ROOT=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPhaseA

run_test() {
  local ini="$1"
  echo "=== TEST $ini ==="
  "$NM" -c "$ini" -s -t 20 -x 2>&1 | tail -2 || true
}

run_train() {
  local ini="$1"
  echo "=== TRAIN $ini ==="
  "$NM" -c "$ini" -s -t 160 -x -S 2>&1 | tail -5
}

accuracy() {
  python3 - <<PY
import csv
from pathlib import Path
rows=list(csv.DictReader(Path("$1").open()))
ok=sum(1 for r in rows if r["match"]=="1")
print(f"{ok}/8")
PY
}

# EXP01 confirm
for d in "$ROOT"/EXP01_ltz_threshold_sweep/Test_thr*; do
  run_test "$d/Project.ini"
  echo "$(basename "$d"): $(accuracy "$d/SelectivityLog/results.csv")"
done

# EXP02
for d in "$ROOT"/EXP02_ltzone_average_mode/Test_avg*; do
  run_test "$d/Project.ini"
  echo "$(basename "$d"): $(accuracy "$d/SelectivityLog/results.csv")"
done

SCR="$ROOT/scripts/copy_config.sh"
for exp in EXP03_sync_tolerance_015 EXP04_sync_tolerance_010 EXP05_resistance_gain_025; do
  run_train "$ROOT/$exp/Train/Project.ini"
  $SCR sync "$ROOT/$exp/Train" "$ROOT/$exp/Test"
  run_test "$ROOT/$exp/Test/Project.ini"
  echo "$exp: $(accuracy "$ROOT/$exp/Test/SelectivityLog/results.csv")"
done

# EXP06 subset (skip full 9 if too slow - run all per plan)
for d in "$ROOT"/EXP06_ltzone_integration/Test_*; do
  run_test "$d/Project.ini"
  echo "$(basename "$d"): $(accuracy "$d/SelectivityLog/results.csv")"
done

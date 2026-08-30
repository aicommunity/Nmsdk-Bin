#!/usr/bin/env bash
# GTS and Dissoc×Secr timing sweep on pilot EXP (default: 3 Pack A pilot).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RESET="$ROOT/scripts/reset_asymrm_cold.sh"
RUN="$ROOT/scripts/run_asymrm.sh"
FEAS="$ROOT/scripts/check_timing_feasibility.py"
STALL="$ROOT/scripts/analyze_train_stall.py"
OUT_DIR="$ROOT/timing_sweep"
PILOT_EXPS="${PILOT_EXPS:-EXP_span25ms_packA_gen EXP_span25ms_packA_preinh EXP_span100ms_packA_preinh}"
MAX_JOBS="${MAX_JOBS:-3}"
TRAIN_T="${TRAIN_T:-80}"
ADAPTIVE_TRAIN="${ADAPTIVE_TRAIN:-0}"

mkdir -p "$OUT_DIR"

GTS_VALUES="${GTS_VALUES:-10000 15000 20000}"
DISSOC_SECR_GRID="${DISSOC_SECR_GRID:-0.0005:0.0005 0.001:0.001 0.002:0.002}"

run_case() {
  local tag="$1" gts="$2" dissoc="$3" secr="$4"
  echo "======== CASE $tag GTS=$gts Dissoc=$dissoc Secr=$secr ========"
  GTS="$gts" DISSOC="$dissoc" SECR="$secr" PILOT_EXPS="$PILOT_EXPS" RESET_TEST=0 bash "$RESET"
  GTS="$gts" DISSOC="$dissoc" SECR="$secr" PILOT_EXPS="$PILOT_EXPS" \
    MAX_JOBS="$MAX_JOBS" TRAIN_T="$TRAIN_T" ADAPTIVE_TRAIN="$ADAPTIVE_TRAIN" \
    ALLOW_PARTIAL_TRAIN=1 bash "$RUN" || true
  local case_dir="$OUT_DIR/${tag}_gts${gts}_d${dissoc}"
  mkdir -p "$case_dir"
  cp "$ROOT/grid_summary.csv" "$case_dir/grid_summary.csv" 2>/dev/null || true
  cp "$ROOT/stall_latest.csv" "$case_dir/stall_latest.csv" 2>/dev/null || true
  cp "$ROOT/feasibility_latest.csv" "$case_dir/feasibility_latest.csv" 2>/dev/null || true
  python3 "$FEAS" --post $(for e in $PILOT_EXPS; do echo "$ROOT/$e/Train/Parameters_00.xml"; done) \
    -o "$case_dir/timing_feasibility.csv" 2>/dev/null || true
  python3 "$STALL" $(for e in $PILOT_EXPS; do echo "$ROOT/$e/Train"; done) \
    -o "$case_dir/stall_summary.csv" 2>/dev/null || true
  echo "$tag,$gts,$dissoc,$secr,$(date -Iseconds)" >> "$OUT_DIR/sweep_log.tsv"
}

printf "tag\tgts\tdissoc\tsecr\ttimestamp\n" > "$OUT_DIR/sweep_log.tsv"

echo "=== GTS sweep (Dissoc=Secr=0.001 locked) ==="
for gts in $GTS_VALUES; do
  run_case "gts" "$gts" "0.001" "0.001"
done

echo "=== Dissoc×Secr sweep (best GTS from above — default GTS=20000) ==="
BEST_GTS="${BEST_GTS:-20000}"
for pair in $DISSOC_SECR_GRID; do
  dissoc="${pair%%:*}"
  secr="${pair##*:}"
  run_case "timing" "$BEST_GTS" "$dissoc" "$secr"
done

echo "Sweep done. Results in $OUT_DIR"

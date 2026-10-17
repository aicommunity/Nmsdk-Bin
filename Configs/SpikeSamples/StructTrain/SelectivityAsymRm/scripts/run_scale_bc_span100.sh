#!/usr/bin/env bash
# Wave 3: Pack B/C span100 only — after Pack A span100 protocol works.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PILOT_EXPS="${SCALE_PILOT_EXPS:-EXP_span100ms_packB_gen EXP_span100ms_packB_preinh EXP_span100ms_packC_gen EXP_span100ms_packC_preinh}"
unset AMP_ONLY || true
export L_REFERENCE="${L_REFERENCE:-ltzcal}"
export SEED_INITIAL="${SEED_INITIAL:-1}"
export INITIAL_SOURCE="${INITIAL_SOURCE:-ltzcal}"
export ADAPTIVE_TRAIN="${ADAPTIVE_TRAIN:-1}"
export MAX_JOBS="${MAX_JOBS:-6}"
export SKIP_COLD_RESET="${SKIP_COLD_RESET:-1}"
export LENGTH_STEPS_SPAN100="${LENGTH_STEPS_SPAN100:-80 160 320 640 1280 2560}"
export LENGTH_MAX_STEP="${LENGTH_MAX_STEP:-2560}"
export WALL_BUDGET_CHECK="${WALL_BUDGET_CHECK:-1}"
export AMP_TRAIN_STEPS="${AMP_TRAIN_STEPS:-320 640 1280}"
exec env -u AMP_ONLY bash "$ROOT/scripts/run_asymrm.sh"

#!/usr/bin/env bash
# Wave 1: Pack B/C span25 only (MAX_JOBS default 6).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PILOT_EXPS="${SCALE_PILOT_EXPS:-EXP_span25ms_packB_gen EXP_span25ms_packB_preinh EXP_span25ms_packC_gen EXP_span25ms_packC_preinh}"
unset AMP_ONLY || true
export L_REFERENCE="${L_REFERENCE:-ltzcal}"
export SEED_INITIAL="${SEED_INITIAL:-1}"
export ADAPTIVE_TRAIN="${ADAPTIVE_TRAIN:-1}"
export MAX_JOBS="${MAX_JOBS:-6}"
export SIGNAL_REF_JSON="${SIGNAL_REF_JSON:-$ROOT/signal_reference_span25.json}"
export LENGTH_STEPS_SPAN25="${LENGTH_STEPS_SPAN25:-80 160 320 640 1280 2560}"
export AMP_TRAIN_STEPS="${AMP_TRAIN_STEPS:-320 640 1280}"
exec env -u AMP_ONLY bash "$ROOT/scripts/run_asymrm.sh"

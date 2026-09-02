#!/usr/bin/env bash
# Phase 2: span25 amp after L-ref refresh (gen: partial sync; preinh: force amp at L_ref).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/finish_pilot_amp.log"
export PILOT_EXPS="EXP_span25ms_packA_gen EXP_span25ms_packA_preinh"
export ADAPTIVE_TRAIN=1 MAX_JOBS=2 L_REFERENCE=ltzcal
export AMP_ONLY=1 AMP_SKIP_REFRESH=1
export AMP_PARTIAL_AT_L_REF=1 AMP_FORCE_AT_L_REF=1
export AMP_TRAIN_STEPS="${AMP_TRAIN_STEPS:-320 640 1280}"
export ALLOW_PARTIAL_TRAIN=1
exec > >(tee -a "$LOG") 2>&1
echo "=== finish_pilot_amp $(date -Iseconds) ==="
bash "$ROOT/scripts/run_asymrm.sh"

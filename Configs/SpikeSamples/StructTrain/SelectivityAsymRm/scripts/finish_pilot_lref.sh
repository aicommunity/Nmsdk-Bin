#!/usr/bin/env bash
# Finish span25 pilot: L-ref refresh + amp (skip span100 — LENGTH_UNDER hopeless).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/finish_pilot_lref.log"
export PILOT_EXPS="EXP_span25ms_packA_gen EXP_span25ms_packA_preinh"
export ADAPTIVE_TRAIN=1 MAX_JOBS=2 L_REFERENCE=ltzcal L_REF_REFRESH=320
export ALLOW_PARTIAL_TRAIN=1 L_REF_ONLY=1 L_REF_REFRESH=320
export AMP_TRAIN_STEPS="${AMP_TRAIN_STEPS:-320 640 1280}"
exec > >(tee "$LOG") 2>&1
echo "=== finish_pilot_lref $(date -Iseconds) ==="
bash "$ROOT/scripts/run_asymrm.sh"

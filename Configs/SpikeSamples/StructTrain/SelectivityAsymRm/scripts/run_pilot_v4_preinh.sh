#!/usr/bin/env bash
# Phase 4b: cold reset preinh after corrupt traces, then train.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PILOT_EXPS="EXP_span25ms_packA_preinh"
export L_REFERENCE="${L_REFERENCE:-ltzcal}"
export ADAPTIVE_TRAIN=1
export SIGNAL_REF_JSON="$ROOT/signal_reference_span25.json"

echo "=== Phase 4b: preinh cold reset + train ==="
"$ROOT/scripts/reset_asymrm_cold.sh" $PILOT_EXPS
exec "$ROOT/scripts/run_asymrm.sh"

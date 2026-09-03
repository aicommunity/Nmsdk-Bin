#!/usr/bin/env bash
# Pilot v4: span25 gen cold reset + adaptive train with signal_fidelity gate.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PILOT_EXPS="EXP_span25ms_packA_gen"
export L_REFERENCE="${L_REFERENCE:-ltzcal}"
export ADAPTIVE_TRAIN=1
export WALL_BUDGET_CHECK="${WALL_BUDGET_CHECK:-1}"
export SIGNAL_REF_JSON="$ROOT/signal_reference_span25.json"

echo "=== Pilot v4 span25 gen ==="
if [[ "${SKIP_COLD_RESET:-0}" != "1" ]]; then
  "$ROOT/scripts/reset_asymrm_cold.sh" "$PILOT_EXPS"
fi

exec "$ROOT/scripts/run_asymrm.sh"

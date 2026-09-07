#!/usr/bin/env bash
# Pilot span100 — separate protocol with length guard (no blind 5120 steps).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PILOT_EXPS="${PILOT_SPAN100_EXPS:-EXP_span100ms_packA_gen EXP_span100ms_packA_preinh}"
export L_REFERENCE="${L_REFERENCE:-ltzcal}"
export ADAPTIVE_TRAIN=1
export SEED_INITIAL="${SEED_INITIAL:-1}"
export INITIAL_SOURCE="${INITIAL_SOURCE:-ltzcal}"
export LENGTH_STEPS_SPAN100="${LENGTH_STEPS_SPAN100:-80 160 320 640 1280 2560}"
export LENGTH_MAX_STEP="${LENGTH_MAX_STEP:-2560}"
export WALL_BUDGET_CHECK=1
export SKIP_COLD_RESET="${SKIP_COLD_RESET:-1}"
export MAX_JOBS="${MAX_JOBS:-6}"
# Do not inherit stale AMP_ONLY from parent shells.
unset AMP_ONLY || true
REPORT="$ROOT/PILOT_SPAN100_REPORT.md"

echo "=== Pilot span100 ==="
if [[ "${SKIP_COLD_RESET:-0}" != "1" ]]; then
  "$ROOT/scripts/reset_asymrm_cold.sh" $PILOT_EXPS
fi

env -u AMP_ONLY "$ROOT/scripts/run_asymrm.sh" || rc=$?
rc=${rc:-0}

for exp in $PILOT_EXPS; do
  python3 "$ROOT/scripts/audit_l_oscillation.py" \
    "$ROOT/$exp/Train" \
    --stat-dir "$(ls -d "$ROOT/$exp/Train/StatisticLog/"* 2>/dev/null | tail -1)" \
    --report "$ROOT/SPAN100_DEND0_AUDIT_${exp#EXP_}.md" 2>/dev/null || true
done

{
  echo "# Pilot span100 Report"
  echo ""
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  echo "## Feasibility"
  python3 "$ROOT/scripts/check_timing_feasibility.py" --post \
    $(for e in $PILOT_EXPS; do echo "$ROOT/$e/Train/Parameters_00.xml"; done) 2>/dev/null || true
  echo ""
  echo "## Stall"
  python3 "$ROOT/scripts/analyze_train_stall.py" \
    $(for e in $PILOT_EXPS; do echo "$ROOT/$e/Train"; done) 2>/dev/null || true
} >"$REPORT"

exit "$rc"

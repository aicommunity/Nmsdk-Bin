#!/usr/bin/env bash
# Pilot span100 — separate protocol with length guard (no blind 5120 steps).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PILOT_EXPS="${PILOT_SPAN100_EXPS:-EXP_span100ms_packA_preinh}"
export ADAPTIVE_TRAIN=1
export LENGTH_STEPS_SPAN100="${LENGTH_STEPS_SPAN100:-80 160 320 640 1280 2560}"
export LENGTH_MAX_STEP="${LENGTH_MAX_STEP:-2560}"
export WALL_BUDGET_CHECK=1
REPORT="$ROOT/PILOT_SPAN100_REPORT.md"

echo "=== Pilot span100 ==="
if [[ "${SKIP_COLD_RESET:-0}" != "1" ]]; then
  "$ROOT/scripts/reset_asymrm_cold.sh" $PILOT_EXPS
fi

"$ROOT/scripts/run_asymrm.sh" || rc=$?
rc=${rc:-0}

python3 "$ROOT/scripts/audit_l_oscillation.py" \
  "$ROOT/EXP_span100ms_packA_preinh/Train" \
  --stat-dir "$(ls -d "$ROOT/EXP_span100ms_packA_preinh/Train/StatisticLog/"* 2>/dev/null | tail -1)" \
  --report "$ROOT/SPAN100_DEND0_AUDIT.md" 2>/dev/null || true

{
  echo "# Pilot span100 Report"
  echo ""
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  python3 "$ROOT/scripts/check_timing_feasibility.py" --post \
    "$ROOT/EXP_span100ms_packA_preinh/Train/Parameters_00.xml" 2>/dev/null || true
} >"$REPORT"

exit "$rc"

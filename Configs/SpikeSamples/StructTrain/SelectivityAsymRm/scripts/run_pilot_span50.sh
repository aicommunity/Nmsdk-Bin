#!/usr/bin/env bash
# Pilot span50 Pack A (gen + preinh) — universality check after span25 fix.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PILOT_EXPS="${PILOT_SPAN50_EXPS:-EXP_span50ms_packA_gen EXP_span50ms_packA_preinh}"
export L_REFERENCE="${L_REFERENCE:-ltzcal}"
export ADAPTIVE_TRAIN=1
export WALL_BUDGET_CHECK="${WALL_BUDGET_CHECK:-1}"
REPORT="$ROOT/PILOT_SPAN50_REPORT.md"

echo "=== Pilot span50 Pack A ==="
if [[ "${SKIP_COLD_RESET:-0}" != "1" ]]; then
  "$ROOT/scripts/reset_asymrm_cold.sh" $PILOT_EXPS
fi

"$ROOT/scripts/run_asymrm.sh" || rc=$?
rc=${rc:-0}

{
  echo "# Pilot span50 Report"
  echo ""
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  for exp in $PILOT_EXPS; do
    echo "## $exp"
    python3 "$ROOT/scripts/check_timing_feasibility.py" --post \
      "$ROOT/$exp/Train/Parameters_00.xml" 2>/dev/null || true
    python3 "$ROOT/scripts/analyze_signal_fidelity.py" "$ROOT/$exp/Train" 2>/dev/null | \
      python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"sync_ok={d.get('all_non_ref_sync_ok')} need_train={d.get('IsNeedToTrain')}\")" 2>/dev/null || true
    echo ""
  done
} >"$REPORT"

exit "$rc"

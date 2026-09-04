#!/usr/bin/env bash
# Phase 7: evaluate span25 gate and optionally scale Pack B/C.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERIFY_DONE="$(cd "$(dirname "$0")/../../SelectivityLtzCalibrate/scripts" && pwd)/verify_train_done.py"
REPORT="$ROOT/PILOT_REPORT.md"
GATE_EXPS=(EXP_span25ms_packA_gen EXP_span25ms_packA_preinh)
DONE=0

for exp in "${GATE_EXPS[@]}"; do
  flags=()
  [[ -f "$ROOT/l_reference.json" ]] && flags+=(--L-reference "$ROOT/l_reference.json")
  if python3 "$VERIFY_DONE" --require-calibrated --require-sync-ok "${flags[@]}" \
      "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
    echo "GATE OK $exp"
    DONE=$((DONE + 1))
  else
    echo "GATE FAIL $exp"
    python3 "$ROOT/scripts/check_timing_feasibility.py" --post \
      "$ROOT/$exp/Train/Parameters_00.xml" 2>/dev/null || true
  fi
done

{
  echo ""
  echo "## Pilot v4 gate ($(date -u +%Y-%m-%d))"
  echo ""
  echo "- span25 Done: $DONE / ${#GATE_EXPS[@]}"
  if (( DONE >= 2 )); then
    echo "- Action: scale Pack B/C span25"
  else
    echo "- Action: investigate blockers (see logs)"
  fi
} >>"$REPORT"

if (( DONE >= 2 )); then
  echo "=== Gate passed (train Done $DONE/${#GATE_EXPS[@]}) ==="
  # Default: do not auto-scale (protects Done weights / concurrent pilots).
  if [[ "${SKIP_SCALE:-1}" == "1" ]]; then
    echo "SKIP_SCALE=1 — not launching scale_asymrm.sh (set SKIP_SCALE=0 to scale)"
  else
    PACK_A_EXPS="" PILOT_EXPS="EXP_span25ms_packA_gen EXP_span25ms_packA_preinh" \
      SKIP_SWEEP=1 "$ROOT/scripts/scale_asymrm.sh" 2>&1 || true
  fi
fi

exit $(( DONE >= 2 ? 0 : 1 ))

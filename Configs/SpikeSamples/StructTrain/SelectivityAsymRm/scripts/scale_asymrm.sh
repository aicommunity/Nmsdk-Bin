#!/usr/bin/env bash
# Phase 4: scale Pack A remaining + B/C grid (gate: >=2/3 pilot Done).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/scripts/run_asymrm.sh"
SWEEP="$ROOT/scripts/sweep_asymrm_amp.sh"
VERIFY="$ROOT/../../SelectivityLtzCalibrate/scripts/verify_train_done.py"
PILOT_EXPS="${PILOT_EXPS:-EXP_span25ms_packA_gen EXP_span25ms_packA_preinh EXP_span100ms_packA_preinh}"
GATE_MIN="${GATE_MIN:-2}"
L_REF="$ROOT/l_reference.json"

count_pilot_done() {
  local n=0
  for exp in $PILOT_EXPS; do
    if python3 "$VERIFY" --require-sync-ok \
        ${L_REF:+--L-reference "$L_REF"} \
        "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
      n=$((n + 1))
    fi
  done
  echo "$n"
}

done_count=$(count_pilot_done)
total_pilot=$(echo "$PILOT_EXPS" | wc -w)
echo "Pilot Done: $done_count / $total_pilot (gate >= $GATE_MIN)"

if (( done_count < GATE_MIN )); then
  echo "Gate not met — skipping scale. See SCALE_DEFERRED.md"
  exit 2
fi

echo "=== Phase 4.1: amp sweep on pilot ==="
GTS="${GTS:-20000}" PILOT_EXPS="$PILOT_EXPS" bash "$SWEEP"

echo "=== Phase 4.2: Pack A remaining 3 EXP ==="
PACK_A_EXPS=1 GTS="${GTS:-20000}" L_REFERENCE=ltzcal ADAPTIVE_TRAIN=1 bash "$RUN"

pack_a_done=0
for exp in EXP_span25ms_packA_gen EXP_span25ms_packA_preinh EXP_span50ms_packA_gen \
           EXP_span50ms_packA_preinh EXP_span100ms_packA_gen EXP_span100ms_packA_preinh; do
  if python3 "$VERIFY" --require-sync-ok "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
    pack_a_done=$((pack_a_done + 1))
  fi
done
echo "Pack A Done: $pack_a_done / 6"

if (( pack_a_done >= 4 )); then
  echo "=== Phase 4.3: Pack B/C (12 EXP) ==="
  GTS="${GTS:-20000}" L_REFERENCE=ltzcal ADAPTIVE_TRAIN=1 MAX_JOBS=3 bash "$RUN"
else
  echo "Pack A gate <4/6 — skip B/C"
fi

echo "=== Phase 4.4: grid summary written to $ROOT/grid_summary.csv ==="
cat "$ROOT/grid_summary.csv" 2>/dev/null || true

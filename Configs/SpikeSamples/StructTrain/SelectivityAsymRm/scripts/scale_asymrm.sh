#!/usr/bin/env bash
# Phase 4: scale Pack A remaining (span50 only) + B/C waves by span.
# Pack A span100 is a separate protocol: scripts/run_pilot_span100.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/scripts/run_asymrm.sh"
SWEEP="$ROOT/scripts/sweep_asymrm_amp.sh"
VERIFY="$ROOT/../SelectivityLtzCalibrate/scripts/verify_train_done.py"
# Default gate: span25 Pack A only (span100 is separate protocol).
PILOT_EXPS="${PILOT_EXPS:-EXP_span25ms_packA_gen EXP_span25ms_packA_preinh}"
GATE_MIN="${GATE_MIN:-2}"
L_REF="$ROOT/l_reference.json"
SKIP_SWEEP="${SKIP_SWEEP:-1}"
MAX_JOBS="${MAX_JOBS:-6}"
SCALE_SPAN25_BC="${SCALE_SPAN25_BC:-1}"
SCALE_SPAN50_BC="${SCALE_SPAN50_BC:-1}"
SCALE_SPAN100_BC="${SCALE_SPAN100_BC:-0}"
FORCE_SPAN100_BC="${FORCE_SPAN100_BC:-0}"

count_done() {
  local n=0
  for exp in "$@"; do
    if python3 "$VERIFY" --require-sync-ok \
        ${L_REF:+--L-reference "$L_REF"} \
        "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
      n=$((n + 1))
    fi
  done
  echo "$n"
}

done_count=$(count_done $PILOT_EXPS)
total_pilot=$(echo "$PILOT_EXPS" | wc -w)
echo "Pilot Done: $done_count / $total_pilot (gate >= $GATE_MIN)"

if (( done_count < GATE_MIN )); then
  echo "Gate not met — skipping scale. See SCALE_DEFERRED.md"
  exit 2
fi

echo "=== Phase 4.1: amp sweep on pilot ==="
if [[ "$SKIP_SWEEP" == "1" ]]; then
  echo "SKIP_SWEEP=1 — preserve Done pilot weights; skip destructive cold-reset sweep"
else
  GTS="${GTS:-20000}" PILOT_EXPS="$PILOT_EXPS" bash "$SWEEP"
fi

echo "=== Phase 4.2: Pack A span50 remaining (skip Done; span100 NOT here) ==="
PACK_A_TODO=()
for exp in EXP_span50ms_packA_gen EXP_span50ms_packA_preinh; do
  if python3 "$VERIFY" --require-sync-ok \
      ${L_REF:+--L-reference "$L_REF"} \
      "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
    echo "skip Done $exp"
  else
    PACK_A_TODO+=("$exp")
  fi
done
if ((${#PACK_A_TODO[@]})); then
  PACK_A_EXPS="" PILOT_EXPS="${PACK_A_TODO[*]}" GTS="${GTS:-20000}" \
    L_REFERENCE=ltzcal SEED_INITIAL=1 ADAPTIVE_TRAIN=1 MAX_JOBS="$MAX_JOBS" \
    SIGNAL_REF_JSON="$ROOT/signal_reference_span50.json" bash "$RUN" || true
else
  echo "Pack A span50 already Done — skip"
fi
echo "NOTE: Pack A span100 → bash scripts/run_pilot_span100.sh (separate protocol)"

pack_a_done=0
pack_a_span25_done=0
pack_a_span100_done=0
for exp in EXP_span25ms_packA_gen EXP_span25ms_packA_preinh; do
  if python3 "$VERIFY" --require-sync-ok \
      ${L_REF:+--L-reference "$L_REF"} \
      "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
    pack_a_done=$((pack_a_done + 1))
    pack_a_span25_done=$((pack_a_span25_done + 1))
  fi
done
for exp in EXP_span50ms_packA_gen EXP_span50ms_packA_preinh; do
  if python3 "$VERIFY" --require-sync-ok \
      ${L_REF:+--L-reference "$L_REF"} \
      "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
    pack_a_done=$((pack_a_done + 1))
  fi
done
for exp in EXP_span100ms_packA_gen EXP_span100ms_packA_preinh; do
  if python3 "$VERIFY" --require-sync-ok \
      ${L_REF:+--L-reference "$L_REF"} \
      "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
    pack_a_done=$((pack_a_done + 1))
    pack_a_span100_done=$((pack_a_span100_done + 1))
  fi
done
echo "Pack A Done: $pack_a_done / 6 (span25=$pack_a_span25_done/2 span100=$pack_a_span100_done/2)"

run_bc_wave() {
  local label="$1"
  shift
  local -a exps=("$@")
  echo "=== $label ==="
  PILOT_EXPS="${exps[*]}" GTS="${GTS:-20000}" \
    L_REFERENCE=ltzcal SEED_INITIAL=1 ADAPTIVE_TRAIN=1 MAX_JOBS="$MAX_JOBS" \
    bash "$RUN" || true
}

if [[ "$SCALE_SPAN25_BC" == "1" ]] && (( pack_a_done >= 4 || pack_a_span25_done >= 2 )); then
  SIGNAL_REF_JSON="$ROOT/signal_reference_span25.json" \
  LENGTH_STEPS_SPAN25="${LENGTH_STEPS_SPAN25:-80 160 320 640 1280 2560}" \
  run_bc_wave "Phase 4.3a: Pack B/C span25" \
    EXP_span25ms_packB_gen EXP_span25ms_packB_preinh \
    EXP_span25ms_packC_gen EXP_span25ms_packC_preinh
else
  echo "Phase 4.3a skipped (SCALE_SPAN25_BC=$SCALE_SPAN25_BC gate pack_a=$pack_a_done span25=$pack_a_span25_done)"
fi

if [[ "$SCALE_SPAN50_BC" == "1" ]] && (( pack_a_done >= 4 )); then
  SIGNAL_REF_JSON="$ROOT/signal_reference_span50.json" \
  LENGTH_STEPS_SPAN50="${LENGTH_STEPS_SPAN50:-80 160 320 640 1280 2560}" \
  run_bc_wave "Phase 4.3b: Pack B/C span50" \
    EXP_span50ms_packB_gen EXP_span50ms_packB_preinh \
    EXP_span50ms_packC_gen EXP_span50ms_packC_preinh
else
  echo "Phase 4.3b skipped (SCALE_SPAN50_BC=$SCALE_SPAN50_BC)"
fi

if [[ "$SCALE_SPAN100_BC" == "1" || "$FORCE_SPAN100_BC" == "1" ]]; then
  if (( pack_a_span100_done >= 2 )) || [[ "$FORCE_SPAN100_BC" == "1" ]]; then
    LENGTH_STEPS_SPAN100="${LENGTH_STEPS_SPAN100:-80 160 320 640 1280 2560}" \
    LENGTH_MAX_STEP="${LENGTH_MAX_STEP:-2560}" \
    WALL_BUDGET_CHECK=1 SKIP_COLD_RESET=1 \
    run_bc_wave "Phase 4.3c: Pack B/C span100" \
      EXP_span100ms_packB_gen EXP_span100ms_packB_preinh \
      EXP_span100ms_packC_gen EXP_span100ms_packC_preinh
  else
    echo "Phase 4.3c skipped — Pack A span100 not Done ($pack_a_span100_done/2); use FORCE_SPAN100_BC=1 to override"
  fi
else
  echo "Phase 4.3c skipped (SCALE_SPAN100_BC=0; enable after Pack A span100 Done)"
fi

echo "=== Phase 4.4: grid summary written to $ROOT/grid_summary.csv ==="
cat "$ROOT/grid_summary.csv" 2>/dev/null || true

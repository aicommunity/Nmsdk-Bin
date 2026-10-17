#!/usr/bin/env bash
# Chain pilot v4: gen → preinh → span50 → gate (run after gen or standalone).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
export SEED_INITIAL="${SEED_INITIAL:-1}"
export INITIAL_SOURCE="${INITIAL_SOURCE:-ltzcal}"
VERIFY_DONE="$(cd "$(dirname "$0")/../../SelectivityLtzCalibrate/scripts" && pwd)/verify_train_done.py"
SEED="$ROOT/scripts/seed_initial_from_ltzcal.py"

wait_log() {
  local log="$1" pattern="$2" max_min="${3:-180}"
  local i=0
  while (( i < max_min * 6 )); do
    if grep -qE "$pattern" "$log" 2>/dev/null; then
      return 0
    fi
    if pgrep -f 'EXP_span25ms_packA_gen/Train.*NeuroModelerConsole' >/dev/null 2>&1; then
      sleep 10
      i=$((i + 1))
      continue
    fi
    if ! pgrep -f 'run_pilot_v4_gen|run_asymrm.sh.*PILOT_EXPS=EXP_span25ms_packA_gen' >/dev/null 2>&1; then
      return 0
    fi
    sleep 10
    i=$((i + 1))
  done
  return 1
}

gen_done() {
  python3 "$VERIFY_DONE" --require-calibrated --require-sync-ok \
    ${L_REF_JSON:+"--L-reference" "$ROOT/l_reference.json"} \
    "$ROOT/EXP_span25ms_packA_gen/Train/Parameters_00.xml" >/dev/null 2>&1
}

seed_if_needed() {
  local exp="$1"
  if python3 "$SEED" --check-ready "$ROOT/$exp/Train" 2>/dev/null; then
    echo "Initial ready $exp"
    return 0
  fi
  echo "=== seed Initial $exp ==="
  python3 "$SEED" "$ROOT/$exp/Train"
}

if [[ "${SKIP_GEN:-0}" != "1" ]]; then
  echo "=== Waiting for pilot_v4_gen (amp/Done) ==="
  wait_log "$ROOT/pilot_v4_gen.log" 'DONE EXP_span25ms_packA_gen|TRAIN_NOT_DONE|=== TEST wave ===' 360 || true
  sleep 5
  if ! gen_done; then
    seed_if_needed EXP_span25ms_packA_gen
    echo "=== AMP_ONLY gen (not Done yet) ==="
    PILOT_EXPS=EXP_span25ms_packA_gen AMP_ONLY=1 L_REFERENCE=ltzcal SEED_INITIAL=1 \
      bash "$ROOT/scripts/run_asymrm.sh" 2>&1 | tee -a "$ROOT/pilot_v4_gen.log" || true
  fi
fi

if [[ "${SKIP_PREINH:-0}" != "1" ]]; then
  seed_if_needed EXP_span25ms_packA_preinh || true
  echo "=== Phase 4b preinh ==="
  "$ROOT/scripts/run_pilot_v4_preinh.sh" 2>&1 | tee "$ROOT/pilot_v4_preinh.log"
fi

if [[ "${SKIP_SPAN50:-0}" != "1" ]]; then
  echo "=== Phase 5 span50 ==="
  "$ROOT/scripts/run_pilot_span50.sh" 2>&1 | tee "$ROOT/pilot_span50.log"
fi

echo "=== Phase 7 gate ==="
"$ROOT/scripts/run_gate_scale.sh" 2>&1 | tee -a "$ROOT/pilot_gate.log"

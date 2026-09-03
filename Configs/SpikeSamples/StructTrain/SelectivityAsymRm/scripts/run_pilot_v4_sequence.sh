#!/usr/bin/env bash
# Chain pilot v4: gen → preinh → span50 → gate (run after gen or standalone).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"

wait_log() {
  local log="$1" pattern="$2" max_min="${3:-180}"
  local i=0
  while (( i < max_min * 6 )); do
    if grep -qE "$pattern" "$log" 2>/dev/null; then
      return 0
    fi
    # Gen pilot still training if NeuroModeler in gen/preinh train dirs
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

if [[ "${SKIP_GEN:-0}" != "1" ]]; then
  echo "=== Waiting for pilot_v4_gen (amp/Done) ==="
  wait_log "$ROOT/pilot_v4_gen.log" 'DONE EXP_span25ms_packA_gen|=== TEST wave ===' 360 || true
  sleep 5
fi

if [[ "${SKIP_PREINH:-0}" != "1" ]]; then
  echo "=== Phase 4b preinh ==="
  "$ROOT/scripts/run_pilot_v4_preinh.sh" 2>&1 | tee "$ROOT/pilot_v4_preinh.log"
fi

if [[ "${SKIP_SPAN50:-0}" != "1" ]]; then
  echo "=== Phase 5 span50 ==="
  "$ROOT/scripts/run_pilot_span50.sh" 2>&1 | tee "$ROOT/pilot_span50.log"
fi

echo "=== Phase 7 gate ==="
"$ROOT/scripts/run_gate_scale.sh" 2>&1 | tee -a "$ROOT/pilot_gate.log"

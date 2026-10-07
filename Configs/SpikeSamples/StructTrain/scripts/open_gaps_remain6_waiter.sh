#!/usr/bin/env bash
# Wait for fs50_preinh (+ ltz25 already done), then PARALLEL=6 for remain6.
# Assumes old xargs may be SIGSTOP'd; does not kill active fs50_preinh.
set -euo pipefail
ROOT=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
RCS_D=$ROOT/_repro/OPEN_GAPS_W0_rcs.d
REMAIN=$ROOT/_repro/OPEN_GAPS_W0_remain6_manifest.txt
LOG=/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/OPEN_GAPS_W0.log
WAITLOG=/tmp/open_gaps_remain6_waiter.log
REMAIN_CASES=(br25_preinh br480_tiprmin asym50 ltz50_gen psi01_050 br25_on)

echo "waiter2 start $(date -u -Iseconds)" | tee "$WAITLOG"

is_verify_pid() {
  local p=$1 c=$2
  local args
  args=$(ps -p "$p" -o args= 2>/dev/null || true)
  # Exact verify cmdline; ignore waiter/scripts that merely mention the string
  [[ "$args" == *"scripts/posttune_verify.py --case ${c} "* ]] || [[ "$args" == *"scripts/posttune_verify.py --case ${c}" ]]
}

kill_verify_case() {
  local c=$1 p
  for p in $(pgrep -f "scripts/posttune_verify.py --case ${c}" || true); do
    if is_verify_pid "$p" "$c"; then
      echo "KILL premature verify $c pid=$p" | tee -a "$WAITLOG"
      pkill -P "$p" 2>/dev/null || true
      kill "$p" 2>/dev/null || true
    fi
  done
}

while true; do
  have25=0
  have50=0
  [[ -f "$RCS_D/ltz25_gen.rc" ]] && have25=1
  [[ -f "$RCS_D/fs50_preinh.rc" ]] && have50=1
  grep -q "CASE ltz25_gen END" "$LOG" 2>/dev/null && have25=1 || true
  grep -q "CASE fs50_preinh END" "$LOG" 2>/dev/null && have50=1 || true

  # Only kill real premature verifies (xargs should be STOP'd)
  for c in "${REMAIN_CASES[@]}"; do
    kill_verify_case "$c"
  done

  echo "wait tick have25=$have25 have50=$have50 $(date -u -Iseconds)" >>"$WAITLOG"
  if [[ "$have25" -eq 1 && "$have50" -eq 1 ]]; then
    echo "both done $(date -u -Iseconds)" | tee -a "$WAITLOG"
    break
  fi
  sleep 20
done

# Clear any bogus remain6 shards
for c in "${REMAIN_CASES[@]}"; do
  rm -f "$RCS_D/${c}.rc"
done

# Stop old orchestrator (CONT then TERM if STOP'd)
for p in $(pgrep -f 'scripts/open_gaps_w0_diag.sh' || true); do
  kill -CONT "$p" 2>/dev/null || true
  kill "$p" 2>/dev/null || true
done
for p in $(pgrep -f 'xargs -P 2 -I\{\} bash -c cd "\$ROOT" && run_one' || true); do
  kill -CONT "$p" 2>/dev/null || true
  kill "$p" 2>/dev/null || true
done
sleep 2
for c in "${REMAIN_CASES[@]}"; do
  kill_verify_case "$c"
  rm -f "$RCS_D/${c}.rc"
done

echo "launch PARALLEL=6 remain6 $(date -u -Iseconds)" | tee -a "$WAITLOG"
cd "$ROOT"
export PARALLEL=6
export MANIFEST="$REMAIN"
export LOG=/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/OPEN_GAPS_W0_remain6.log
export RCS=$ROOT/_repro/OPEN_GAPS_W0_remain6_rcs.txt
# Note: open_gaps_w0_diag.sh hardcodes RCS_DIR to OPEN_GAPS_W0_rcs.d — OK
nohup bash scripts/open_gaps_w0_diag.sh >>/tmp/open_gaps_remain6_nohup.out 2>&1 &
echo "remain6_pid=$!" | tee -a "$WAITLOG"

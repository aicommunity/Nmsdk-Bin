#!/usr/bin/env bash
set -uo pipefail
ROOT=/home/user/Nmsdk
cd "$ROOT"
LOGDIR="$ROOT/Bin/Configs/SpikeSamples/StructTrain/_repro"
UTC=$(date -u +%Y%m%dT%H%M%SZ)
BATCH_LOG="$LOGDIR/T2_control_batch_${UTC}.log"
RCS="$LOGDIR/T2_case_rcs_${UTC}.txt"
echo "T2 start $UTC" | tee "$BATCH_LOG"
echo "console=$(sha256sum Bin/Platform/Linux/NeuroModelerConsole | awk '{print $1}')" | tee -a "$BATCH_LOG"
run_case() {
  local name="$1"; shift
  local label="$1"; shift
  echo "=== CASE $label ($name) START $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$BATCH_LOG"
  set +e
  python3 -B Bin/Configs/SpikeSamples/StructTrain/scripts/posttune_verify.py --case "$name" "$@" 2>&1 | tee -a "$BATCH_LOG"
  local rc=${PIPESTATUS[0]}
  set -e
  echo "$label $name rc=$rc" | tee -a "$RCS" | tee -a "$BATCH_LOG"
  echo "=== CASE $label END rc=$rc $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$BATCH_LOG"
  return 0
}
# 1) Branch25 gold / skip soft_cold train
run_case br25_on gold_skip_train --skip-train
# 2) Branch25 soft_cold
run_case br25_on soft_cold
# 3+4) Asym50 clean workdir isolates stale archive flag; full cold train
run_case asym50 asym50_cold
echo "T2 batch done $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$BATCH_LOG"

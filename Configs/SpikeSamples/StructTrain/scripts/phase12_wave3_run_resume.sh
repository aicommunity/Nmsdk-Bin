#!/usr/bin/env bash
set -uo pipefail
ROOT=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
LOG=$ROOT/_repro/phase12_w3b_asym2.log
LOCK=$ROOT/_repro/phase12_w3b.lock
export PYTHONUNBUFFERED=1
cd "$ROOT"
exec 9>"$LOCK"
flock -n 9 || { echo "lock held"; exit 1; }
{
  echo "=== START asym resume $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  python3 -u scripts/phase12_validate.py run-asym-packa-all --from EXP_span25ms_packA_preinh --force-prepare
  echo ASYM_PACKA_RC=$?
  python3 -u scripts/phase12_validate.py run-asym-clones
  echo ASYM_CLONES_RC=$?
  echo "=== DONE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
} >>"$LOG" 2>&1

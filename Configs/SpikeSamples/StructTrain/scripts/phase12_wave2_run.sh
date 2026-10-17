#!/usr/bin/env bash
# PHASE12 Wave2: B/C matrix-only clones then br480 soft-cold.
set -euo pipefail
ROOT=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
LOG=$ROOT/_repro/phase12_wave2_run.log
mkdir -p "$ROOT/_repro"
exec >>"$LOG" 2>&1
echo "=== START wave2 $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
cd "$ROOT"

python3 scripts/phase12_validate.py list-wave2

echo "===== run-clones-wave2 ====="
python3 scripts/phase12_validate.py run-clones-wave2

echo "===== run-br480-all ====="
python3 scripts/phase12_validate.py run-br480-all --force-prepare

echo "=== ALL DONE wave2 $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

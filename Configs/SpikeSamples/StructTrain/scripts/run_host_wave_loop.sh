#!/usr/bin/env bash
# Sequential wave train loop (one host). Always --no-commit; commits via watch on local.
# Usage:
#   HOST_ROLE=local  bash run_host_wave_loop.sh
#   HOST_ROLE=17     bash run_host_wave_loop.sh
# Env: JOBS (default 8), WAVES="W03 W05 ..." (optional override)
set -euo pipefail

ROOT=/home/user/Nmsdk
ST="$ROOT/Bin/Configs/SpikeSamples/StructTrain"
RUNS="$ST/_repro/TimeLearnerMatrixRuns"
QUEUE="$ST/scripts/run_timelearner_matrix_queue.py"
ROLE="${HOST_ROLE:-local}"
JOBS="${JOBS:-8}"
PREFIX="run-${ROLE}"
[[ "$ROLE" == "17" ]] && PREFIX="run-17"
LOG="$ROOT/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/host_wave_loop_${ROLE}.log"
mkdir -p "$(dirname "$LOG")" "$RUNS"
exec > >(tee -a "$LOG") 2>&1

log() { echo "[$(date -u +%H:%M:%SZ)] [$ROLE] $*"; }

WAVES_17=(W06 W07 W46 W47 W10 W12 W13 W15 W17 W19 W45 W21 W23 W25 W26 W28 W30 W32 W34 W35 W36 W38 W40 W41 W42 W43 W44)
WAVES_LOCAL=(W03 W05 W08 W09 W11 W14 W16 W18 W20 W22 W24 W27 W29 W31 W33 W37 W39)

if [[ -n "${WAVES:-}" ]]; then
  # shellcheck disable=SC2206
  LIST=($WAVES)
elif [[ "$ROLE" == "17" ]]; then
  LIST=("${WAVES_17[@]}")
else
  LIST=("${WAVES_LOCAL[@]}")
fi

wave_done() {
  local w=$1
  local f="$ST/TimeLearnerMatrix/$w/results.json"
  [[ -f "$f" ]] || return 1
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('run_complete') and d.get('cases') else 1)" "$f"
}

# Drop staged junk; leave untracked alone
git -C "$ROOT" diff --cached --quiet || git -C "$ROOT" reset HEAD
git -C "$ROOT/Bin" diff --cached --quiet || git -C "$ROOT/Bin" reset HEAD

log "start jobs=$JOBS waves=${#LIST[@]}: ${LIST[*]}"

for wave in "${LIST[@]}"; do
  if wave_done "$wave"; then
    log "SKIP $wave (results.json already complete)"
    continue
  fi

  # Free disk hint
  avail_g=$(df -BG --output=avail "$ROOT" | tail -1 | tr -dc '0-9')
  if [[ -n "$avail_g" && "$avail_g" -lt 40 ]]; then
    log "STOP: free disk ${avail_g}G < 40G"
    exit 2
  fi

  run_id="${PREFIX}-$(date -u +%Y%m%dT%H%M%SZ)-$$"
  mkdir -p "$RUNS/$run_id"
  log "START $wave RUN_ID=$run_id"

  # Reset prepare dirt from prior waves (inputs only)
  git -C "$ROOT/Bin" checkout -- Configs/SpikeSamples/StructTrain/TimeLearnerMatrix 2>/dev/null || true
  git -C "$ROOT" diff --cached --quiet || git -C "$ROOT" reset HEAD
  git -C "$ROOT/Bin" diff --cached --quiet || git -C "$ROOT/Bin" reset HEAD

  set +e
  (
    cd "$ST"
    export PYTHONUNBUFFERED=1 TIMELEARNER_MATRIX_RUN_ID=$run_id
    python3 -u "$QUEUE" --run-id "$run_id" --waves "$wave" --jobs "$JOBS" --no-commit \
      > "$RUNS/$run_id/queue.log" 2>&1
    rc=$?
    printf '%s\n' "$rc" > "$RUNS/$run_id/queue.exit"
    exit "$rc"
  )
  rc=$?
  set -e

  status=""
  if [[ -f "$RUNS/$run_id/queue_status.json" ]]; then
    status=$(python3 -c "import json;print(json.load(open('$RUNS/$run_id/queue_status.json')).get('status',''))")
  fi
  log "DONE $wave rc=$rc status=$status RUN_ID=$run_id"

  if [[ $rc -eq 2 || "$status" == *infrastructure* || "$status" == *incomplete* ]]; then
    log "INFRA fail on $wave — stop loop (resume after fix)"
    exit 2
  fi
  # rc 0/1 (train/eval issues): continue to next wave; commit-watch handles git
  log "CONTINUE to next wave"
done

log "ALL WAVES IN LIST FINISHED for role=$ROLE"
exit 0

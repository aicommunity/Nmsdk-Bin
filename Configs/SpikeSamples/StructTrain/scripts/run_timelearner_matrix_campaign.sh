#!/usr/bin/env bash
# Dual-host full-matrix campaign: train all assigned waves; analyze later.
# Continues after training_stop / eval_error. Stops only on incomplete/infra.
set -euo pipefail

ROOT=/home/user/Nmsdk
ST="$ROOT/Bin/Configs/SpikeSamples/StructTrain"
RUNS="${TIMELEARNER_MATRIX_RUNS_ROOT:-$ST/_repro/TimeLearnerMatrixRuns}"
REMOTE_RUNS="${TIMELEARNER_MATRIX_REMOTE_RUNS_ROOT:-/media/user/Data/NmsdkRuntime/TimeLearnerMatrixRuns}"
LOCK="$ST/_repro/.matrix_commit.lock"
UPDATER="$ST/scripts/update_timelearner_matrix_report.py"
QUEUE="$ST/scripts/run_timelearner_matrix_queue.py"
SSH_HOST="${TIMELEARNER_MATRIX_SSH:-user@10.245.1.17}"
STATE="$ROOT/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/matrix_campaign_state.json"
LOG="$ROOT/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/matrix_campaign.log"
JOBS="${JOBS:-8}"

# Keep large run data on the chosen data disk rather than the checkout partition.
if [[ ! "$REMOTE_RUNS" =~ ^/[A-Za-z0-9._/-]+$ ]]; then
  echo "TIMELEARNER_MATRIX_REMOTE_RUNS_ROOT must be an absolute path without shell metacharacters" >&2
  exit 2
fi
if [[ "$REMOTE_RUNS" != /media/user/Data/* || "$REMOTE_RUNS" == *"/../"* || "$REMOTE_RUNS" == */.. ]]; then
  echo "TIMELEARNER_MATRIX_REMOTE_RUNS_ROOT must stay under /media/user/Data" >&2
  exit 2
fi
if [[ "$RUNS" != /* ]]; then
  echo "TIMELEARNER_MATRIX_RUNS_ROOT must be absolute" >&2
  exit 2
fi
export TIMELEARNER_MATRIX_RUNS_ROOT="$RUNS"

WAVES_17=(W04 W06 W07 W46 W47 W10 W12 W13 W15 W17 W19 W45 W21 W23 W25 W26 W28 W30 W32 W34 W35 W36 W38 W40 W41 W42 W43 W44)
WAVES_LOCAL=(W02 W03 W05 W08 W09 W11 W14 W16 W18 W20 W22 W24 W27 W29 W31 W33 W37 W39)

mkdir -p "$(dirname "$STATE")" "$RUNS"
exec > >(tee -a "$LOG") 2>&1

log() { echo "[$(date -u +%H:%M:%SZ)] $*"; }

ssh17() {
  if [[ -n "${SSHPASS:-}" ]]; then
    sshpass -e ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 "$SSH_HOST" "$@"
  else
    ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 "$SSH_HOST" "$@"
  fi
}

rsync_from_17() {
  local src=$1 dst=$2
  if [[ -n "${SSHPASS:-}" ]]; then
    sshpass -e rsync -a -e "ssh -o StrictHostKeyChecking=accept-new" "$src" "$dst"
  else
    rsync -a "$src" "$dst"
  fi
}

wave_done() {
  local w=$1
  (cd "$ST" && python3 "$QUEUE" --check-completed "$w" >/dev/null 2>&1)
}

acquire_lock() {
  mkdir -p "$(dirname "$LOCK")"
  local i=0
  while ! mkdir "$LOCK" 2>/dev/null; do
    i=$((i+1))
    if (( i > 1440 )); then log "LOCK timeout"; exit 2; fi
    sleep 5
  done
  echo "pid=$$ utc=$(date -u +%Y%m%dT%H%M%SZ)" > "$LOCK/owner"
}

release_lock() { rm -rf "$LOCK"; }

push_repos() {
  git -C "$ROOT/Bin" push origin HEAD || true
  git -C "$ROOT" push origin HEAD || true
}

save_state() {
  python3 - <<PY
import json
from datetime import datetime, timezone
json.dump({
  "updated_utc": datetime.now(timezone.utc).isoformat(),
  "ri": $ri, "li": $li,
  "remote_wave": $( [[ -n "${remote_wave:-}" ]] && echo "\"$remote_wave\"" || echo null ),
  "remote_run": $( [[ -n "${remote_run:-}" ]] && echo "\"$remote_run\"" || echo null ),
  "note": """$1""",
}, open("$STATE","w"), indent=2)
print(file=open("$STATE","a"))
PY
}

ingest_17() {
  local wave=$1 run_id=$2
  log "INGEST $wave $run_id"
  if [[ -e "$RUNS/$run_id" ]]; then
    log "REFUSE ingest: local RUN_ID already exists; preserving both copies"
    return 2
  fi
  mkdir "$RUNS/$run_id"
  rsync_from_17 "$SSH_HOST:$REMOTE_RUNS/$run_id/" "$RUNS/$run_id/"
  commit_wave_from_run "$wave" "$run_id" " (host=17)"
  log "Raw run retained on .17 at $REMOTE_RUNS/$run_id"
  log "INGEST done $wave"
}

start_remote_wave() {
  local wave=$1
  remote_run="run-17-$(date -u +%Y%m%dT%H%M%SZ)-$$-$RANDOM"
  remote_wave=$wave
  log "START remote $wave RUN_ID=$remote_run"
  ssh17 "set -e
mountpoint -q /media/user/Data
resolved_runs=\$(realpath -m -- '$REMOTE_RUNS')
case \"\$resolved_runs\" in /media/user/Data/*) ;; *) echo 'remote run root resolves outside Data mount' >&2; exit 2;; esac
mkdir -p '$REMOTE_RUNS'
cd $ST
test ! -e '$REMOTE_RUNS/$remote_run'
nohup bash -c '
  export PYTHONUNBUFFERED=1 TIMELEARNER_MATRIX_RUN_ID=$remote_run TIMELEARNER_MATRIX_RUNS_ROOT=$REMOTE_RUNS
  cd $ST
  python3 -u scripts/run_timelearner_matrix_queue.py --run-id $remote_run --waves $wave --jobs $JOBS --no-commit
  rc=\$?
  printf \"%s\\n\" \"\$rc\" > $REMOTE_RUNS/$remote_run.launch.exit
  printf \"%s\\n\" \"\$rc\" > $REMOTE_RUNS/$remote_run/queue.exit
' > '$REMOTE_RUNS/$remote_run.launch.log' 2>&1 &
echo \$! > '$REMOTE_RUNS/$remote_run.launch.pid'
"
}

remote_finished() {
  [[ -n "${remote_run:-}" ]] || return 1
  ssh17 "test -f '$REMOTE_RUNS/$remote_run.launch.exit'" >/dev/null 2>&1
}

commit_wave_from_run() {
  local wave=$1 run_id=$2 host_tag=$3
  acquire_lock
  export TIMELEARNER_MATRIX_RUN_ID=$run_id
  export TIMELEARNER_MATRIX_RUNS_ROOT="$RUNS"
  (
    cd "$ST"
    python3 "$UPDATER" "$wave"
  )
  (
    cd "$ROOT/Bin"
    git add -- Configs/SpikeSamples/StructTrain/EXPERIMENTS.md \
      Configs/SpikeSamples/StructTrain/SUCCESSFUL_EXPERIMENTS.md \
      "Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/$wave/results.json"
    git add -- Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/"$wave"/run_results/"$run_id"-*.json
    if ! git diff --cached --quiet; then
      git commit -m "research(TimeLearner): record $wave results${host_tag}"
    fi
  )
  (
    cd "$ROOT"
    git add -- Bin \
      Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/TIMELEARNER_MATRIX_WAVES_20261010.md \
      Docs/Audit/TimeLearner-2026-09-26-review/plans/TimeLearner-full-matrix-waves-20261010.ru.md \
      Docs/Audit/TimeLearner-2026-09-26-review/TIMELEARNER_FULL_MATRIX_AND_HISTORY_2026-10-10.ru.md
    if ! git diff --cached --quiet; then
      git commit -m "research(TimeLearner): pin $wave report${host_tag}"
    fi
  )
  release_lock
  push_repos
}

run_local_wave() {
  local wave=$1
  local run_id="run-local-$(date -u +%Y%m%dT%H%M%SZ)-$$-$RANDOM"
  log "START local $wave RUN_ID=$run_id"
  # --no-commit avoids ensure_wave_paths_clean failing on dirty Bin gitlink (untracked clutter).
  set +e
  (
    cd "$ST"
    export PYTHONUNBUFFERED=1 TIMELEARNER_MATRIX_RUN_ID=$run_id TIMELEARNER_MATRIX_RUNS_ROOT="$RUNS"
    python3 -u "$QUEUE" --run-id "$run_id" --waves "$wave" --jobs "$JOBS" --no-commit \
      > "$RUNS/$run_id.launch.log" 2>&1
    rc=$?
    if [[ -d "$RUNS/$run_id" ]]; then
      printf '%s\n' "$rc" > "$RUNS/$run_id/queue.exit"
      mv -n "$RUNS/$run_id.launch.log" "$RUNS/$run_id/queue.log"
    fi
    exit "$rc"
  )
  local rc=$?
  set -e
  if [[ $rc -eq 2 ]]; then
    log "INFRA FAIL local $wave rc=2"
    return 2
  fi
  # Train finished (0=clean, 1=train/eval issues) → updater+commit, then continue
  if [[ ! -f "$RUNS/$run_id/queue_status.json" ]]; then
    log "MISSING queue_status for $wave — treat as infra fail"
    return 2
  fi
  local status
  status=$(python3 -c "import json;print(json.load(open('$RUNS/$run_id/queue_status.json')).get('status',''))")
  if [[ "$status" == *infrastructure* || "$status" == *incomplete* ]]; then
    log "INFRA status local $wave: $status"
    return 2
  fi
  commit_wave_from_run "$wave" "$run_id" " (host=local)"
  log "LOCAL DONE $wave rc=$rc status=$status — continue"
  return 0
}

# filter already done / resume active remote from state
ri=0; li=0
remote_wave=""; remote_run=""
if [[ -f "$STATE" ]]; then
  eval "$(python3 - <<'PY'
import json
from pathlib import Path
p=Path("/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/matrix_campaign_state.json")
d=json.loads(p.read_text())
rw=d.get("remote_wave") or ""
rr=d.get("remote_run") or ""
print(f'remote_wave={rw!r}')
print(f'remote_run={rr!r}')
print(f'ri={int(d.get("ri") or 0)}')
print(f'li={int(d.get("li") or 0)}')
PY
)"
fi
log "Campaign start: continue-through-failures; analyze after full matrix"
log "W01 already recorded; remaining .17=${#WAVES_17[@]} local=${#WAVES_LOCAL[@]}"
if [[ -n "${remote_run:-}" ]]; then
  if remote_finished; then
    log "Resume: remote $remote_wave $remote_run already finished — will ingest"
  elif ssh17 "test -d '$REMOTE_RUNS/$remote_run'"; then
    log "Resume: attach to in-flight remote $remote_wave $remote_run"
  else
    log "Resume: stale remote_run $remote_run missing — clear"
    remote_wave=""; remote_run=""
  fi
fi

while (( ri < ${#WAVES_17[@]} || li < ${#WAVES_LOCAL[@]} )); do
  # skip completed
  while (( ri < ${#WAVES_17[@]} )) && wave_done "${WAVES_17[$ri]}"; do
    log "SKIP .17-list ${WAVES_17[$ri]} (results present)"; ri=$((ri+1))
  done
  while (( li < ${#WAVES_LOCAL[@]} )) && wave_done "${WAVES_LOCAL[$li]}"; do
    log "SKIP local-list ${WAVES_LOCAL[$li]} (results present)"; li=$((li+1))
  done
  (( ri < ${#WAVES_17[@]} || li < ${#WAVES_LOCAL[@]} )) || break

  if [[ -z "${remote_run:-}" ]] && (( ri < ${#WAVES_17[@]} )); then
    start_remote_wave "${WAVES_17[$ri]}"
    save_state "remote_started"
  fi

  if (( li < ${#WAVES_LOCAL[@]} )); then
    if ! run_local_wave "${WAVES_LOCAL[$li]}"; then
      save_state "local_infra_fail"; exit 2
    fi
    li=$((li+1))
    save_state "local_done"
  fi

  if [[ -n "${remote_run:-}" ]]; then
    log "WAIT remote $remote_wave $remote_run"
    while ! remote_finished; do
      # if local still has waves, keep training locally while waiting
      if (( li < ${#WAVES_LOCAL[@]} )); then
        if ! wave_done "${WAVES_LOCAL[$li]}"; then
          if ! run_local_wave "${WAVES_LOCAL[$li]}"; then
            save_state "local_infra_fail"; exit 2
          fi
        fi
        li=$((li+1))
        save_state "local_done_while_wait"
      else
        sleep 60
      fi
    done
    ssh17 "if [ -d '$REMOTE_RUNS/$remote_run' ]; then mv -n '$REMOTE_RUNS/$remote_run.launch.log' '$REMOTE_RUNS/$remote_run/queue.log'; fi" || true
    rc_remote=$(ssh17 "cat '$REMOTE_RUNS/$remote_run/queue.exit'")
    status=$(ssh17 "python3 -c \"import json;print(json.load(open('$REMOTE_RUNS/$remote_run/queue_status.json')).get('status',''))\"" || true)
    log "REMOTE EXIT $remote_wave rc=$rc_remote status=$status"
    if [[ -z "$status" || "$status" == *infrastructure* || "$status" == *incomplete* ]]; then
      log "INFRA on remote — stop"; save_state "remote_infra_fail"; exit 2
    fi
    ingest_17 "$remote_wave" "$remote_run"
    remote_wave=""; remote_run=""
    ri=$((ri+1))
    save_state "remote_ingested"
  fi
done

log "CAMPAIGN COMPLETE — all listed waves finished; run analyze-full-matrix next"
save_state "campaign_complete"
exit 0

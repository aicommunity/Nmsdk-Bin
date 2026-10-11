#!/usr/bin/env bash
# Periodic wave commits (separate from train): poll finished RUN_IDs and commit on local.
# - Local: _repro/TimeLearnerMatrixRuns/run-local-*/queue.exit → commit
# - .17:   ssh queue.exit → rsync → commit --host-tag host=17
#
# State: Docs/.../evidence/metrics/matrix_commit_watch_state.json
set -euo pipefail

ROOT=/home/user/Nmsdk
ST="$ROOT/Bin/Configs/SpikeSamples/StructTrain"
RUNS="$ST/_repro/TimeLearnerMatrixRuns"
COMMIT_PY="$ST/scripts/commit_timelearner_matrix_wave.py"
SSH_HOST="${TIMELEARNER_MATRIX_SSH:-user@10.245.1.17}"
STATE="$ROOT/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/matrix_commit_watch_state.json"
LOG="$ROOT/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/matrix_commit_watch.log"
ARCHIVE_17=/media/user/Data/NmsdkStructTrainArchive/matrix_runs
POLL_S="${POLL_S:-60}"

mkdir -p "$(dirname "$STATE")" "$RUNS"
touch "$STATE"
exec > >(tee -a "$LOG") 2>&1

log() { echo "[$(date -u +%H:%M:%SZ)] $*"; }

ssh17() {
  if [[ -n "${SSHPASS:-}" ]]; then
    sshpass -e ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 "$SSH_HOST" "$@"
  else
    ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 "$SSH_HOST" "$@"
  fi
}

already_committed() {
  local run_id=$1
  python3 - <<PY
import json
from pathlib import Path
p=Path("$STATE")
d=json.loads(p.read_text()) if p.exists() and p.stat().st_size else {"committed":[]}
print("yes" if "$run_id" in d.get("committed",[]) else "no")
PY
}

mark_committed() {
  local run_id=$1 wave=$2
  python3 - <<PY
import json
from pathlib import Path
from datetime import datetime, timezone
p=Path("$STATE")
d=json.loads(p.read_text()) if p.exists() and p.stat().st_size else {"committed":[]}
d.setdefault("committed", [])
if "$run_id" not in d["committed"]:
    d["committed"].append("$run_id")
d["last"]={"run_id":"$run_id","wave":"$wave","utc":datetime.now(timezone.utc).isoformat()}
p.write_text(json.dumps(d, indent=2)+"\n")
PY
}

wave_from_run() {
  local run_dir=$1
  # first Wxx subdirectory
  basename "$(find "$run_dir" -maxdepth 1 -type d -name 'W[0-9][0-9]' | head -1)"
}

commit_local_run() {
  local run_id=$1
  local run_dir="$RUNS/$run_id"
  [[ -f "$run_dir/queue.exit" ]] || return 0
  already_committed "$run_id" | grep -q yes && return 0
  local wave
  wave=$(wave_from_run "$run_dir")
  [[ -n "$wave" && "$wave" != "." ]] || { log "skip $run_id: no wave dir"; return 0; }
  # skip if results already committed for this wave with same run_id
  if [[ -f "$ST/TimeLearnerMatrix/$wave/results.json" ]]; then
    if python3 -c "import json;print(json.load(open('$ST/TimeLearnerMatrix/$wave/results.json')).get('run_id',''))" | grep -qx "$run_id"; then
      log "already in results.json $wave $run_id"; mark_committed "$run_id" "$wave"; return 0
    fi
  fi
  log "COMMIT local $wave $run_id"
  python3 "$COMMIT_PY" "$wave" --run-id "$run_id" --host-tag host=local --push
  mark_committed "$run_id" "$wave"
}

commit_remote_run() {
  local run_id=$1 wave=$2
  already_committed "$run_id" | grep -q yes && return 0
  if [[ -f "$ST/TimeLearnerMatrix/$wave/results.json" ]]; then
    if python3 -c "import json;print(json.load(open('$ST/TimeLearnerMatrix/$wave/results.json')).get('run_id',''))" | grep -qx "$run_id"; then
      log "already in results.json $wave $run_id"; mark_committed "$run_id" "$wave"; return 0
    fi
  fi
  log "COMMIT .17 $wave $run_id"
  python3 "$COMMIT_PY" "$wave" --run-id "$run_id" --host-tag host=17 --rsync-from-17 --push
  ssh17 "mkdir -p $ARCHIVE_17 && rsync -a $ST/_repro/TimeLearnerMatrixRuns/$run_id/ $ARCHIVE_17/$run_id/ && rm -rf $ST/_repro/TimeLearnerMatrixRuns/$run_id" || true
  mark_committed "$run_id" "$wave"
}

log "commit-watch start poll=${POLL_S}s (train separate; commits on local only)"

while true; do
  # local finished runs
  for d in "$RUNS"/run-local-*; do
    [[ -d "$d" ]] || continue
    commit_local_run "$(basename "$d")" || log "WARN local commit failed for $d"
  done

  # remote finished runs (list dirs with queue.exit)
  mapfile -t remote_done < <(ssh17 "ls -1 $ST/_repro/TimeLearnerMatrixRuns 2>/dev/null" || true)
  for run_id in "${remote_done[@]:-}"; do
    [[ "$run_id" == run-17-* ]] || continue
    if ssh17 "test -f $ST/_repro/TimeLearnerMatrixRuns/$run_id/queue.exit"; then
      wave=$(ssh17 "basename \$(ls -d $ST/_repro/TimeLearnerMatrixRuns/$run_id/W[0-9][0-9] 2>/dev/null | head -1)")
      [[ -n "$wave" && "$wave" == W* ]] || continue
      commit_remote_run "$run_id" "$wave" || log "WARN remote commit failed $run_id"
    fi
  done

  sleep "$POLL_S"
done

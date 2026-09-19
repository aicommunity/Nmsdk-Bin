#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain
BIN=/home/user/Nmsdk/Bin
LOG="$ROOT/_repro/_invest/run_invest.log"
mkdir -p "$ROOT/_repro/_invest"
exec > >(tee -a "$LOG") 2>&1

commit_job() {
  local id="$1" msg="$2"
  cd "$BIN"
  git add Configs/SpikeSamples/StructTrain/_repro/_invest/COMPARE.md \
          Configs/SpikeSamples/StructTrain/_repro/REPRO_COLD_INVESTIGATION.md 2>/dev/null || true
  shopt -s nullglob
  local csvs=(Configs/SpikeSamples/StructTrain/_repro/_invest/*/Test/SelectivityLog/results*.csv)
  if ((${#csvs[@]})); then git add -f "${csvs[@]}"; fi
  if git diff --cached --quiet; then
    echo "COMMIT skip $id (nothing staged)"; return 0
  fi
  git commit -m "$(cat <<EOM
repro: cold invest ${msg}

EOM
)"
  echo "COMMIT ok $id"
}

for JOB in A1 A2 B1 B2; do
  echo "======== START $JOB $(date -u +%Y-%m-%dT%H:%M:%SZ) ========"
  # isolate log per job status via temp
  STATUS_FILE="$ROOT/_repro/_invest/.last_status"
  rm -f "$STATUS_FILE"
  set +e
  python3 -u "$ROOT/scripts/repro_cold_harness.py" invest --job "$JOB" --force 2>&1 | tee /tmp/invest_$JOB.out
  rc=${PIPESTATUS[0]}
  set -e
  status=$(grep -E '^TRAIN_STATUS=' /tmp/invest_$JOB.out | tail -1 | cut -d= -f2 || true)
  echo "job=$JOB rc=$rc TRAIN_STATUS=$status"
  if [[ "$status" != "done" && "$status" != "dry" ]]; then
    echo "ABORT: train not done for $JOB — still commit COMPARE if present"
    # still try append happened inside harness; commit incomplete
  fi
  case "$JOB" in
    A1) commit_job A1 "C2.A1 fs soft." ;;
    A2) commit_job A2 "C2.A2 fs strip." ;;
    B1) commit_job B1 "C2.B1 branch soft." ;;
    B2) commit_job B2 "C2.B2 branch strip." ;;
  esac
  echo "======== DONE $JOB $(date -u +%Y-%m-%dT%H:%M:%SZ) ========"
done
echo "ALL INVEST DONE"

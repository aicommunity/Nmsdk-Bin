#!/usr/bin/env bash
# Sequential invest A1→A2→B1→B2 with Bin commits C2.* after each job.
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
  # force-add CSVs if present
  shopt -s nullglob
  local csvs=(Configs/SpikeSamples/StructTrain/_repro/_invest/*/Test/SelectivityLog/results*.csv)
  if ((${#csvs[@]})); then
    git add -f "${csvs[@]}"
  fi
  if git diff --cached --quiet; then
    echo "COMMIT skip $id (nothing staged)"
    return 0
  fi
  git commit -m "$(cat <<EOF
repro: cold invest ${msg}

EOF
)"
  echo "COMMIT ok $id"
}

for JOB in A1 A2 B1 B2; do
  echo "======== START $JOB $(date -u +%Y-%m-%dT%H:%M:%SZ) ========"
  python3 -u "$ROOT/scripts/repro_cold_harness.py" invest --job "$JOB" --force
  case "$JOB" in
    A1) commit_job A1 "C2.A1 fs soft." ;;
    A2) commit_job A2 "C2.A2 fs strip." ;;
    B1) commit_job B1 "C2.B1 branch soft." ;;
    B2) commit_job B2 "C2.B2 branch strip." ;;
  esac
  echo "======== DONE $JOB $(date -u +%Y-%m-%dT%H:%M:%SZ) ========"
done
echo "ALL INVEST DONE"

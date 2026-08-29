#!/usr/bin/env bash
# Run NeuroModelerConsole on many cell dirs with bounded parallelism.
# Usage: run_parallel.sh <cells_parent|list_file> [SIM_T]
# Env: MAX_JOBS=4..6  NM=path  CELLS_GLOB="cells/*/project.ini"
set -euo pipefail
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
MAX_JOBS="${MAX_JOBS:-4}"
SIM_T="${2:-3}"
TARGET="${1:?cells dir or file with project.ini paths}"

if (( MAX_JOBS > 6 )); then MAX_JOBS=6; fi
if (( MAX_JOBS < 1 )); then MAX_JOBS=1; fi

mapfile -t JOBS < <(
  if [[ -f "$TARGET" ]]; then
    grep -v '^#' "$TARGET" | grep -v '^$' || true
  else
    find "$TARGET" -name 'project.ini' -o -name 'Project.ini' | sort
  fi
)

echo "nproc=$(nproc) load=$(cut -d' ' -f1-3 /proc/loadavg) MAX_JOBS=$MAX_JOBS cells=${#JOBS[@]} SIM_T=$SIM_T"

running=0
fail=0
pids=()
dirs=()

wait_one() {
  local pid="${pids[0]}"
  local d="${dirs[0]}"
  pids=("${pids[@]:1}")
  dirs=("${dirs[@]:1}")
  if wait "$pid"; then
    echo "OK  $d"
  else
    echo "FAIL $d (exit $?)"
    fail=$((fail + 1))
  fi
  running=$((running - 1))
}

for ini in "${JOBS[@]}"; do
  [[ -z "$ini" ]] && continue
  cell="$(dirname "$ini")"
  while (( running >= MAX_JOBS )); do
    wait_one
  done
  echo "START $cell"
  (
    cd "$cell"
    "$NM" -c "$(basename "$ini")" -s -t "$SIM_T" -x >"run_console.log" 2>&1
  ) &
  pids+=($!)
  dirs+=("$cell")
  running=$((running + 1))
done

while (( running > 0 )); do
  wait_one
done

echo "Done. failures=$fail"
exit "$fail"

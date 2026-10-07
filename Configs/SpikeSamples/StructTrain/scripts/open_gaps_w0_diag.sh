#!/usr/bin/env bash
# Open Gaps W0 diagnostic SoftCold subset — keep-slog, skip registry.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="${MANIFEST:-$ROOT/_repro/OPEN_GAPS_W0_manifest.txt}"
LOG="${LOG:-/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics/OPEN_GAPS_W0.log}"
RCS="${RCS:-$ROOT/_repro/OPEN_GAPS_W0_rcs.txt}"
RCS_DIR="$ROOT/_repro/OPEN_GAPS_W0_rcs.d"
PARALLEL="${PARALLEL:-2}"
AUTOSAVE_S="${AUTOSAVE_S:-10}"
SNAP_EVERY="${SNAP_EVERY:-20}"
STALL_N="${STALL_N:-8}"
mkdir -p "$RCS_DIR"
: >"$LOG"
mapfile -t cases < <(grep -vE '^\s*(#|$)' "$MANIFEST")
echo "Open Gaps W0 diag start $(date -u -Iseconds) PARALLEL=$PARALLEL n=${#cases[@]}" | tee -a "$LOG"
run_one() {
  local case="$1" rc utc
  echo "==== CASE $case START $(date -u -Iseconds) ====" | tee -a "$LOG"
  set +e
  PYTHONUNBUFFERED=1 python3 -u scripts/posttune_verify.py \
    --case "$case" \
    --autosave-model-s "$AUTOSAVE_S" \
    --snap-every "$SNAP_EVERY" \
    --stall-autosave-n "$STALL_N" \
    --keep-slog \
    --no-result-md >>"$LOG" 2>&1
  rc=$?
  set -e
  utc="$(date -u -Iseconds)"
  printf '%s %s %s\n' "$case" "$rc" "$utc" >"$RCS_DIR/${case}.rc"
  echo "==== CASE $case END rc=$rc $utc ====" | tee -a "$LOG"
}
export -f run_one
export ROOT LOG RCS_DIR AUTOSAVE_S SNAP_EVERY STALL_N
cd "$ROOT"
printf '%s\n' "${cases[@]}" | xargs -P "$PARALLEL" -I{} bash -c 'cd "$ROOT" && run_one "$@"' _ {}
: >"$RCS"
for case in "${cases[@]}"; do
  if [[ -f "$RCS_DIR/${case}.rc" ]]; then
    cat "$RCS_DIR/${case}.rc" >>"$RCS"
  else
    echo "MISSING $case" | tee -a "$LOG"
  fi
done
echo "SKIP_REGISTRY_APPLY=1 — no EXPERIMENTS apply" | tee -a "$LOG"
echo "Open Gaps W0 diag done $(date -u -Iseconds) RCS=$RCS LOG=$LOG" | tee -a "$LOG"

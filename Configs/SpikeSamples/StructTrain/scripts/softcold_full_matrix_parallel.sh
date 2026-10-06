#!/usr/bin/env bash
# SoftCold full-matrix with N concurrent posttune_verify workers.
# Per-case atomic RCS under _repro/rcs.d/; single serial registry apply at end.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
METRICS_ROOT="${METRICS_ROOT:-/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics}"
mkdir -p "$METRICS_ROOT" "$ROOT/_repro"
LOG="${LOG:-$METRICS_ROOT/SOFTCOLD_full_matrix_parallel.log}"
RCS="${RCS:-$ROOT/_repro/SOFTCOLD_HEAD_rcs.txt}"
MANIFEST="${MANIFEST:-$ROOT/_repro/SOFTCOLD_QUEUE_manifest.txt}"
RCS_DIR="${RCS_DIR:-$ROOT/_repro/rcs.d}"
LOCK="${LOCK:-$ROOT/_repro/registry_apply.lock}"
AUTOSAVE_S="${AUTOSAVE_MODEL_S:-10}"
SNAP_EVERY="${SNAP_EVERY:-20}"
PARALLEL="${PARALLEL:-6}"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"

mkdir -p "$RCS_DIR"
# Fresh shard dir for this matrix
rm -f "$RCS_DIR"/*.rc "$RCS_DIR"/*.rc.tmp 2>/dev/null || true

mapfile -t cases < <(grep -v '^[[:space:]]*$' "$MANIFEST" | grep -v '^#')
queue_n=${#cases[@]}

avail_gib=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
need_gib=$((80 + 10 * PARALLEL))
if [[ -n "$avail_gib" && "$avail_gib" -lt "$need_gib" ]]; then
  echo "WARN: free ${avail_gib}GiB < recommended ${need_gib}GiB; clamping PARALLEL" | tee -a "$LOG"
  while [[ "$PARALLEL" -gt 1 && "$avail_gib" -lt $((80 + 10 * PARALLEL)) ]]; do
    PARALLEL=$((PARALLEL - 1))
  done
fi

{
  echo "SoftCold full matrix PARALLEL start $(date -u -Iseconds)"
  echo "SHA=$(sha256sum "$NM")"
  echo "autosave_model_s=$AUTOSAVE_S snap_every=$SNAP_EVERY PARALLEL=$PARALLEL queue_n=$queue_n avail_gib=${avail_gib:-?}"
} | tee -a "$LOG"

run_one() {
  local case="$1"
  local tmp rc utc
  echo "==== CASE $case START $(date -u -Iseconds) ====" | tee -a "$LOG"
  set +e
  PYTHONUNBUFFERED=1 python3 -u scripts/posttune_verify.py \
    --case "$case" \
    --autosave-model-s "$AUTOSAVE_S" \
    --snap-every "$SNAP_EVERY" \
    --no-result-md >>"$LOG" 2>&1
  rc=$?
  set -e
  utc="$(date -u -Iseconds)"
  tmp="$RCS_DIR/${case}.rc.tmp"
  printf '%s %s %s\n' "$case" "$rc" "$utc" >"$tmp"
  mv -f "$tmp" "$RCS_DIR/${case}.rc"
  echo "==== CASE $case END rc=$rc $utc ====" | tee -a "$LOG"
  if [[ "$rc" -eq 0 ]]; then
    echo "$case -> SoftCold PASS (case=$case)" | tee -a "$LOG"
  else
    echo "$case -> SoftCold FAIL (case=$case, rc=$rc)" | tee -a "$LOG"
  fi
}
export -f run_one
export ROOT LOG RCS_DIR AUTOSAVE_S SNAP_EVERY
export PATH

# GNU parallel via xargs -P (one case per worker)
printf '%s\n' "${cases[@]}" | xargs -P "$PARALLEL" -I{} bash -c 'cd "$ROOT" && run_one "$@"' _ {}

# Merge RCS in manifest order
: >"$RCS"
missing=0
for case in "${cases[@]}"; do
  if [[ ! -f "$RCS_DIR/${case}.rc" ]]; then
    echo "MISSING RCS shard: $case" | tee -a "$LOG"
    missing=1
    continue
  fi
  cat "$RCS_DIR/${case}.rc" >>"$RCS"
done
nlines=$(grep -cve '^[[:space:]]*$' "$RCS" || true)
echo "RCS merged lines=$nlines expected=$queue_n missing=$missing" | tee -a "$LOG"
if [[ "$missing" -ne 0 || "$nlines" -ne "$queue_n" ]]; then
  echo "ERROR: RCS incomplete" | tee -a "$LOG"
  exit 2
fi

# apply_softcold_rcs_to_registry.py already fcntl-locks $LOCK — do not wrap with
# flock(1) on the same path (nested LOCK_EX on a second fd deadlocks for hours).
# Selective / dry runs: SKIP_REGISTRY_APPLY=1 (no EXPERIMENTS.md mutate).
if [[ "${SKIP_REGISTRY_APPLY:-0}" == "1" ]]; then
  echo "SKIP_REGISTRY_APPLY=1 — RCS merge only, no EXPERIMENTS.md apply" | tee -a "$LOG"
else
  python3 -u scripts/apply_softcold_rcs_to_registry.py --rcs "$RCS" | tee -a "$LOG" || true
fi
echo "SoftCold full matrix PARALLEL done $(date -u -Iseconds)" | tee -a "$LOG"
echo "LOG=$LOG RCS=$RCS PARALLEL=$PARALLEL"

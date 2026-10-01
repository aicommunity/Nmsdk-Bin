#!/usr/bin/env bash
# SoftCold full-matrix queue: all CASES from SOFTCOLD_QUEUE_manifest.txt
# with model-time autosave + snap. Updates RCS after each case.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
METRICS_ROOT="${METRICS_ROOT:-/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-26-review/evidence/metrics}"
mkdir -p "$METRICS_ROOT" "$ROOT/_repro"
LOG="${LOG:-$METRICS_ROOT/SOFTCOLD_full_matrix.log}"
RCS="${RCS:-$ROOT/_repro/SOFTCOLD_HEAD_rcs.txt}"
MANIFEST="${MANIFEST:-$ROOT/_repro/SOFTCOLD_QUEUE_manifest.txt}"
AUTOSAVE_S="${AUTOSAVE_MODEL_S:-10}"
SNAP_EVERY="${SNAP_EVERY:-20}"
TICK_NOTE="${AGENT_LOOP_TICK:-600}"  # seconds between AGENT_LOOP_TICK lines

: >"$RCS"
{
  echo "SoftCold full matrix start $(date -u -Iseconds)"
  echo "SHA=$(sha256sum /home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole)"
  echo "autosave_model_s=$AUTOSAVE_S snap_every=$SNAP_EVERY"
  mapfile -t cases < <(grep -v '^[[:space:]]*$' "$MANIFEST" | grep -v '^#')
  echo "queue_n=${#cases[@]}"
  i=0
  for case in "${cases[@]}"; do
    i=$((i + 1))
    echo "==== CASE $case ($i/${#cases[@]}) START $(date -u -Iseconds) ===="
    echo "AGENT_LOOP_TICK case=$case i=$i/${#cases[@]} at $(date -u -Iseconds) (tick=${TICK_NOTE}s)"
    set +e
    python3 scripts/posttune_verify.py \
      --case "$case" \
      --autosave-model-s "$AUTOSAVE_S" \
      --snap-every "$SNAP_EVERY"
    rc=$?
    set -e
    echo "==== CASE $case END rc=$rc $(date -u -Iseconds) ===="
    echo "$case $rc $(date -u -Iseconds)" >>"$RCS"
    python3 scripts/apply_softcold_rcs_to_registry.py --rcs <(echo "$case $rc") || true
  done
  echo "SoftCold full matrix done $(date -u -Iseconds)"
  python3 scripts/apply_softcold_rcs_to_registry.py --rcs "$RCS" || true
} 2>&1 | tee -a "$LOG"
echo "LOG=$LOG RCS=$RCS"

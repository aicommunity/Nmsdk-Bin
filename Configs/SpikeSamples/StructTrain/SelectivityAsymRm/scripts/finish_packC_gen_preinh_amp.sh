#!/usr/bin/env bash
# Pack C gen amp via Done Pack C preinh TipR+Initial; hard isolation from 16 Done EXP.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/finish_packC_gen_preinh_amp.log"
SEED="$ROOT/scripts/seed_from_done_preinh.py"
FINGER="$ROOT/scripts/done_fingerprint.py"
VERIFY="$ROOT/../SelectivityLtzCalibrate/scripts/verify_train_done.py"

ALLOWED=(EXP_span50ms_packC_gen EXP_span100ms_packC_gen)
PILOT_LIST="${PILOT_EXPS:-EXP_span50ms_packC_gen EXP_span100ms_packC_gen}"

refuse_bad_pilot() {
  local e
  if [[ -z "${PILOT_LIST// }" ]]; then
    echo "Refuse empty PILOT_EXPS" >&2
    exit 1
  fi
  for e in $PILOT_LIST; do
    local ok=0 a
    for a in "${ALLOWED[@]}"; do
      [[ "$e" == "$a" ]] && ok=1
    done
    if [[ "$ok" -ne 1 ]]; then
      echo "Refuse non-whitelist PILOT exp: $e (allowed: ${ALLOWED[*]})" >&2
      exit 1
    fi
  done
}

prune_keep_newest() {
  local exp="$1"
  local base="$ROOT/$exp/Train/StatisticLog"
  [[ -d "$base" ]] || return 0
  local newest
  newest=$(ls -td "$base"/*/ 2>/dev/null | head -1 || true)
  [[ -n "$newest" ]] || return 0
  local d
  for d in "$base"/*/; do
    [[ -d "$d" ]] || continue
    if [[ "$(realpath "$d")" != "$(realpath "$newest")" ]]; then
      echo "prune $d"
      rm -rf "$d"
    fi
  done
  echo "KEEP $newest"
}

BACKUP_DIR="$ROOT/.preinh_amp_report_backup"
backup_reports() {
  mkdir -p "$BACKUP_DIR"
  local f
  for f in PEAK_SYNC_REPORT.md peak_sync_latest.json stall_latest.csv stall_latest.json \
           feasibility_latest.csv grid_summary.csv; do
    if [[ -f "$ROOT/$f" ]]; then
      cp -a "$ROOT/$f" "$BACKUP_DIR/$f"
      echo "backup $f"
    fi
  done
}

restore_reports() {
  local f
  for f in PEAK_SYNC_REPORT.md peak_sync_latest.json stall_latest.csv stall_latest.json \
           feasibility_latest.csv grid_summary.csv; do
    if [[ -f "$BACKUP_DIR/$f" ]]; then
      cp -a "$BACKUP_DIR/$f" "$ROOT/$f"
      echo "restore $f"
    fi
  done
  # Prefer full-grid regenerate when possible
  if ls -d "$ROOT"/EXP_*/Train >/dev/null 2>&1; then
    python3 "$ROOT/scripts/analyze_peak_sync.py" \
      $(ls -d "$ROOT"/EXP_*/Train) \
      -o "$ROOT/peak_sync_latest.json" --md "$ROOT/PEAK_SYNC_REPORT.md" 2>/dev/null \
      && echo "regenerated peak_sync full grid" || echo "peak_sync regen skipped"
    python3 "$ROOT/scripts/analyze_train_stall.py" \
      $(ls -d "$ROOT"/EXP_*/Train) \
      -o "$ROOT/stall_latest.csv" 2>/dev/null \
      && echo "regenerated stall_latest full grid" || echo "stall regen skipped"
  fi
}

exec > >(tee -a "$LOG") 2>&1
echo "=== finish_packC_gen_preinh_amp $(date -Iseconds) ==="
refuse_bad_pilot
echo "PILOT_EXPS=$PILOT_LIST"

PRE_FP="$ROOT/done_fingerprint_pre_preinh_amp.json"
POST_FP="$ROOT/done_fingerprint_post_preinh_amp.json"

echo "=== preflight Done fingerprint ==="
python3 "$FINGER" --write "$PRE_FP"

backup_reports

for exp in $PILOT_LIST; do
  prune_keep_newest "$exp"
done

echo "=== seed TipR+Initial from Pack C preinh + surgical ==="
# shellcheck disable=SC2086
python3 "$SEED" --surgical $(for e in $PILOT_LIST; do echo "$ROOT/$e/Train"; done)

export PILOT_EXPS="$PILOT_LIST"
export ADAPTIVE_TRAIN=1
export MAX_JOBS="${MAX_JOBS:-2}"
export L_REFERENCE=ltzcal
export AMP_ONLY=1
export AMP_SKIP_REFRESH=1
export AMP_FORCE_AT_L_REF=1
export AMP_PARTIAL_AT_L_REF=1
export AMP_TRAIN_STEPS="${AMP_TRAIN_STEPS:-80 160 320}"
export AMP_ABORT_HARD_OSC=1
export AMP_HARD_OSC_NO_IMPROVE="${AMP_HARD_OSC_NO_IMPROVE:-20}"
export SEED_INITIAL=1
export ALLOW_PARTIAL_TRAIN=1

echo "=== AMP_ONLY steps=$AMP_TRAIN_STEPS SKIP_REFRESH=1 ABORT_HARD_OSC=1 ==="
set +e
bash "$ROOT/scripts/run_asymrm.sh"
rc=$?
set -e

echo "=== verify pilot gen ==="
fail=0
for e in $PILOT_LIST; do
  if python3 "$VERIFY" --require-calibrated --require-sync-ok \
      --L-reference "$ROOT/l_reference.json" \
      "$ROOT/$e/Train/Parameters_00.xml"; then
    echo "PASS $e"
  else
    echo "FAIL $e"
    fail=1
  fi
done

# One renudge if still failing and hard OSC present
if [[ "$fail" -ne 0 ]]; then
  echo "=== re-nudge preinh TipR+surgical + AMP_TRAIN_STEPS=80 160 ==="
  # shellcheck disable=SC2086
  python3 "$SEED" --surgical $(for e in $PILOT_LIST; do echo "$ROOT/$e/Train"; done)
  for exp in $PILOT_LIST; do prune_keep_newest "$exp"; done
  export AMP_TRAIN_STEPS="80 160"
  set +e
  bash "$ROOT/scripts/run_asymrm.sh"
  set -e
  fail=0
  for e in $PILOT_LIST; do
    if python3 "$VERIFY" --require-calibrated --require-sync-ok \
        --L-reference "$ROOT/l_reference.json" \
        "$ROOT/$e/Train/Parameters_00.xml"; then
      echo "PASS $e (after renudge)"
    else
      echo "FAIL $e (after renudge)"
      fail=1
    fi
  done
fi

echo "=== postflight Done fingerprint ==="
python3 "$FINGER" --write "$POST_FP"
if ! python3 "$FINGER" --diff "$PRE_FP"; then
  echo "FATAL: Done EXP regression detected" >&2
  restore_reports
  exit 2
fi

restore_reports

echo "=== finish_packC_gen_preinh_amp done rc=$rc fail=$fail $(date -Iseconds) ==="
exit "$fail"

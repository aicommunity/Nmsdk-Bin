#!/usr/bin/env bash
# Pack C gen: reset pathological TipR (H1) then short amp. Whitelist + Done fingerprint.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/finish_packC_gen_tip_reset_amp.log"
RESET="$ROOT/scripts/reset_pathological_tip.py"
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

BACKUP_DIR="$ROOT/.tip_reset_amp_report_backup"
backup_reports() {
  mkdir -p "$BACKUP_DIR"
  local f
  for f in PEAK_SYNC_REPORT.md peak_sync_latest.json stall_latest.csv stall_latest.json \
           feasibility_latest.csv grid_summary.csv SELECTIVITY_REPORT.md; do
    if [[ -f "$ROOT/$f" ]]; then
      cp -a "$ROOT/$f" "$BACKUP_DIR/$f"
      echo "backup $f"
    fi
  done
}

restore_reports() {
  local f
  for f in PEAK_SYNC_REPORT.md peak_sync_latest.json stall_latest.csv stall_latest.json \
           feasibility_latest.csv grid_summary.csv SELECTIVITY_REPORT.md; do
    if [[ -f "$BACKUP_DIR/$f" ]]; then
      cp -a "$BACKUP_DIR/$f" "$ROOT/$f"
      echo "restore $f"
    fi
  done
  if ls -d "$ROOT"/EXP_*/Train >/dev/null 2>&1; then
    python3 "$ROOT/scripts/analyze_peak_sync.py" \
      $(ls -d "$ROOT"/EXP_*/Train) \
      -o "$ROOT/peak_sync_latest.json" --md "$ROOT/PEAK_SYNC_REPORT.md" 2>/dev/null \
      && echo "regenerated peak_sync full grid" || true
    python3 "$ROOT/scripts/analyze_train_stall.py" \
      $(ls -d "$ROOT"/EXP_*/Train) \
      -o "$ROOT/stall_latest.csv" 2>/dev/null \
      && echo "regenerated stall_latest full grid" || true
  fi
}

exec > >(tee -a "$LOG") 2>&1
echo "=== finish_packC_gen_tip_reset_amp $(date -Iseconds) ==="
refuse_bad_pilot
echo "PILOT_EXPS=$PILOT_LIST"

PRE_FP="$ROOT/done_fingerprint_pre_tip_reset_amp.json"
POST_FP="$ROOT/done_fingerprint_post_tip_reset_amp.json"
python3 "$FINGER" --write "$PRE_FP"
backup_reports

echo "=== reset pathological TipR ==="
python3 "$RESET" --json \
  $(for e in $PILOT_LIST; do echo "$ROOT/$e/Train"; done) \
  | tee "$ROOT/packc_tip_reset.json"

echo "=== short amp after tip reset ==="
MAX_JOBS="${MAX_JOBS:-2}" \
TRAIN_T="${TRAIN_T:-80}" \
AMP_TRAIN_STEPS="${AMP_TRAIN_STEPS:-80 160}" \
AMP_ABORT_HARD_OSC=1 \
AMP_HARD_OSC_NO_IMPROVE="${AMP_HARD_OSC_NO_IMPROVE:-20}" \
ALLOW_PARTIAL_TRAIN=1 \
SKIP_TRAIN=0 \
PILOT_EXPS="$PILOT_LIST" \
  bash "$ROOT/scripts/run_asymrm.sh" || true

python3 "$FINGER" --write "$POST_FP"
python3 "$FINGER" --diff "$PRE_FP"

echo "=== verify Done on pilot ==="
fail=0
for e in $PILOT_LIST; do
  if python3 "$VERIFY" --require-calibrated --require-sync-ok --diagnose \
      ${L_REF_JSON:+--L-reference "$L_REF_JSON"} \
      "$ROOT/$e/Train/Parameters_00.xml"; then
    echo "DONE_OK $e"
  else
    echo "STILL_NEED $e"
    fail=1
  fi
done

python3 "$ROOT/scripts/analyze_train_stall.py" --json \
  $(for e in $PILOT_LIST; do echo "$ROOT/$e/Train"; done) \
  > "$ROOT/finish_packC_gen_tip_reset_amp_stall.json" || true

restore_reports
echo "=== finish_packC_gen_tip_reset_amp done fail=$fail $(date -Iseconds) ==="
exit "$fail"

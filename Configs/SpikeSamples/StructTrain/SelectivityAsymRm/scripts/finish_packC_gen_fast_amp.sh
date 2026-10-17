#!/usr/bin/env bash
# Fast Pack C gen amp: TipR from Done Pack B, short steps, no refresh, hard-OSC abort.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/finish_packC_gen_fast_amp.log"
SEED_TIPR="$ROOT/scripts/seed_tipr_from_done_sibling.py"

PILOT_LIST="${PILOT_EXPS:-EXP_span50ms_packC_gen EXP_span100ms_packC_gen}"

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

exec > >(tee -a "$LOG") 2>&1
echo "=== finish_packC_gen_fast_amp $(date -Iseconds) ==="
echo "PILOT_EXPS=$PILOT_LIST"

for exp in $PILOT_LIST; do
  prune_keep_newest "$exp"
done

echo "=== TipR from Done Pack B sibling ==="
# shellcheck disable=SC2086
python3 "$SEED_TIPR" $(for e in $PILOT_LIST; do echo "$ROOT/$e/Train"; done)

export PILOT_EXPS="$PILOT_LIST"
export ADAPTIVE_TRAIN=1
export MAX_JOBS="${MAX_JOBS:-2}"
export L_REFERENCE=ltzcal
export AMP_ONLY=1
export AMP_SKIP_REFRESH=1
export AMP_FORCE_AT_L_REF=1
export AMP_PARTIAL_AT_L_REF=1
export AMP_TRAIN_STEPS="${AMP_TRAIN_STEPS:-160 320 640}"
export AMP_ABORT_HARD_OSC=1
export AMP_HARD_OSC_NO_IMPROVE="${AMP_HARD_OSC_NO_IMPROVE:-20}"
export SEED_INITIAL=1
export ALLOW_PARTIAL_TRAIN=1
# Do not inherit stale amp schedule / refresh from parent shells.
unset AMP_TRAIN_STEPS_OVERRIDE || true

echo "=== AMP_ONLY steps=$AMP_TRAIN_STEPS SKIP_REFRESH=1 ABORT_HARD_OSC=1 ==="
bash "$ROOT/scripts/run_asymrm.sh"
rc=$?

echo "=== post-amp stall ==="
# shellcheck disable=SC2086
python3 "$ROOT/scripts/analyze_train_stall.py" --json \
  $(for e in $PILOT_LIST; do echo "$ROOT/$e/Train"; done) \
  | tee "$ROOT/finish_packC_gen_fast_amp_stall.json" || true

VERIFY="$ROOT/../SelectivityLtzCalibrate/scripts/verify_train_done.py"
echo "=== verify ==="
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

# One TipR re-nudge + shorter amp if hard OSC still pending
if [[ "$fail" -ne 0 ]]; then
  hard=0
  if python3 - "$ROOT/finish_packC_gen_fast_amp_stall.json" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.is_file():
    sys.exit(1)
rows = json.loads(p.read_text())
for r in rows:
    if str(r.get("IsNeedToTrain")) == "0":
        continue
    if r.get("blocker") == "AMP_OSCILLATION":
        for d in r.get("dendrites") or []:
            if d.get("dend") == 3:
                continue
            if d.get("blocker") == "AMP_OSCILLATION" and float(d.get("no_improve") or 0) >= 20:
                sys.exit(0)
sys.exit(1)
PY
  then
    hard=1
  fi
  if [[ "$hard" -eq 1 ]]; then
    echo "=== re-nudge TipR + AMP_TRAIN_STEPS=160 320 ==="
    # shellcheck disable=SC2086
    python3 "$SEED_TIPR" $(for e in $PILOT_LIST; do echo "$ROOT/$e/Train"; done)
    for exp in $PILOT_LIST; do prune_keep_newest "$exp"; done
    export AMP_TRAIN_STEPS="160 320"
    bash "$ROOT/scripts/run_asymrm.sh" || true
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
fi

echo "=== finish_packC_gen_fast_amp done rc=$rc fail=$fail $(date -Iseconds) ==="
exit "$fail"

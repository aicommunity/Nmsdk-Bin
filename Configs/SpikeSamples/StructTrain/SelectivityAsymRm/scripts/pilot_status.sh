#!/usr/bin/env bash
# Quick pilot v3 status: Done count, L, sync, blocker.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERIFY="$ROOT/../../SelectivityLtzCalibrate/scripts/verify_train_done.py"
STALL="$ROOT/scripts/analyze_train_stall.py"
SYNC="$ROOT/scripts/analyze_sync_tolerance.py"
PILOT_EXPS="${PILOT_EXPS:-EXP_span25ms_packA_gen EXP_span25ms_packA_preinh EXP_span100ms_packA_preinh}"
L_REF="${L_REF:-$ROOT/l_reference.json}"

done_n=0
total=0
echo "# Pilot status $(date -Iseconds)"
for exp in $PILOT_EXPS; do
  total=$((total + 1))
  p="$ROOT/$exp/Train/Parameters_00.xml"
  [[ -f "$p" ]] || { echo "$exp: MISSING"; continue }
  if python3 "$VERIFY" --require-sync-ok --require-calibrated \
      ${L_REF:+--L-reference "$L_REF"} "$p" >/dev/null 2>&1; then
    done_n=$((done_n + 1))
    st="DONE"
  else
    st="NOT_DONE"
  fi
  blocker=$(python3 "$STALL" "$ROOT/$exp/Train" --json 2>/dev/null | python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
print(d[0].get('blocker','?') if d else '?')
" 2>/dev/null || echo "?")
  L=$(grep -oP '(?<=<DendriteLength[^>]*>)[^<]+' "$p" | head -1)
  sync=$(python3 "$SYNC" "$ROOT/$exp/Train" 2>/dev/null | tail -1)
  echo "$exp: $st blocker=$blocker L=$L"
done
echo "Gate: $done_n / $total Done (need >=2 for scale)"

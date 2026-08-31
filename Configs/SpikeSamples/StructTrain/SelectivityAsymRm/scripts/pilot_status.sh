#!/usr/bin/env bash
# Quick pilot v3 status: Done count, L, sync, blocker.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERIFY="$ROOT/../../SelectivityLtzCalibrate/scripts/verify_train_done.py"
STALL="$ROOT/scripts/analyze_train_stall.py"
PILOT_EXPS="${PILOT_EXPS:-EXP_span25ms_packA_gen EXP_span25ms_packA_preinh EXP_span100ms_packA_preinh}"
L_REF="${L_REF:-$ROOT/l_reference.json}"

n_ok=0
n_total=0
echo "# Pilot status $(date -Iseconds)"
for exp in $PILOT_EXPS; do
  n_total=$((n_total + 1))
  p="$ROOT/$exp/Train/Parameters_00.xml"
  if [[ ! -f "$p" ]]; then
    echo "$exp: MISSING"
    continue
  fi
  st="NOT_DONE"
  if python3 "$VERIFY" --require-sync-ok --require-calibrated \
      ${L_REF:+--L-reference "$L_REF"} "$p" >/dev/null 2>&1; then
    n_ok=$((n_ok + 1))
    st="DONE"
  fi
  blocker=$(python3 "$STALL" "$ROOT/$exp/Train" --json 2>/dev/null | \
    python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print(d[0].get("blocker","?") if d else "?")' \
    2>/dev/null || echo "?")
  L=$(python3 -c "
import re, sys
from pathlib import Path
t = Path(sys.argv[1]).read_text(encoding='utf-8')
m = re.search(r'<DendriteLength[^>]*>([^<]*)</DendriteLength>', t)
print(m.group(1).strip() if m else '?')
" "$p")
  echo "$exp: $st blocker=$blocker L=$L"
done
echo "Gate: $n_ok / $n_total Done (need >=2 for scale)"

#!/usr/bin/env bash
# ResistanceAdjustGain / IterationGap / PeakMargin sweep on pilot EXP.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RESET="$ROOT/scripts/reset_asymrm_cold.sh"
RUN="$ROOT/scripts/run_asymrm.sh"
GRID="$ROOT/amp_sweep"
PILOT_EXPS="${PILOT_EXPS:-EXP_span25ms_packA_gen EXP_span25ms_packA_preinh EXP_span100ms_packA_preinh}"
MAX_JOBS="${MAX_JOBS:-1}"
GTS="${GTS:-20000}"

mkdir -p "$GRID"

patch_train_param() {
  local params="$1" tag="$2" val="$3"
  python3 - "$params" "$tag" "$val" <<'PY'
import re, sys
from pathlib import Path
p, tag, val = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
t = p.read_text(encoding="utf-8")
t = re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{val}\2", t, count=0)
p.write_text(t, encoding="utf-8")
PY
}

patch_peak_margin() {
  local exp="$1" margin="$2"
  for f in "$ROOT/$exp/Train/Parameters_00.xml" "$ROOT/$exp/Train/Model_00.xml" \
           "$ROOT/$exp/Test/Parameters_00.xml" "$ROOT/$exp/Test/Model_00.xml"; do
    [[ -f "$f" ]] && patch_train_param "$f" "PeakMeasureMargin" "$margin"
  done
}

run_case() {
  local tag="$1" gain="$2" igap="$3" pmargin="${4:-}"
  local out="$GRID/$tag"
  mkdir -p "$out"
  echo "======== AMP SWEEP $tag gain=$gain igap=$igap pmargin=${pmargin:-default} ========"
  GTS="$GTS" PILOT_EXPS="$PILOT_EXPS" RESET_TEST=0 bash "$RESET"
  for exp in $PILOT_EXPS; do
    p="$ROOT/$exp/Train/Parameters_00.xml"
    m="$ROOT/$exp/Train/Model_00.xml"
    patch_train_param "$p" "ResistanceAdjustGain" "$gain"
    patch_train_param "$m" "ResistanceAdjustGain" "$gain"
    patch_train_param "$p" "IterationGap" "$igap"
    patch_train_param "$m" "IterationGap" "$igap"
    if [[ -n "$pmargin" ]]; then
      patch_peak_margin "$exp" "$pmargin"
    fi
  done
  ALLOW_PARTIAL_TRAIN=1 MAX_JOBS="$MAX_JOBS" GTS="$GTS" PILOT_EXPS="$PILOT_EXPS" \
    ADAPTIVE_TRAIN=1 bash "$RUN" 2>&1 | tee "$out/run.log" || true
  cp "$ROOT/stall_latest.csv" "$out/stall.csv" 2>/dev/null || true
  cp "$ROOT/feasibility_latest.csv" "$out/feasibility.csv" 2>/dev/null || true
  python3 "$ROOT/scripts/analyze_peak_sync.py" \
    $(for e in $PILOT_EXPS; do echo "$ROOT/$e/Train"; done) \
    -o "$out/peak_sync.json" --md "$out/PEAK_SYNC.md" || true
}

# Default grid from plan
run_case "baseline" "0.4" "1.5" ""
run_case "gain_low" "0.2" "1.5" ""
run_case "gain_high" "0.8" "1.5" ""
run_case "faster_iter" "0.4" "1.0" ""
run_case "margin_wide" "0.4" "1.5" "0.003"
run_case "margin_narrow" "0.4" "1.5" "0.001458"

echo "Amp sweep done. Results in $GRID/"

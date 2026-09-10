#!/usr/bin/env bash
# Test-only re-run for StructTrain experiments (no Train). Writes AUDIT_GATE_RECOMPUTE.csv
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
METRICS="$ROOT/scripts/selectivity_metrics.py"
OUT="${OUT:-$ROOT/AUDIT_GATE_RECOMPUTE.csv}"
TIMEOUT_SEC="${TIMEOUT_SEC:-180}"
TEST_SIM_T="${TEST_SIM_T:-22}"
PRIORITY_ONLY="${PRIORITY_ONLY:-0}"
PARALLEL="${PARALLEL:-4}"
SKIP_MERGE="${SKIP_MERGE:-1}"
LOG="$ROOT/scripts/_rerun_tests.log"
JOBS_DIR="$ROOT/scripts/_rerun_jobs"
mkdir -p "$JOBS_DIR"
rm -f "$JOBS_DIR"/*.row "$JOBS_DIR"/*.log

list_tests() {
  ROOT="$ROOT" python3 - <<'PY'
from pathlib import Path
import os
ROOT = Path(os.environ["ROOT"])
EXCLUDE = {"XOR", "SpikeAnsTrainer", "SpikeTrainer", "RTlibs"}
rows = []
for camp in sorted(ROOT.iterdir()):
    if not camp.is_dir() or camp.name.startswith(".") or camp.name in EXCLUDE:
        continue
    if not (camp.name.startswith("Selectivity") or camp.name.startswith("TimeNeuron")):
        continue
    for test in camp.rglob("Test"):
        if not test.is_dir() or test.name != "Test":
            continue
        if ".statistic" in str(test):
            continue
        if "Train" in test.parts:
            continue
        ini = test / "Project.ini"
        if ini.exists():
            rows.append(str(ini))
print("\n".join(sorted(set(rows))))
PY
}

is_priority() {
  case "$1" in
    *span25*|*/TimeNeuronTimeLearnerBranch/*|*NextSegInh*|*PreInh250*) return 0 ;;
    *) return 1 ;;
  esac
}

run_one() {
  local ini="$1"
  local idx="$2"
  local test_dir exp_rel csv line rowfile
  test_dir="$(dirname "$ini")"
  exp_rel="${test_dir#$ROOT/}"
  rowfile="$JOBS_DIR/$(printf '%04d' "$idx").row"
  {
    echo "=== TEST $exp_rel ==="
    if [ "$SKIP_MERGE" != "1" ]; then
      local train_dir
      train_dir="$(dirname "$test_dir")/Train"
      if [ -d "$train_dir" ] && [ -f "$train_dir/Parameters_00.xml" ] && [ -f "$test_dir/Parameters_00.xml" ]; then
        if [ -f "$ROOT/SelectivityLtzCalibrate/scripts/merge_train_weights.py" ]; then
          python3 "$ROOT/SelectivityLtzCalibrate/scripts/merge_train_weights.py" --test \
            "$train_dir/Parameters_00.xml" "$test_dir/Parameters_00.xml" || true
        fi
      fi
    fi
    timeout "$TIMEOUT_SEC" "$NM" -c "$ini" -s -t "$TEST_SIM_T" -x || echo "run_exit=$?"
  } >"$JOBS_DIR/$(printf '%04d' "$idx").log" 2>&1

  csv="$test_dir/SelectivityLog/results.csv"
  line="$(python3 "$METRICS" -v "$csv" 2>/dev/null || true)"
  if [ -z "$line" ]; then
    line="ok=0 n=0 acc=0 target_hit=0 fire_all=0 mode=missing fires= matches= fa=0 ok_strict=0 ok_audit=0 acc_strict=0 fire_all_strict=0 late_fp=0 late_fn=0 response_quality=missing n_burst=0 n_per_stim=0 max_spikes=0"
  fi
  python3 - <<PY >"$rowfile"
import re
line = """$line"""
exp = """$exp_rel"""
csv = """${csv#$ROOT/}"""
kv = dict(re.findall(r"(\w+)=([^\s]+)", line))
def g(k, d="0"):
    return kv.get(k, d)
print(",".join([
    exp, g("n"), g("ok"), g("ok_strict"), g("ok_audit"), g("acc"), g("acc_strict"),
    g("fire_all"), g("fire_all_strict"), g("late_fp"), g("late_fn"),
    g("response_quality", "missing"), g("n_burst"), g("n_per_stim"), g("max_spikes"),
    g("mode", "missing"), csv,
]))
PY
  echo "done $exp_rel" >>"$LOG"
}

echo "exp,n,ok_legacy,ok_strict,ok_audit,acc_legacy,acc_strict,fire_all_legacy,fire_all_strict,late_fp,late_fn,response_quality,n_burst,n_per_stim,max_spikes,mode_legacy,csv" > "$OUT"
: > "$LOG"

mapfile -t ALL < <(list_tests)
INIS=()
idx=0
for ini in "${ALL[@]}"; do
  if [ "$PRIORITY_ONLY" = "1" ] && ! is_priority "$ini"; then
    continue
  fi
  INIS+=("$ini")
done
echo "Running ${#INIS[@]} / ${#ALL[@]} tests PARALLEL=$PARALLEL" | tee -a "$LOG"

active=0
i=0
for ini in "${INIS[@]}"; do
  run_one "$ini" "$i" &
  i=$((i + 1))
  active=$((active + 1))
  if [ "$active" -ge "$PARALLEL" ]; then
    wait -n || true
    active=$((active - 1))
  fi
done
wait || true

cat "$JOBS_DIR"/*.row >> "$OUT" 2>/dev/null || true
echo "Wrote $OUT ($(wc -l < "$OUT") lines)" | tee -a "$LOG"

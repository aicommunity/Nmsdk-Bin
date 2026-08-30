#!/usr/bin/env bash
# AsymRm train + AutoCalibrate + adaptive TRAIN_T continue + sync + test.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LTZCAL_SCRIPTS="$(cd "$(dirname "$0")/../../SelectivityLtzCalibrate/scripts" && pwd)"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
MAX_JOBS="${MAX_JOBS:-3}"
TRAIN_T="${TRAIN_T:-80}"
TEST_T="${TEST_T:-20}"
META="$ROOT/grid_cells.tsv"
OUT="$ROOT/grid_summary.csv"
LOG="$ROOT/run_asymrm.log"
VERIFY="$ROOT/scripts/verify_element_params.py"
VERIFY_SPAN="$ROOT/scripts/verify_pattern_span.py"
COPY="$ROOT/scripts/copy_config.sh"
LTZ_TRAIN="$LTZCAL_SCRIPTS/patch_ltz_calibrate_train.py"
LTZ_TEST="$LTZCAL_SCRIPTS/patch_ltz_calibrate_test.py"
VERIFY_DONE="$LTZCAL_SCRIPTS/verify_train_done.py"
STALL="$ROOT/scripts/analyze_train_stall.py"
FEAS="$ROOT/scripts/check_timing_feasibility.py"
PILOT_EXPS="${PILOT_EXPS:-}"
ADAPTIVE_TRAIN="${ADAPTIVE_TRAIN:-1}"
TRAIN_STEPS="${TRAIN_STEPS:-80 160 320 640}"
SKIP_TRAIN="${SKIP_TRAIN:-0}"
ALLOW_PARTIAL_TRAIN="${ALLOW_PARTIAL_TRAIN:-0}"

[[ -f "$META" ]] || { echo "Run setup_asymrm.sh first" >&2; exit 1; }

mapfile -t ALL_EXPS < <(awk -F'\t' 'NR>1{print $1}' "$META")
EXPS=()
for e in "${ALL_EXPS[@]}"; do
  if [[ -z "$PILOT_EXPS" ]]; then EXPS+=("$e"); continue; fi
  for p in $PILOT_EXPS; do [[ "$p" == "$e" ]] && EXPS+=("$e"); done
done
((${#EXPS[@]})) || { echo "No EXP selected (PILOT_EXPS=$PILOT_EXPS)" >&2; exit 1; }

exp_meta() {
  awk -F'\t' -v e="$1" -v c="$2" '$1==e{print $c;exit}' "$META"
}

verify_model() {
  local model="$1" neuron="$2" kind="$3" cap="$4" exc_rm="$5" exc_rsyn="$6"
  python3 - "$exc_rm" "$exc_rsyn" <<'PY' > /tmp/asym_inh_vals.txt
import sys
exc_rm=float(sys.argv[1]); exc_rsyn=float(sys.argv[2])
print(f"{exc_rm*10:g}")
print(f"{exc_rsyn*10:g}")
PY
  local inh_rm inh_rsyn
  inh_rm=$(sed -n '1p' /tmp/asym_inh_vals.txt)
  inh_rsyn=$(sed -n '2p' /tmp/asym_inh_vals.txt)
  local args=(--expect-dissoc "${DISSOC:-0.001}" --expect-cap "$cap" --expect-secr "${SECR:-0.001}"
    --expect-exc-r "$exc_rm" --expect-inh-r "$inh_rm"
    --expect-inh-syn-r "$inh_rsyn"
    --expect-class "$neuron" --min-count 4)
  if [[ "$kind" == *preinh* ]]; then args+=(--expect-inh 2.5); else args+=(--no-inh); fi
  python3 "$VERIFY" "$model" "${args[@]}"
}

run_wave() {
  local mode="$1" tlim="$2"
  local -a pids=() dirs=()
  local running=0 fail=0
  wait_one() {
    local pid="${pids[0]}" d="${dirs[0]}"
    pids=("${pids[@]:1}"); dirs=("${dirs[@]:1}")
    if wait "$pid"; then echo "OK $mode $d"; else echo "FAIL $mode $d"; fail=$((fail+1)); fi
    running=$((running-1))
  }
  for exp in "${EXPS[@]}"; do
    while (( running >= MAX_JOBS )); do wait_one; done
    local dir="$ROOT/$exp/$( [[ $mode == train ]] && echo Train || echo Test )"
    local ini=Project.ini
    [[ -f "$dir/project.ini" ]] && ini=project.ini
    echo "START $mode $exp t=$tlim"
    (
      cd "$dir"
      if [[ "$mode" == train ]]; then
        "$NM" -c "$ini" -s -t "$tlim" -x -S >run_console.log 2>&1
      else
        "$NM" -c "$ini" -s -t "$tlim" -x >run_console.log 2>&1
      fi
    ) &
    pids+=($!); dirs+=("$exp"); running=$((running+1))
  done
  while (( running > 0 )); do wait_one; done
  return "$fail"
}

apply_ltz_train_patch() {
  for exp in "${EXPS[@]}"; do
    kind=$(exp_meta "$exp" 4)
    p="$ROOT/$exp/Train/Parameters_00.xml"
    if [[ "$kind" == *preinh* ]]; then
      python3 "$LTZ_TRAIN" --preinh "$p"
    else
      python3 "$LTZ_TRAIN" "$p"
    fi
  done
}

train_one_exp() {
  local exp="$1" tlim="$2"
  local dir="$ROOT/$exp/Train"
  local ini=Project.ini
  [[ -f "$dir/project.ini" ]] && ini=project.ini
  ( cd "$dir"; "$NM" -c "$ini" -s -t "$tlim" -x -S >run_console.log 2>&1 )
}

get_stall_blocker() {
  python3 "$STALL" "$ROOT/$1/Train" --json 2>/dev/null | python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
print(d[0].get('blocker','UNKNOWN') if d else 'UNKNOWN')
" 2>/dev/null || echo "UNKNOWN"
}

adaptive_train_exp() {
  local exp="$1"
  local -a steps=($TRAIN_STEPS)
  if [[ "$ADAPTIVE_TRAIN" != "1" ]]; then
    train_one_exp "$exp" "$TRAIN_T"
    return $?
  fi
  local cumulative=0
  for step in "${steps[@]}"; do
    echo "=== adaptive train $exp step=$step (cumulative +$step) ==="
    train_one_exp "$exp" "$step" || return 1
    cumulative=$((cumulative + step))
    if python3 "$VERIFY_DONE" --require-calibrated "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
      echo "DONE $exp after cumulative T=$cumulative"
      return 0
    fi
    blocker=$(get_stall_blocker "$exp")
    echo "stall $exp blocker=$blocker after T=$cumulative"
    case "$blocker" in
      TIME_BUDGET|LENGTH_STALL) continue ;;
      PEAK_INVALID) echo "route PEAK_INVALID — stop adaptive for $exp"; return 0 ;;
      AMP_AT_RMIN|AMP_OSCILLATION|AMP_PENDING) echo "route AMP — stop adaptive for $exp"; return 0 ;;
      *) continue ;;
    esac
  done
  return 0
}

adaptive_train_all() {
  local -a pids=() dirs=()
  local running=0 fail=0
  wait_one() {
    local pid="${pids[0]}" d="${dirs[0]}"
    pids=("${pids[@]:1}"); dirs=("${dirs[@]:1}")
    if wait "$pid"; then echo "OK train $d"; else echo "FAIL train $d"; fail=$((fail+1)); fi
    running=$((running-1))
  }
  for exp in "${EXPS[@]}"; do
    while (( running >= MAX_JOBS )); do wait_one; done
    ( adaptive_train_exp "$exp" ) &
    pids+=($!); dirs+=("$exp"); running=$((running+1))
  done
  while (( running > 0 )); do wait_one; done
  return "$fail"
}

exec > >(tee "$LOG") 2>&1

echo "=== EXP count=${#EXPS[@]} TRAIN_T start=$TRAIN_T ADAPTIVE=$ADAPTIVE_TRAIN ==="
echo "=== LTZ train patch ==="
apply_ltz_train_patch

echo "=== VERIFY pattern spans (pre-run) ==="
python3 "$VERIFY_SPAN" --meta "$META" \
  $(for e in "${EXPS[@]}"; do echo "$ROOT/$e/Train/Parameters_00.xml" "$ROOT/$e/Test/Parameters_00.xml"; done)

if [[ "$SKIP_TRAIN" != "1" ]]; then
  echo "=== TRAIN wave ==="
  if [[ "$ADAPTIVE_TRAIN" == "1" ]]; then
    adaptive_train_all || exit 1
  else
    run_wave train "$TRAIN_T" || exit 1
  fi
fi

echo "=== Feasibility + stall snapshot ==="
python3 "$FEAS" --post $(for e in "${EXPS[@]}"; do echo "$ROOT/$e/Train/Parameters_00.xml"; done) \
  -o "$ROOT/feasibility_latest.csv"
python3 "$STALL" $(for e in "${EXPS[@]}"; do echo "$ROOT/$e/Train"; done) \
  -o "$ROOT/stall_latest.csv"

echo "=== VERIFY train Done + calibrated ==="
fail_done=0
for exp in "${EXPS[@]}"; do
  if ! python3 "$VERIFY_DONE" --require-calibrated --diagnose \
      "$ROOT/$exp/Train/Parameters_00.xml"; then
    echo "TRAIN_NOT_DONE_OR_UNCALIBRATED $exp"
    fail_done=1
  fi
done
if (( fail_done )) && [[ "$ALLOW_PARTIAL_TRAIN" != "1" ]]; then
  echo "Abort sync/test: train not Done/calibrated."
  exit 1
fi

echo "=== VERIFY Train Models ==="
for exp in "${EXPS[@]}"; do
  verify_model "$ROOT/$exp/Train/Model_00.xml" \
    "$(exp_meta "$exp" 2)" "$(exp_meta "$exp" 4)" "$(exp_meta "$exp" 6)" \
    "$(exp_meta "$exp" 7)" "$(exp_meta "$exp" 8)"
done

echo "=== SYNC train -> test + LTZ patch ==="
for exp in "${EXPS[@]}"; do
  neuron=$(exp_meta "$exp" 2)
  kind=$(exp_meta "$exp" 4)
  cap=$(exp_meta "$exp" 6)
  exc_rm=$(exp_meta "$exp" 7)
  exc_rsyn=$(exp_meta "$exp" 8)
  echo "sync $exp"
  "$COPY" sync "$ROOT/$exp/Train" "$ROOT/$exp/Test"
  python3 "$LTZ_TEST" "$ROOT/$exp/Test/Parameters_00.xml" \
    --train "$ROOT/$exp/Train/Parameters_00.xml"
  python3 - "$ROOT/$exp/Train/Parameters_00.xml" "$ROOT/$exp/Test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
train = Path(sys.argv[1]).read_text(encoding="utf-8")
tp = Path(sys.argv[2]); test = tp.read_text(encoding="utf-8"); neuron = sys.argv[3]
def set_tag(text, tag, value, count=1):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count)
def get_tag(text, tag):
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)
    return m.group(1) if m else None
test = set_tag(test, "NeuronClassName", neuron, 0)
for tag in ("UseElementDefaults", "MembraneCapacity", "SynapseDissociationTC", "SynapseSecretionTC",
            "ExcMembraneResistance", "InhMembraneResistance", "ExcSynapseResistance",
            "InhSynapseResistance", "FixedLTZThreshold", "CalibratedFixedLTZThreshold"):
    v = get_tag(train, tag)
    if v is not None:
        test = set_tag(test, tag, v, 0)
tp.write_text(test, encoding="utf-8")
PY
  verify_model "$ROOT/$exp/Test/Model_00.xml" "$neuron" "$kind" "$cap" "$exc_rm" "$exc_rsyn"
done

echo "=== TEST wave t=$TEST_T ==="
run_wave test "$TEST_T" || exit 1

printf "exp,neuron,span_ms,kind,pack,acc,fn,fp,fires,mode,gate,target_hit,L,FixedLTZ,stall_blocker,L_target,iter_count\n" > "$OUT"
for exp in "${EXPS[@]}"; do
  neuron=$(exp_meta "$exp" 2)
  span=$(exp_meta "$exp" 3)
  kind=$(exp_meta "$exp" 4)
  pack=$(exp_meta "$exp" 5)
  csv="$ROOT/$exp/Test/SelectivityLog/results.csv"
  params="$ROOT/$exp/Train/Parameters_00.xml"
  stall_json=$(python3 "$STALL" "$ROOT/$exp/Train" --json 2>/dev/null || echo '[]')
  python3 - "$OUT" "$exp" "$neuron" "$span" "$kind" "$pack" "$csv" "$params" "$stall_json" <<'PY'
import csv, json, re, sys
from pathlib import Path
out, exp, neuron, span, kind, pack, csv_path, params, stall_json = sys.argv[1:10]
rows = list(csv.DictReader(Path(csv_path).open(encoding="utf-8"))) if Path(csv_path).exists() else []
acc = fn = fp = fires = target_hit = gate = 0
mode = "silent"
if rows:
    for r in rows:
        fired = r.get("neuron_fired", "0") == "1"
        if r.get("match", "0") == "1": acc += 1
        if fired: fires += 1
        if r.get("target_class") == "1" and not fired: fn += 1
        if r.get("target_class") == "0" and fired: fp += 1
    n = len(rows)
    if rows[0].get("target_class") == "1" and rows[0].get("neuron_fired") == "1":
        target_hit = 1
    fire_all = fires == n
    mode = "fire_all" if fire_all else ("silent" if fires == 0 else "partial_FA")
    gate = 1 if (target_hit and not fire_all and acc >= 4) else 0
    acc_s = f"{acc}/{n}"
else:
    acc_s = "0/0"
pt = Path(params).read_text(encoding="utf-8")
Lm = re.search(r"<DendriteLength[^>]*>([^<]*)</DendriteLength>", pt)
L = Lm.group(1).strip() if Lm else ""
Fm = re.search(r"<FixedLTZThreshold[^>]*>([^<]*)</FixedLTZThreshold>", pt)
flt = Fm.group(1) if Fm else ""
stall = {}
try:
    sj = json.loads(stall_json)
    if sj: stall = sj[0]
except Exception:
    pass
blocker = stall.get("blocker", "")
lt = stall.get("L_target", [])
lt_s = " ".join(str(x) for x in lt) if lt else ""
iter_c = stall.get("iter_count", "")
with open(out, "a", encoding="utf-8") as f:
    f.write(f"{exp},{neuron},{span},{kind},{pack},{acc_s},{fn},{fp},{fires},{mode},{gate},{target_hit},{L},{flt},{blocker},{lt_s},{iter_c}\n")
print(exp, acc_s, mode, "gate", gate, "blocker", blocker)
PY
done
echo "Wrote $OUT"
cat "$OUT"

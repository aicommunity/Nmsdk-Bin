#!/usr/bin/env bash
# Train + verify Done+calibrate + sync + Test for AsymRmLtzCal (Pack A).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GRID="$ROOT/AsymRmLtzCal"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
MAX_JOBS="${MAX_JOBS:-3}"
TRAIN_T="${TRAIN_T:-80}"
TEST_T="${TEST_T:-20}"
META="$GRID/grid_cells.tsv"
OUT="$GRID/grid_summary.csv"
LOG="$GRID/run_asymrm_ltzcal.log"
COPY="$ROOT/scripts/copy_config.sh"
VERIFY_EL="${VERIFY_EL:-$ROOT/../SelectivityAsymRm/scripts/verify_element_params.py}"
VERIFY_SPAN="$ROOT/scripts/verify_pattern_span.py"
LTZ_TEST="$ROOT/scripts/patch_ltz_calibrate_test.py"
EVAL="$ROOT/scripts/evaluate_selectivity_csv.py"
VERIFY_DONE="$ROOT/scripts/verify_train_done.py"
LTZ_TRAIN="$ROOT/scripts/patch_ltz_calibrate_train.py"

[[ -f "$META" ]] || { echo "Run setup_asymrm_ltzcal.sh first" >&2; exit 1; }

# Warm gate optional: SKIP_REGRESSION_GATE=1 (warm already PASS for campaign).
if [[ "${SKIP_REGRESSION_GATE:-1}" != "1" ]]; then
  if [[ ! -f "$ROOT/REGRESSION.md" ]] || ! grep -q '\*\*PASS\*\*' "$ROOT/REGRESSION.md"; then
    echo "REGRESSION.md missing PASS — set SKIP_REGRESSION_GATE=1 or run warm gate" >&2
    exit 1
  fi
fi

mapfile -t EXPS < <(awk -F'\t' 'NR>1{print $1}' "$META")

apply_phase1_baseline() {
  echo "=== PHASE1_BASELINE: disable AutoCalibrate on Train ==="
  for exp in "${EXPS[@]}"; do
    kind=$(awk -F'\t' -v e="$exp" '$1==e{print $4;exit}' "$META")
    p="$GRID/$exp/Train/Parameters_00.xml"
    python3 - "$p" <<'PY'
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
t = re.sub(r"(<AutoCalibrateFixedLTZThreshold\b[^>]*>)[^<]*(</AutoCalibrateFixedLTZThreshold>)", r"\g<1>0\2", t)
p.write_text(t, encoding="utf-8")
print("PHASE1", p)
PY
  done
}

apply_phase2_ltzcal() {
  echo "=== PHASE2_LTZCAL: enable AutoCalibrate, continue train ==="
  for exp in "${EXPS[@]}"; do
    kind=$(awk -F'\t' -v e="$exp" '$1==e{print $4;exit}' "$META")
    p="$GRID/$exp/Train/Parameters_00.xml"
    if [[ "$kind" == *preinh* ]]; then
      python3 "$LTZ_TRAIN" --preinh "$p"
    else
      python3 "$LTZ_TRAIN" "$p"
    fi
    python3 - "$p" <<'PY'
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
def set_tag(text, tag, value, count=0):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count or 0)
t = set_tag(t, "ResetToUntrainedState", "0", 0)
t = set_tag(t, "IsNeedToTrain", "1", 1)
t = set_tag(t, "StructureBuildMode", "1", 1)
p.write_text(t, encoding="utf-8")
print("PHASE2", p)
PY
  done
}

if [[ "${PHASE1_BASELINE:-0}" == "1" ]]; then
  apply_phase1_baseline
fi
if [[ "${PHASE2_LTZCAL:-0}" == "1" ]]; then
  apply_phase2_ltzcal
fi

verify_model() {
  local model="$1" neuron="$2" kind="$3" cap="$4" exc_rm="$5" exc_rsyn="$6"
  python3 - "$exc_rm" "$exc_rsyn" <<'PY' > /tmp/asym_ltz_inh_vals.txt
import sys
exc_rm=float(sys.argv[1]); exc_rsyn=float(sys.argv[2])
print(f"{exc_rm*10:g}")
print(f"{exc_rsyn*10:g}")
PY
  local inh_rm inh_rsyn
  inh_rm=$(sed -n '1p' /tmp/asym_ltz_inh_vals.txt)
  inh_rsyn=$(sed -n '2p' /tmp/asym_ltz_inh_vals.txt)
  local args=(--expect-dissoc 0.001 --expect-cap "$cap" --expect-secr 0.001
    --expect-exc-r "$exc_rm" --expect-inh-r "$inh_rm"
    --expect-inh-syn-r "$inh_rsyn"
    --expect-class "$neuron" --min-count 4)
  if [[ "$kind" == *preinh* ]]; then
    args+=(--expect-inh 2.5)
  else
    args+=(--no-inh)
  fi
  python3 "$VERIFY_EL" "$model" "${args[@]}"
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
    local dir="$GRID/$exp/$( [[ $mode == train ]] && echo Train || echo Test )"
    local ini=Project.ini
    [[ -f "$dir/project.ini" ]] && ini=project.ini
    echo "START $mode $exp"
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

verify_test_ltz_synced() {
  local train_p="$1" test_p="$2"
  python3 - "$train_p" "$test_p" <<'PY'
import re, sys
from pathlib import Path
def get(path, tag):
    t = Path(path).read_text(encoding="utf-8")
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", t)
    return float(m.group(1)) if m else None
tr, te = get(sys.argv[1], "FixedLTZThreshold"), get(sys.argv[2], "FixedLTZThreshold")
if tr is None or te is None:
    print(f"FAIL missing FixedLTZ train={tr} test={te}")
    sys.exit(1)
if abs(tr - 0.0115) < 1e-9:
    print(f"FAIL FixedLTZ still cold 0.0115")
    sys.exit(1)
if abs(tr - te) > 1e-6:
    print(f"FAIL FixedLTZ mismatch train={tr} test={te}")
    sys.exit(1)
print(f"OK FixedLTZ synced {te}")
PY
}

exec > >(tee "$LOG") 2>&1

echo "=== VERIFY spans pre-run ==="
python3 "$VERIFY_SPAN" --meta "$META" \
  "$GRID"/EXP_*/Train/Parameters_00.xml \
  "$GRID"/EXP_*/Test/Parameters_00.xml

echo "=== TRAIN t=$TRAIN_T MAX_JOBS=$MAX_JOBS ==="
if [[ "${SKIP_TRAIN:-0}" != "1" ]]; then
  run_wave train "$TRAIN_T" || exit 1
else
  echo "SKIP_TRAIN=1"
fi

echo "=== VERIFY train Done + calibrated ==="
fail_done=0
for exp in "${EXPS[@]}"; do
  if ! python3 "$VERIFY_DONE" --require-calibrated "$GRID/$exp/Train/Parameters_00.xml"; then
    echo "TRAIN_NOT_DONE_OR_UNCALIBRATED $exp"
    fail_done=1
  fi
done
if (( fail_done )) && [[ "${ALLOW_PARTIAL_TRAIN:-0}" != "1" ]]; then
  echo "Abort sync/test: train not Done/calibrated. Try TRAIN_T=160/320 or PHASE2_LTZCAL=1."
  exit 1
fi
if (( fail_done )); then
  echo "WARN: ALLOW_PARTIAL_TRAIN=1 — continuing"
fi

echo "=== VERIFY Train element params Pack A ==="
for exp in "${EXPS[@]}"; do
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  kind=$(awk -F'\t' -v e="$exp" '$1==e{print $4;exit}' "$META")
  cap=$(awk -F'\t' -v e="$exp" '$1==e{print $6;exit}' "$META")
  exc_rm=$(awk -F'\t' -v e="$exp" '$1==e{print $7;exit}' "$META")
  exc_rsyn=$(awk -F'\t' -v e="$exp" '$1==e{print $8;exit}' "$META")
  verify_model "$GRID/$exp/Train/Model_00.xml" "$neuron" "$kind" "$cap" "$exc_rm" "$exc_rsyn"
done

echo "=== SYNC + LTZ test patch ==="
for exp in "${EXPS[@]}"; do
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  kind=$(awk -F'\t' -v e="$exp" '$1==e{print $4;exit}' "$META")
  cap=$(awk -F'\t' -v e="$exp" '$1==e{print $6;exit}' "$META")
  exc_rm=$(awk -F'\t' -v e="$exp" '$1==e{print $7;exit}' "$META")
  exc_rsyn=$(awk -F'\t' -v e="$exp" '$1==e{print $8;exit}' "$META")
  echo "sync $exp"
  "$COPY" sync "$GRID/$exp/Train" "$GRID/$exp/Test"
  python3 "$LTZ_TEST" "$GRID/$exp/Test/Parameters_00.xml" --train "$GRID/$exp/Train/Parameters_00.xml"
  python3 - "$GRID/$exp/Test/Model_00.xml" "$GRID/$exp/Test/Parameters_00.xml" \
    "$neuron" "$cap" "$exc_rm" "$exc_rsyn" <<'PY'
import re, sys
from pathlib import Path
mp, pp = Path(sys.argv[1]), Path(sys.argv[2])
neuron, cap, exc_rm, exc_rsyn = sys.argv[3:7]
inh_rm = f"{float(exc_rm)*10:g}"
inh_rsyn = f"{float(exc_rsyn)*10:g}"

def set_tag(text, tag, value, count=0):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count or 0)

def ensure_after(text, after, tag, value):
    if re.search(rf"<{tag}\b", text):
        return set_tag(text, tag, value, 0)
    return re.sub(rf"(<{after}\b[^>]*>[^<]*</{after}>)",
                  rf'\1\n\t\t\t\t\t\t\t<{tag} Type="d" PType="257" IoType="17">{value}</{tag}>', text, count=1)

def patch(t):
    t = set_tag(t, "NeuronClassName", neuron, 1)
    t = set_tag(t, "UseElementDefaults", "1", 0)
    t = set_tag(t, "MembraneCapacity", cap, 0)
    t = set_tag(t, "SynapseDissociationTC", "0.001", 0)
    for tag, val in [("SynapseSecretionTC","0.001"),("ExcMembraneResistance",exc_rm),
                     ("InhMembraneResistance",inh_rm),("ExcSynapseResistance",exc_rsyn),
                     ("InhSynapseResistance",inh_rsyn)]:
        t = ensure_after(t, "SynapseDissociationTC", tag, val)
    t = set_tag(t, "StructureBuildMode", "1", 0)
    t = set_tag(t, "IsNeedToTrain", "0", 0)
    return t

m = mp.read_text(encoding="utf-8")
m = re.sub(r'(<Neuron Class=")[^"]+(">)', rf'\g<1>{neuron}\2', m, count=1)
mp.write_text(patch(m), encoding="utf-8")
pp.write_text(patch(pp.read_text(encoding="utf-8")), encoding="utf-8")
PY
  verify_test_ltz_synced "$GRID/$exp/Train/Parameters_00.xml" "$GRID/$exp/Test/Parameters_00.xml"
  verify_model "$GRID/$exp/Test/Model_00.xml" "$neuron" "$kind" "$cap" "$exc_rm" "$exc_rsyn"
done

echo "=== TEST t=$TEST_T ==="
run_wave test "$TEST_T"

printf "exp,neuron,span_ms,kind,pack,acc,fn,fp,fires,mode,gate,target_hit,L,FixedLTZ,CalibratedFixedLTZ\n" > "$OUT"
for exp in "${EXPS[@]}"; do
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  span=$(awk -F'\t' -v e="$exp" '$1==e{print $3;exit}' "$META")
  kind=$(awk -F'\t' -v e="$exp" '$1==e{print $4;exit}' "$META")
  pack=$(awk -F'\t' -v e="$exp" '$1==e{print $5;exit}' "$META")
  csv="$GRID/$exp/Test/SelectivityLog/results.csv"
  params="$GRID/$exp/Train/Parameters_00.xml"
  python3 - "$OUT" "$exp" "$neuron" "$span" "$kind" "$pack" "$csv" "$params" <<'PY'
import csv, re, sys
from pathlib import Path
out, exp, neuron, span, kind, pack, csv_path, params = sys.argv[1:9]
rows = list(csv.DictReader(Path(csv_path).open(encoding="utf-8"))) if Path(csv_path).exists() else []
acc = fn = fp = fires = target_hit = gate = 0
mode = "missing"
if rows:
    for r in rows:
        fired = r.get("neuron_fired") == "1"
        if r.get("match") == "1":
            acc += 1
        if fired:
            fires += 1
        if r.get("target_class") == "1" and not fired:
            fn += 1
        if r.get("target_class") == "0" and fired:
            fp += 1
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
Cm = re.search(r"<CalibratedFixedLTZThreshold[^>]*>([^<]*)</CalibratedFixedLTZThreshold>", pt)
cal = Cm.group(1) if Cm else ""
with open(out, "a", encoding="utf-8") as f:
    f.write(f"{exp},{neuron},{span},{kind},{pack},{acc_s},{fn},{fp},{fires},{mode},{gate},{target_hit},{L},{flt},{cal}\n")
print(exp, acc_s, mode, "gate", gate, "FixedLTZ", flt)
PY
done
echo "Wrote $OUT"
cat "$OUT"

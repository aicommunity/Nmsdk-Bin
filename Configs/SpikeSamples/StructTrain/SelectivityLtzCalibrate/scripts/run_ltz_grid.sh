#!/usr/bin/env bash
# Train + sync (merge_train_weights) + Test for FastSpanLtzCal grid.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GRID="$ROOT/FastSpanLtzCal"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
MAX_JOBS="${MAX_JOBS:-4}"
TRAIN_T="${TRAIN_T:-160}"
TEST_T="${TEST_T:-20}"
META="$ROOT/grid_cells.tsv"
OUT="$ROOT/grid_summary.csv"
LOG="$ROOT/run_ltz_grid.log"
COPY="$ROOT/scripts/copy_config.sh"
VERIFY="$ROOT/scripts/verify_element_params.py"
VERIFY_SPAN="$ROOT/scripts/verify_pattern_span.py"
LTZ_TEST="$ROOT/scripts/patch_ltz_calibrate_test.py"
EVAL="$ROOT/scripts/evaluate_selectivity_csv.py"

if [[ ! -f "$ROOT/REGRESSION.md" ]]; then
  echo "Run regression first (setup_regression.sh + run_regression.sh)" >&2
  exit 1
fi

if grep -q '\*\*FAIL\*\*' "$ROOT/REGRESSION.md"; then
  echo "Regression FAIL — fix before FastSpanLtzCal grid" >&2
  exit 1
fi

mapfile -t EXPS < <(awk -F'\t' 'NR>1{print $1}' "$META")

verify_model() {
  local model="$1" neuron="$2" kind="$3"
  local args=(--expect-dissoc 0.002 --expect-cap 2.5e-10 --expect-class "$neuron" --min-count 4)
  if [[ "$kind" == *preinh* ]]; then
    args+=(--expect-inh 2.5)
  else
    args+=(--no-inh)
  fi
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

exec > >(tee "$LOG") 2>&1

echo "=== VERIFY spans pre-run ==="
python3 "$VERIFY_SPAN" --meta "$META" \
  "$GRID"/EXP_*/Train/Parameters_00.xml \
  "$GRID"/EXP_*/Test/Parameters_00.xml

echo "=== TRAIN ==="
if [[ "${SKIP_TRAIN:-0}" != "1" ]]; then
  run_wave train "$TRAIN_T" || exit 1
else
  echo "SKIP_TRAIN=1 — using existing Train Parameters"
fi

echo "=== VERIFY Train models ==="
for exp in "${EXPS[@]}"; do
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  kind=$(awk -F'\t' -v e="$exp" '$1==e{print $4;exit}' "$META")
  verify_model "$GRID/$exp/Train/Model_00.xml" "$neuron" "$kind"
done

echo "=== SYNC (merge_train_weights via copy_config) ==="
for exp in "${EXPS[@]}"; do
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  echo "sync $exp"
  "$COPY" sync "$GRID/$exp/Train" "$GRID/$exp/Test"
  python3 "$LTZ_TEST" "$GRID/$exp/Test/Parameters_00.xml" --train "$GRID/$exp/Train/Parameters_00.xml"
  python3 - "$GRID/$exp/Test/Model_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
mp, neuron = Path(sys.argv[1]), sys.argv[2]
m = mp.read_text(encoding="utf-8")
m = re.sub(r'(<Neuron Class=")[^"]+(">)', rf'\g<1>{neuron}\2', m, count=1)
def set_tag(text, tag, value, count=0):
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count or 0)
m = set_tag(m, "NeuronClassName", neuron, 0)
m = set_tag(m, "UseElementDefaults", "1", 0)
m = set_tag(m, "MembraneCapacity", "2.5e-10", 0)
m = set_tag(m, "SynapseDissociationTC", "0.002", 0)
m = set_tag(m, "StructureBuildMode", "1", 0)
m = set_tag(m, "IsNeedToTrain", "0", 0)
mp.write_text(m, encoding="utf-8")
PY
  python3 - "$GRID/$exp/Test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
p, neuron = Path(sys.argv[1]), sys.argv[2]
t = p.read_text(encoding="utf-8")
def set_tag(text, tag, value, count=0):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count or 0)
for tag, val in [("NeuronClassName", neuron), ("UseElementDefaults", "1"), ("MembraneCapacity", "2.5e-10"), ("SynapseDissociationTC", "0.002"), ("StructureBuildMode", "1"), ("IsNeedToTrain", "0")]:
    t = set_tag(t, tag, val, count=1 if tag == "NeuronClassName" else 0)
p.write_text(t, encoding="utf-8")
PY
done

echo "=== TEST ==="
run_wave test "$TEST_T"

printf "exp,neuron,span_ms,kind,acc,fn,fp,fires,mode,gate,target_hit,L,FixedLTZ,CalibratedLTZ\n" > "$OUT"
for exp in "${EXPS[@]}"; do
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  span=$(awk -F'\t' -v e="$exp" '$1==e{print $3;exit}' "$META")
  kind=$(awk -F'\t' -v e="$exp" '$1==e{print $4;exit}' "$META")
  csv="$GRID/$exp/Test/SelectivityLog/results.csv"
  params="$GRID/$exp/Train/Parameters_00.xml"
  qline=$(python3 "$EVAL" "$csv" 2>/dev/null || echo "ok=0")
  python3 - "$OUT" "$exp" "$neuron" "$span" "$kind" "$csv" "$params" "$qline" <<'PY'
import csv, re, sys
from pathlib import Path
out, exp, neuron, span, kind, csv_path, params, qline = sys.argv[1:9]
rows = list(csv.DictReader(Path(csv_path).open(encoding="utf-8"))) if Path(csv_path).exists() else []
acc = fn = fp = fires = target_hit = gate = 0
mode = "missing"
if rows:
    for r in rows:
        fired = r.get("neuron_fired") == "1"
        tgt = r.get("target_class") == "0"
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
with open(out, "a") as f:
    f.write(f"{exp},{neuron},{span},{kind},{acc_s},{fn},{fp},{fires},{mode},{gate},{target_hit},{L},{flt},{cal}\n")
print(exp, acc_s, mode)
PY
done
echo "Wrote $OUT"
cat "$OUT"

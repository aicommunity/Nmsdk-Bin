#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
MAX_JOBS="${MAX_JOBS:-3}"
TRAIN_T="${TRAIN_T:-160}"
TEST_T="${TEST_T:-20}"
META="$ROOT/grid_cells.tsv"
OUT="$ROOT/grid_summary.csv"
LOG="$ROOT/run_asymrm.log"
VERIFY="$ROOT/scripts/verify_element_params.py"
VERIFY_SPAN="$ROOT/scripts/verify_pattern_span.py"
COPY="$ROOT/scripts/copy_config.sh"

[[ -f "$META" ]] || { echo "Run setup_asymrm.sh first" >&2; exit 1; }
mapfile -t EXPS < <(awk -F'\t' 'NR>1{print $1}' "$META")

verify_model() {
  local model="$1" neuron="$2" kind="$3" cap="$4" exc_rm="$5" exc_rsyn="$6"
  # Inh Rm = 10x; Inh Rsyn = 10x
  python3 - "$exc_rm" "$exc_rsyn" <<'PY' > /tmp/asym_inh_vals.txt
import sys
exc_rm=float(sys.argv[1]); exc_rsyn=float(sys.argv[2])
print(f"{exc_rm*10:g}")
print(f"{exc_rsyn*10:g}")
PY
  local inh_rm inh_rsyn
  inh_rm=$(sed -n '1p' /tmp/asym_inh_vals.txt)
  inh_rsyn=$(sed -n '2p' /tmp/asym_inh_vals.txt)
  local args=(--expect-dissoc 0.001 --expect-cap "$cap" --expect-secr 0.001
    --expect-exc-r "$exc_rm" --expect-inh-r "$inh_rm"
    --expect-inh-syn-r "$inh_rsyn"
    --expect-class "$neuron" --min-count 4)
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
    local dir="$ROOT/$exp/$( [[ $mode == train ]] && echo Train || echo Test )"
    local ini=Project.ini
    [[ -f "$dir/$ini" ]] || ini=project.ini
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

echo "=== VERIFY pattern spans (pre-run) ==="
python3 "$VERIFY_SPAN" --meta "$META" "$ROOT"/EXP_*/Train/Parameters_00.xml "$ROOT"/EXP_*/Test/Parameters_00.xml

echo "=== TRAIN wave MAX_JOBS=$MAX_JOBS t=$TRAIN_T ==="
if ! run_wave train "$TRAIN_T"; then
  echo "Train wave had failures" >&2
  exit 1
fi

echo "=== VERIFY Train Models ==="
for exp in "${EXPS[@]}"; do
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  kind=$(awk -F'\t' -v e="$exp" '$1==e{print $4;exit}' "$META")
  cap=$(awk -F'\t' -v e="$exp" '$1==e{print $6;exit}' "$META")
  exc_rm=$(awk -F'\t' -v e="$exp" '$1==e{print $7;exit}' "$META")
  exc_rsyn=$(awk -F'\t' -v e="$exp" '$1==e{print $8;exit}' "$META")
  verify_model "$ROOT/$exp/Train/Model_00.xml" "$neuron" "$kind" "$cap" "$exc_rm" "$exc_rsyn"
done

echo "=== SYNC train -> test ==="
for exp in "${EXPS[@]}"; do
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  kind=$(awk -F'\t' -v e="$exp" '$1==e{print $4;exit}' "$META")
  cap=$(awk -F'\t' -v e="$exp" '$1==e{print $6;exit}' "$META")
  exc_rm=$(awk -F'\t' -v e="$exp" '$1==e{print $7;exit}' "$META")
  exc_rsyn=$(awk -F'\t' -v e="$exp" '$1==e{print $8;exit}' "$META")
  echo "sync $exp"
  "$COPY" sync "$ROOT/$exp/Train" "$ROOT/$exp/Test"
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
            "InhSynapseResistance", "FixedLTZThreshold"):
    v = get_tag(train, tag)
    if v is not None:
        test = set_tag(test, tag, v, 0)
tp.write_text(test, encoding="utf-8")
PY
  verify_model "$ROOT/$exp/Test/Model_00.xml" "$neuron" "$kind" "$cap" "$exc_rm" "$exc_rsyn"
done

echo "=== TEST wave MAX_JOBS=$MAX_JOBS t=$TEST_T ==="
if ! run_wave test "$TEST_T"; then
  echo "Test wave had failures" >&2
  exit 1
fi

printf "exp,neuron,span_ms,kind,pack,acc,fn,fp,fires,mode,gate,target_hit,L,FixedLTZ\n" > "$OUT"
for exp in "${EXPS[@]}"; do
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  span=$(awk -F'\t' -v e="$exp" '$1==e{print $3;exit}' "$META")
  kind=$(awk -F'\t' -v e="$exp" '$1==e{print $4;exit}' "$META")
  pack=$(awk -F'\t' -v e="$exp" '$1==e{print $5;exit}' "$META")
  csv="$ROOT/$exp/Test/SelectivityLog/results.csv"
  params="$ROOT/$exp/Train/Parameters_00.xml"
  python3 - "$OUT" "$exp" "$neuron" "$span" "$kind" "$pack" "$csv" "$params" <<'PY'
import csv, re, sys
from pathlib import Path
out, exp, neuron, span, kind, pack, csv_path, params = sys.argv[1:9]
rows = []
p = Path(csv_path)
if p.exists():
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
acc = fn = fp = fires = 0
target_hit = 0
mode = "silent"
gate = 0
n = 0
if rows:
    for r in rows:
        fired = r.get("neuron_fired", "0") == "1"
        tgt = r.get("target_class", "0") == "1"
        match = r.get("match", "0") == "1"
        if match: acc += 1
        if fired: fires += 1
        if tgt and not fired: fn += 1
        if (not tgt) and fired: fp += 1
    if rows[0].get("target_class") == "1" and rows[0].get("neuron_fired") == "1" and rows[0].get("match", "0") == "1":
        target_hit = 1
    n = len(rows)
    fire_all = fires == n
    if fire_all: mode = "fire_all"
    elif target_hit and acc >= 4 and not fire_all: mode = "selective"
    elif target_hit: mode = "partial_FA"
    elif fires == 0: mode = "silent"
    else: mode = "miss_target"
    gate = 1 if (target_hit and (not fire_all) and acc >= 4) else 0
    acc_s = f"{acc}/{n}"
else:
    acc_s = "0/0"
pt = Path(params).read_text(encoding="utf-8")
Lm = re.search(r"<DendriteLength[^>]*>([^<]*)</DendriteLength>", pt)
L = Lm.group(1).strip() if Lm else ""
Fm = re.search(r"<FixedLTZThreshold[^>]*>([^<]*)</FixedLTZThreshold>", pt)
flt = Fm.group(1) if Fm else ""
with open(out, "a", encoding="utf-8") as f:
    f.write(f"{exp},{neuron},{span},{kind},{pack},{acc_s},{fn},{fp},{fires},{mode},{gate},{target_hit},{L},{flt}\n")
print(exp, acc_s, mode, "gate", gate)
PY
done
echo "Wrote $OUT"
cat "$OUT"

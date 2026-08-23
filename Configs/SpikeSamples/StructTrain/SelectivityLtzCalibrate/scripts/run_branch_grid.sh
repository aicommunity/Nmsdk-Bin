#!/usr/bin/env bash
# Train + sync + Test for BranchFastSpan (after regression PASS).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GRID="$ROOT/BranchFastSpan"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
COPY="$ROOT/scripts/copy_config_branch.sh"
META="$ROOT/grid_branch.tsv"
LOG="$ROOT/run_branch.log"
LTZ_TEST="$ROOT/scripts/patch_ltz_calibrate_test.py"
TRAIN_T="${TRAIN_T:-160}"
TEST_T="${TEST_T:-20}"

if [[ -f "$ROOT/REGRESSION.md" ]] && grep -q '\*\*FAIL\*\*' "$ROOT/REGRESSION.md"; then
  echo "Regression FAIL — branch grid blocked." >&2
  exit 1
fi

mapfile -t EXPS < <(awk -F'\t' 'NR>1{print $1}' "$META")

exec > >(tee "$LOG") 2>&1

if [[ "${SKIP_TRAIN:-0}" != "1" ]]; then
  for exp in "${EXPS[@]}"; do
    dir="$GRID/$exp/Train"
    echo "=== TRAIN $exp ==="
    (cd "$dir" && "$NM" -c Project.ini -s -t "$TRAIN_T" -x -S >run_console.log 2>&1) \
      || { echo "FAIL TRAIN $exp"; exit 1; }
  done
else
  echo "SKIP_TRAIN=1"
fi

for exp in "${EXPS[@]}"; do
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  echo "=== SYNC $exp ==="
  "$COPY" sync "$GRID/$exp/Train" "$GRID/$exp/Test"
  python3 "$LTZ_TEST" "$GRID/$exp/Test/Parameters_00.xml" --train "$GRID/$exp/Train/Parameters_00.xml"
  python3 - "$GRID/$exp/Test/Model_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
mp, neuron = Path(sys.argv[1]), sys.argv[2]
m = mp.read_text(encoding="utf-8")
m = re.sub(r'(<Neuron Class=")[^"]+(">)', rf'\g<1>{neuron}\2', m, count=1)
def set_tag(text, tag, value, count=0):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count or 0)
for tag, val in [("NeuronClassName", neuron), ("UseElementDefaults", "1"), ("MembraneCapacity", "2.5e-10"),
                 ("SynapseDissociationTC", "0.002"), ("StructureBuildMode", "1"), ("IsNeedToTrain", "0")]:
    m = set_tag(m, tag, val, 0)
mp.write_text(m, encoding="utf-8")
PY
  python3 - "$GRID/$exp/Test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
p, neuron = Path(sys.argv[1]), sys.argv[2]
t = p.read_text(encoding="utf-8")
def set_tag(text, tag, value, count=0):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count or 0)
for tag, val in [("NeuronClassName", neuron), ("UseElementDefaults", "1"), ("MembraneCapacity", "2.5e-10"),
                 ("SynapseDissociationTC", "0.002"), ("StructureBuildMode", "1"), ("IsNeedToTrain", "0")]:
    t = set_tag(t, tag, val, count=1 if tag == "NeuronClassName" else 0)
p.write_text(t, encoding="utf-8")
PY
done

for exp in "${EXPS[@]}"; do
  dir="$GRID/$exp/Test"
  echo "=== TEST $exp ==="
  rm -rf "$dir/SelectivityLog"
  set +e
  (cd "$dir" && "$NM" -c Project.ini -s -t "$TEST_T" -x >run_console.log 2>&1)
  rc=$?
  set -e
  if [[ $rc -ne 0 && ! -f "$dir/SelectivityLog/results.csv" ]]; then
    echo "FAIL TEST $exp (exit $rc)"
    exit 1
  fi
  if [[ -f "$dir/SelectivityLog/results.csv" ]]; then
    python3 - "$dir/SelectivityLog/results.csv" <<'PY'
import csv, sys
from pathlib import Path
rows=list(csv.DictReader(Path(sys.argv[1]).open()))
acc=sum(1 for r in rows if r.get('match')=='1')
fires=sum(1 for r in rows if r.get('neuron_fired')=='1')
print(f"  acc={acc}/{len(rows)} fires={fires}")
PY
  fi
done

echo "Branch grid run complete."

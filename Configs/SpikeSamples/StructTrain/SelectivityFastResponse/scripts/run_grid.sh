#!/usr/bin/env bash
# Train / sync / Test all FastResponse grid cells; write grid_summary.csv
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"
NM=/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole
META="$ROOT/grid_cells.tsv"
OUT="$ROOT/grid_summary.csv"
TRAIN_T="${TRAIN_T:-160}"
TEST_T="${TEST_T:-20}"

if [[ ! -f "$META" ]]; then
  echo "Missing $META — run setup_grid.sh first" >&2
  exit 1
fi

post_sync_patch_test() {
  local train="$1"
  local test="$2"
  local neuron="$3"
  python3 - "$train/Parameters_00.xml" "$test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
train = Path(sys.argv[1]).read_text(encoding="utf-8")
tp = Path(sys.argv[2])
test = tp.read_text(encoding="utf-8")
neuron = sys.argv[3]

def set_tag(text, tag, value, count=1):
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count)

def get_tag(text, tag):
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)
    return m.group(1) if m else None

test = set_tag(test, "NeuronClassName", neuron)
test = set_tag(test, "SyncTolerance", "0.01")
flt = get_tag(train, "FixedLTZThreshold")
if flt:
    test = set_tag(test, "FixedLTZThreshold", flt)
tp.write_text(test, encoding="utf-8")
PY
}

printf "exp,neuron_class,dissoc,capacity,train_ok,acc,fn,fp,L,FixedLTZ,soma_peak,t_peak,neuron_t_rel,delta_t_peak\n" > "$OUT"

CTRL_TPEAK=""

while IFS=$'\t' read -r exp neuron dissoc capacity; do
  [[ "$exp" == "exp" ]] && continue
  train="$ROOT/$exp/Train"
  test="$ROOT/$exp/Test"
  echo "========== $exp =========="
  echo "=== TRAIN $exp -t $TRAIN_T ==="
  "$NM" -c "$train/Project.ini" -s -t "$TRAIN_T" -x -S 2>&1 | tail -8 || true

  "$SCR" sync "$train" "$test"
  post_sync_patch_test "$train" "$test" "$neuron"

  echo "=== TEST $exp -t $TEST_T ==="
  "$NM" -c "$test/Project.ini" -s -t "$TEST_T" -x 2>&1 | tail -5 || true

  csv="$test/SelectivityLog/results.csv"
  python3 - "$OUT" "$exp" "$neuron" "$dissoc" "$capacity" "$csv" "$train/Parameters_00.xml" <<'PY'
import csv, re, sys
from pathlib import Path

out, exp, neuron, dissoc, capacity, csv_path, params = sys.argv[1:8]
rows = []
p = Path(csv_path)
if p.exists():
    rows = list(csv.DictReader(p.open(encoding="utf-8")))

train_ok = 0
acc = fn = fp = 0
soma_peak = ""
t_peak = ""
neuron_t_rel = ""
if rows:
    n = len(rows)
    for r in rows:
        fired = r.get("neuron_fired", "0") == "1"
        tgt = r.get("target_class", "0") == "1"
        match = r.get("match", "0") == "1"
        if match:
            acc += 1
        if tgt and not fired:
            fn += 1
        if (not tgt) and fired:
            fp += 1
    acc = f"{acc}/{n}"
    t0 = rows[0]
    if t0.get("target_class") == "1" and t0.get("neuron_fired") == "1":
        train_ok = 1
    soma_peak = t0.get("soma_amp_sum", "")
    neuron_t_rel = t0.get("neuron_t_rel", "")
    t_peak = neuron_t_rel

params_txt = Path(params).read_text(encoding="utf-8")
def get_tag(text, tag):
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)
    return m.group(1).replace(",", ".") if m else ""
L = get_tag(params_txt, "DendriteLength")
flt = get_tag(params_txt, "FixedLTZThreshold")

# delta filled later for ctrl baseline
delta = ""
line = f"{exp},{neuron},{dissoc},{capacity},{train_ok},{acc},{fn},{fp},{L},{flt},{soma_peak},{t_peak},{neuron_t_rel},{delta}\n"
Path(out).open("a", encoding="utf-8").write(line)
print(line.strip())
PY
done < "$META"

# fill delta_t_peak vs EXP00CtrlExp04
python3 - "$OUT" <<'PY'
import csv, sys
from pathlib import Path
p = Path(sys.argv[1])
rows = list(csv.DictReader(p.open(encoding="utf-8")))
ctrl = next((r for r in rows if r["exp"] == "EXP00CtrlExp04"), None)
base = None
if ctrl and ctrl.get("neuron_t_rel"):
    try:
        base = float(ctrl["neuron_t_rel"].replace(",", "."))
    except ValueError:
        base = None
for r in rows:
    if base is None or not r.get("neuron_t_rel"):
        r["delta_t_peak"] = ""
        continue
    try:
        r["delta_t_peak"] = f"{float(r['neuron_t_rel'].replace(',', '.')) - base:.6g}"
    except ValueError:
        r["delta_t_peak"] = ""
fieldnames = list(rows[0].keys()) if rows else []
with p.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)
print("Wrote", p)
PY

echo "Summary: $OUT"

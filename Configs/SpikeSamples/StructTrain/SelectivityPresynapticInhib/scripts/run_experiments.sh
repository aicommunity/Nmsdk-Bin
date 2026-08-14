#!/usr/bin/env bash
set -euo pipefail
NM=/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"
export PYTHONUNBUFFERED=1

accuracy() {
  python3 - <<PY
import csv
from pathlib import Path
p=Path("$1")
if not p.exists():
  print("missing")
else:
  rows=list(csv.DictReader(p.open()))
  ok=sum(1 for r in rows if r.get("match")=="1")
  print(f"{ok}/{len(rows)}")
PY
}

for exp in EXP00_baseline EXP01_preinh_050 EXP02_preinh_100 EXP03_preinh_200; do
  echo "=== TRAIN $exp ==="
  "$NM" -c "$ROOT/$exp/Train/Project.ini" -s -t 160 -x -S >"$ROOT/$exp/train.log" 2>&1 || true
  # show last useful lines
  rg -n 'TrainingPhase|phase=|Done|SaveProject|throws exception|Incomplete' "$ROOT/$exp/train.log" | tail -15 || tail -5 "$ROOT/$exp/train.log"
  "$SCR" sync "$ROOT/$exp/Train" "$ROOT/$exp/Test"
  neu=$(python3 - <<PY
import re
from pathlib import Path
t=Path("$ROOT/$exp/Train/Parameters_00.xml").read_text()
m=re.search(r'<NeuronClassName[^>]*>([^<]+)</NeuronClassName>', t)
print(m.group(1) if m else "NSPNeuronGen")
PY
)
  python3 "$ROOT/scripts/patch_neuron_class.py" "$ROOT/$exp/Test/Parameters_00.xml" "$neu"
  echo "=== TEST $exp (NeuronClass=$neu) ==="
  "$NM" -c "$ROOT/$exp/Test/Project.ini" -s -t 20 -x >"$ROOT/$exp/test.log" 2>&1 || true
  echo "$exp: $(accuracy "$ROOT/$exp/Test/SelectivityLog/results.csv")"
done

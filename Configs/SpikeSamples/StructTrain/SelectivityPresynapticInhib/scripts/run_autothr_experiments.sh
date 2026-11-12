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

calibrated_thr() {
  python3 - <<PY
import re
from pathlib import Path
t=Path("$1").read_text(encoding="utf-8")
for tag in ("CalibratedFixedLTZThreshold", "FixedLTZThreshold"):
  m=re.search(rf'<{tag} Type="d" PType="257" IoType="17">([^<]+)</{tag}>', t)
  if not m and tag=="CalibratedFixedLTZThreshold":
    m=re.search(rf'<{tag} Type="d" PType="[^"]*" IoType="[^"]*">([^<]+)</{tag}>', t)
  if m and float(m.group(1))>0:
    print(m.group(1)); break
else:
  m=re.search(r'<FixedLTZThreshold Type="d" PType="257" IoType="17">([^<]+)</FixedLTZThreshold>', t)
  print(m.group(1) if m else "?")
PY
}

for exp in EXP00_baseline_autothr EXP01_preinh_050_autothr EXP02_preinh_100_autothr EXP03_preinh_200_autothr; do
  echo "=== TRAIN $exp ==="
  "$NM" -c "$ROOT/$exp/Train/Project.ini" -s -t 160 -x -S >"$ROOT/$exp/train.log" 2>&1 || true
  rg -n 'CalibrateFixedLTZ|phase -> Done|SaveProject|throws exception' "$ROOT/$exp/train.log" | tail -10 || tail -5 "$ROOT/$exp/train.log"
  echo "Calibrated thr: $(calibrated_thr "$ROOT/$exp/Train/Parameters_00.xml")"
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
  echo "=== TEST $exp ==="
  "$NM" -c "$ROOT/$exp/Test/Project.ini" -s -t 20 -x >"$ROOT/$exp/test.log" 2>&1 || true
  echo "$exp: $(accuracy "$ROOT/$exp/Test/SelectivityLog/results.csv")"
done

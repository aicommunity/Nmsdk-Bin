#!/usr/bin/env bash
# Warm regression: golden trained Parameters → sync → test (validates sync pipeline §13.4).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REG="$ROOT/RegressionFull480"
PREINH="$ROOT/../SelectivityPresynapticInhib"
COPY="$ROOT/scripts/copy_config.sh"
META="$ROOT/grid_regression.tsv"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
TEST_T="${TEST_T:-20}"

mapfile -t EXPS < <(awk -F'\t' 'NR>1{print $1"\t"$4}' "$META")

for pair in "${EXPS[@]}"; do
  IFS=$'\t' read -r exp golden_exp <<<"$pair"
  echo "=== WARM restore $exp from $golden_exp ==="
  cp "$PREINH/${golden_exp}/Train/Parameters_00.xml" "$REG/$exp/Train/Parameters_00.xml"
  rsync -a --exclude='EventsLog' --exclude='StatisticLog' --exclude='History.xml' \
    --exclude='settings.qt' --exclude='SelectivityLog' \
    "$PREINH/${golden_exp}/Test/" "$REG/$exp/Test/"
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  sed -i "s|<ProjectName>[^<]*</ProjectName>|<ProjectName>${exp}_Test</ProjectName>|" "$REG/$exp/Test/Project.ini"
  python3 "$ROOT/scripts/patch_test_model.py" "$REG/$exp/Test/Model_00.xml"
  python3 - "$REG/$exp/Test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
pp, neuron = Path(sys.argv[1]), sys.argv[2]
def set_tag(text, tag, value, count=1):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count)
t = pp.read_text(encoding="utf-8")
t = set_tag(t, "NeuronClassName", neuron, 1)
t = set_tag(t, "IsNeedToTrain", "0", 1)
t = set_tag(t, "StructureBuildMode", "0", 1)
pp.write_text(t, encoding="utf-8")
PY
done

for pair in "${EXPS[@]}"; do
  IFS=$'\t' read -r exp _ <<<"$pair"
  echo "=== SYNC $exp ==="
  "$COPY" sync "$REG/$exp/Train" "$REG/$exp/Test"
  python3 "$ROOT/scripts/patch_ltz_calibrate_test.py" \
    "$REG/$exp/Test/Parameters_00.xml" --train "$REG/$exp/Train/Parameters_00.xml"
  neuron=$(awk -F'\t' -v e="$exp" '$1==e{print $2;exit}' "$META")
  python3 - "$REG/$exp/Test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
p, neuron = Path(sys.argv[1]), sys.argv[2]
t = p.read_text(encoding="utf-8")
t = re.sub(rf"(<NeuronClassName\b[^>]*>)[^<]*(</NeuronClassName>)", rf"\g<1>{neuron}\2", t, count=1)
p.write_text(t, encoding="utf-8")
PY
done

for pair in "${EXPS[@]}"; do
  IFS=$'\t' read -r exp _ <<<"$pair"
  dir="$REG/$exp/Test"
  ini=Project.ini
  [[ -f "$dir/project.ini" ]] && ini=project.ini
  echo "=== TEST $exp ==="
  rm -rf "$dir/SelectivityLog"
  set +e
  (cd "$dir" && "$NM" -c "$ini" -s -t "$TEST_T" -x >run_console.log 2>&1)
  rc=$?
  set -e
  if [[ $rc -ne 0 && ! -f "$dir/SelectivityLog/results.csv" ]]; then
    echo "FAIL TEST $exp (exit $rc, no results.csv)"
    exit 1
  fi
  if [[ $rc -ne 0 ]]; then
    echo "WARN TEST $exp: NM exit $rc but results.csv present"
  fi
done

python3 "$ROOT/scripts/verify_regression.py" --root "$ROOT" --mode warm
echo "Warm regression complete."

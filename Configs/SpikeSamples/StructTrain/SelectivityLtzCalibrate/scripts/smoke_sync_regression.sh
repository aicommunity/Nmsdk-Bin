#!/usr/bin/env bash
# Smoke sync: golden train Parameters + test Model → sync → test acc (no cold train).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PREINH="$ROOT/../SelectivityPresynapticInhib"
COPY="$ROOT/scripts/copy_config.sh"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
SMOKE="$ROOT/_smoke_sync"
TEST_T="${TEST_T:-20}"
fail=0

run_smoke() {
  local exp="$1" golden="$2" neuron="$3" min_acc="$4" expect_fires="$5"
  local train="$SMOKE/$exp/Train"
  local test="$SMOKE/$exp/Test"
  echo "=== smoke sync $exp ($golden) ==="
  rm -rf "$SMOKE/$exp"
  mkdir -p "$train" "$test"
  rsync -a --exclude='EventsLog' --exclude='StatisticLog' --exclude='History.xml' \
    --exclude='settings.qt' --exclude='SelectivityLog' \
    "$PREINH/${golden}/Train/" "$train/"
  rsync -a --exclude='EventsLog' --exclude='StatisticLog' --exclude='History.xml' \
    --exclude='settings.qt' --exclude='SelectivityLog' \
    "$PREINH/${golden}/Test/" "$test/"
  "$COPY" sync "$train" "$test"
  python3 "$ROOT/scripts/patch_ltz_calibrate_test.py" "$test/Parameters_00.xml" --train "$train/Parameters_00.xml"
  python3 - "$test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
p, neuron = Path(sys.argv[1]), sys.argv[2]
t = p.read_text(encoding="utf-8")
t = re.sub(rf"(<NeuronClassName\b[^>]*>)[^<]*(</NeuronClassName>)", rf"\g<1>{neuron}\2", t, count=1)
p.write_text(t, encoding="utf-8")
PY
  rm -rf "$test/SelectivityLog"
  (cd "$test" && "$NM" -c Project.ini -s -t "$TEST_T" -x >run_console.log 2>&1)
  csv="$test/SelectivityLog/results.csv"
  if [[ ! -f "$csv" ]]; then
    echo "FAIL $exp: no results.csv"
    fail=$((fail+1))
    return
  fi
  read -r acc fires <<<"$(python3 - "$csv" "$min_acc" "$expect_fires" <<'PY'
import csv, sys
from pathlib import Path
rows = list(csv.DictReader(Path(sys.argv[1]).open(encoding="utf-8")))
min_acc = int(sys.argv[2])
expect = sys.argv[3]
acc = sum(1 for r in rows if r.get("match") == "1")
fires = "".join("1" if r.get("neuron_fired") == "1" else "0" for r in rows)
print(acc, fires)
if acc < min_acc:
    raise SystemExit(1)
if fires == expect:
    pass
elif fires == "11111111":
    raise SystemExit(2)
PY
)"
  echo "OK $exp acc=${acc}/8 fires=$fires (min $min_acc, expect $expect_fires)"
}

run_smoke EXP00_smoke EXP00_baseline_margprops NSPNeuronGen 5 10101010 || fail=$((fail+1))
run_smoke EXP04_smoke EXP04_preinh_250_margprops NSPNeuronGenPreinh2_5 6 10001010 || fail=$((fail+1))

if (( fail > 0 )); then
  echo "Smoke sync FAIL ($fail)"
  exit 1
fi
echo "Smoke sync PASS (gen 5/8 + preinh 6/8)"

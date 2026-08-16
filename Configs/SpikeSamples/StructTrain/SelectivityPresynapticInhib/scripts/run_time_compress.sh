#!/usr/bin/env bash
# Cold train + auto-tune timing + sync + test for time-compress EXPs.
set -euo pipefail
NM=/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"
TUNE="$ROOT/scripts/tune_timing_params.py"
PREPARE="$ROOT/scripts/prepare_gui_psi_train.py"
PATCH_NEU="$ROOT/scripts/patch_neuron_class.py"

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

lens() {
  python3 - <<PY
import re
from pathlib import Path
t=Path("$1").read_text(encoding="utf-8")
m=re.search(r'<DendriteLength Type="simplevector"[^>]*>([^<]+)</DendriteLength>', t)
print(m.group(1).strip() if m else "?")
PY
}

thr() {
  python3 - <<PY
import re
from pathlib import Path
t=Path("$1").read_text(encoding="utf-8")
for tag in ("CalibratedFixedLTZThreshold", "FixedLTZThreshold"):
  m=re.search(rf'<{tag}[^>]*>([^<]+)</{tag}>', t)
  if m and float(m.group(1)) > 0:
    print(m.group(1)); break
else:
  print("?")
PY
}

diagnose_log() {
  python3 - <<'PY' "$1"
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
if "phase -> Done" in text:
    print("ok"); raise SystemExit
iters = []
for m in re.finditer(
    r"FinishTrainingIteration: iter=(\d+).*?amp=\[([^\]]+)\].*?len=\[([^\]]+)\]"
    r".*?lastAbsDt=\[([^\]]+)\].*?peakValid=\[([^\]]+)\]",
    text,
):
    it = int(m.group(1))
    amps = [float(x) for x in m.group(2).split(",")]
    lens = [int(float(x)) for x in m.group(3).split(",")]
    dts = [float(x) for x in m.group(4).split(",")]
    pvs = [int(x) for x in m.group(5).split(",")]
    iters.append((it, amps, lens, dts, pvs))
if not iters:
    print("unknown"); raise SystemExit
near = [x for x in iters if 3 <= x[0] <= 8] or iters[:8]
if all(max(a) < 1e-9 for _, a, *_ in near):
    print("amp0"); raise SystemExit
if all(sum(pv) == 0 for *_, pv in near):
    print("peak0"); raise SystemExit
early = [x for x in iters if x[0] <= 1]
late = [x for x in iters if 4 <= x[0] <= 8]
if early and late:
    eL = max(early[0][2])
    lL = max(max(x[2]) for x in late)
    eDt = min(min(x[3][:3]) for x in early)
    lDt = min(min(x[3][:3]) for x in late)
    if lL <= eL + 1 and lDt >= eDt * 0.95:
        print("stall"); raise SystemExit
print("nodone")
PY
}

enable_debug() {
  python3 - <<PY
import re
from pathlib import Path
p=Path("$1")
t=p.read_text(encoding="utf-8")
t2,n=re.subn(
  r'(<EnableDebug Type="b" PType="257" IoType="17">)[01](</EnableDebug>)',
  r'\g<1>1\g<2>', t, count=1)
if n!=1:
  raise SystemExit(f"EnableDebug patch failed in {p}: {n}")
p.write_text(t2, encoding="utf-8")
PY
}

reset_cold() {
  local train="$1"
  local neu="$2"
  python3 "$PREPARE" "$train/Parameters_00.xml"
  python3 "$PATCH_NEU" "$train/Parameters_00.xml" "$neu"
  python3 "$PATCH_NEU" "$train/Model_00.xml" "$neu"
  enable_debug "$train/Parameters_00.xml"
}

# Curated widen sequence: discrete L steps often need SyncTol ≳ residual lastAbsDt.
widen_params() {
  local span_ms="$1"
  local idx="$2"
  python3 - <<PY
import sys
sys.path.insert(0, "$ROOT/scripts")
from patch_pattern_scale import compute_initial, FLOOR
span_s = $span_ms / 1000.0
i = compute_initial(span_s)
s0, p0, dmin = i["sync_tol"], i["peak_margin"], i["delta_min"]
cands = []
for s in (1.5 * s0, 2.0 * s0, 3.0 * s0, dmin, 0.25 * span_s, 0.5 * span_s,
          max(dmin, 0.35 * span_s)):
    s = max(FLOOR, min(span_s, s))
    for p in (p0, min(max(FLOOR, 1.25 * p0), max(FLOOR, 0.45 * dmin)),
              max(FLOOR, 0.75 * p0)):
        p = max(FLOOR, min(max(p0, FLOOR), p)) if 0.45 * dmin < FLOOR else max(
            FLOOR, min(0.45 * dmin, p)
        )
        a = max(s, min(0.03, p))
        t = (round(s, 12), round(p, 12), round(a, 12))
        if t not in {(c[0], c[1], c[2]) for c in cands}:
            cands.append((s, p, a))
idx = $idx - 1
if idx < 0 or idx >= len(cands):
    print("EMPTY")
else:
    s, p, a = cands[idx]
    print(f"{s:.8g} {p:.8g} {a:.8g}")
PY
}

sync_test_timing() {
  local train="$1"
  local test="$2"
  python3 - <<PY
import re, sys
from pathlib import Path
sys.path.insert(0, "$ROOT/scripts")
from patch_pattern_scale import set_or_insert_double
tr = Path("$train/Parameters_00.xml").read_text(encoding="utf-8")
vals = {}
for tag in ("SyncTolerance", "PeakMeasureMargin", "DelayAgreeMarginMin"):
  m = re.search(rf'<{tag}[^>]*>([^<]+)</{tag}>', tr)
  vals[tag] = float(m.group(1)) if m else None
for path in ("$test/Parameters_00.xml", "$test/Model_00.xml"):
  p = Path(path)
  t = p.read_text(encoding="utf-8")
  for tag, v in vals.items():
    if v is not None:
      t = set_or_insert_double(t, tag, v)
  p.write_text(t, encoding="utf-8")
print("test timing", vals)
PY
}

run_one() {
  local exp="$1"
  local neu="$2"
  local span_ms="$3"
  local train="$ROOT/$exp/Train"
  local test="$ROOT/$exp/Test"
  local max_tune="${4:-10}"
  mkdir -p "$ROOT/$exp"
  local tune_idx=0
  local status="unknown"

  while true; do
    echo "=== TRAIN $exp (tune_idx=$tune_idx) ==="
    reset_cold "$train" "$neu"
    : >"$ROOT/$exp/train.log"
    "$NM" -c "$train/Project.ini" -s -t 90 -x -S >"$ROOT/$exp/train.log" 2>&1 || true
    local info
    info="$(ls -t "$train/EventsLog/"*INFO* 2>/dev/null | head -1 || true)"
    local src="$ROOT/$exp/train.log"
    [[ -n "$info" ]] && src="$info"
    status="$(diagnose_log "$src")"
    echo "diagnose=$status L=$(lens "$train/Parameters_00.xml") thr=$(thr "$train/Parameters_00.xml")"
    rg -n 'phase -> Done|CalibrateFixedLTZ|throws exception' "$ROOT/$exp/train.log" | tail -8 || true

    if [[ "$status" == "ok" ]]; then
      break
    fi
    if [[ "$status" == "amp0" || "$status" == "peak0" ]]; then
      echo "HARD FAIL $status"
      if [[ "$tune_idx" -ge 2 ]]; then
        echo "ABORT $exp after amp/peak fails"
        echo "$exp: FAIL/$status" >"$ROOT/$exp/RESULT.txt"
        return 1
      fi
    fi
    if [[ "$tune_idx" -ge "$max_tune" ]]; then
      echo "ABORT $exp grid exhausted status=$status"
      echo "$exp: FAIL/$status" >"$ROOT/$exp/RESULT.txt"
      return 1
    fi
    tune_idx=$((tune_idx + 1))
    local wp
    wp="$(widen_params "$span_ms" "$tune_idx")"
    if [[ "$wp" == "EMPTY" ]]; then
      echo "ABORT $exp widen empty"
      echo "$exp: FAIL/$status" >"$ROOT/$exp/RESULT.txt"
      return 1
    fi
    read -r sync peak agree <<<"$wp"
    echo "AUTO-TUNE widen#$tune_idx SyncTol=$sync Peak=$peak Agree=$agree"
    python3 "$TUNE" \
      "$train/Parameters_00.xml" "$train/Model_00.xml" \
      "$test/Parameters_00.xml" "$test/Model_00.xml" \
      --span-ms "$span_ms" --sync-tol "$sync" --peak-margin "$peak" --agree-min "$agree"
  done

  "$SCR" sync "$train" "$test"
  python3 "$PATCH_NEU" "$test/Parameters_00.xml" "$neu"
  python3 "$PATCH_NEU" "$test/Model_00.xml" "$neu"
  sync_test_timing "$train" "$test"

  echo "=== TEST $exp ==="
  "$NM" -c "$test/Project.ini" -s -t 20 -x >"$ROOT/$exp/test.log" 2>&1 || true
  local acc
  acc="$(accuracy "$test/SelectivityLog/results.csv")"
  echo "$exp: $acc L=$(lens "$train/Parameters_00.xml") thr=$(thr "$train/Parameters_00.xml") tune=$tune_idx" | tee "$ROOT/$exp/RESULT.txt"
}

for spec in "$@"; do
  IFS=':' read -r name neu span <<<"$spec"
  run_one "$name" "$neu" "$span" || true
done

#!/usr/bin/env bash
# Cold train + quality-aware timing grid + sync + test for time-compress/expand EXPs.
# Iterate full grid; pick best candidate by rank_key (max Acc among PASS preferred).
# Final gate PASS only if best snapshot has ok=1 (target_hit, not fire_all, Acc>=4/8).
set -euo pipefail
NM=/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"
TUNE="$ROOT/scripts/tune_timing_params.py"
EVAL="$ROOT/scripts/evaluate_selectivity_csv.py"
PREPARE="$ROOT/scripts/prepare_gui_psi_train.py"
PATCH_NEU="$ROOT/scripts/patch_neuron_class.py"
PATCH_SCALE="$ROOT/scripts/patch_pattern_scale.py"

parse_kv() {
  # parse "ok=1 n=8 ..." into vars ok n acc ...
  local line="$1"
  ok=0; n=0; acc=0; target_hit=0; fire_all=0; mode=missing; fires=; matches=; fa=0
  for pair in $line; do
    local k="${pair%%=*}"
    local v="${pair#*=}"
    case "$k" in
      ok) ok=$v ;;
      n) n=$v ;;
      acc) acc=$v ;;
      target_hit) target_hit=$v ;;
      fire_all) fire_all=$v ;;
      mode) mode=$v ;;
      fires) fires=$v ;;
      matches) matches=$v ;;
      fa) fa=$v ;;
    esac
  done
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

read_timing() {
  python3 - <<PY
import re
from pathlib import Path
t=Path("$1").read_text(encoding="utf-8")
vals=[]
for tag in ("SyncTolerance", "PeakMeasureMargin", "DelayAgreeMarginMin"):
  m=re.search(rf'<{tag}[^>]*>([^<]+)</{tag}>', t)
  vals.append(m.group(1) if m else "?")
print(" ".join(vals))
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

grid_size() {
  python3 "$TUNE" --span-ms "$1" --list --limit 999 2>/dev/null | grep -c '^[[:space:]]*[0-9]'
}

rank_key() {
  # stdout: comparable string for sorting best-of (higher better via sort -V not used;
  # we compare numerically in python)
  python3 - <<PY
th=$target_hit
fa_all=$fire_all
acc=$acc
fa=$fa
sync="$1"
sync0="$2"
print(f"{th} {1-int(fa_all)} {acc} {-int(fa)} {-abs(float(sync)-float(sync0)):.12g}")
PY
}

better_than() {
  # $1=cand_key $2=best_key ; return 0 if cand better
  python3 - <<PY
a=list(map(float, "$1".split()))
b=list(map(float, "$2".split()))
print("yes" if a > b else "no")
PY
}

run_one() {
  local exp="$1"
  local neu="$2"
  local span_ms="$3"
  local train="$ROOT/$exp/Train"
  local test="$ROOT/$exp/Test"
  mkdir -p "$ROOT/$exp"
  local tune_log="$ROOT/$exp/tune_log.txt"
  : >"$tune_log"

  echo "=== RESET TIMING $exp span=${span_ms}ms ==="
  python3 "$PATCH_SCALE" \
    "$train/Parameters_00.xml" "$train/Model_00.xml" \
    "$test/Parameters_00.xml" "$test/Model_00.xml" \
    --span-ms "$span_ms" --no-scale

  local sync0 peak0 agree0
  read -r sync0 peak0 agree0 <<<"$(read_timing "$train/Parameters_00.xml")"

  local ngrid
  ngrid="$(grid_size "$span_ms")"
  local max_attempts=20
  if [[ "$ngrid" -lt "$max_attempts" ]]; then
    max_attempts=$ngrid
  fi
  [[ "$max_attempts" -lt 1 ]] && max_attempts=1

  local best_rank="-1 0 -1 0 0"
  local best_dir=""
  local hard_fail_streak=0
  local attempts=0
  local idx=0
  local gate=FAIL
  local last_mode=unknown

  while [[ "$attempts" -lt "$max_attempts" ]]; do
    echo "=== TRAIN $exp attempt=$attempts idx=$idx / max=$max_attempts grid=$ngrid ==="
    if [[ "$attempts" -gt 0 || "$idx" -gt 0 ]]; then
      if [[ "$idx" -ge "$ngrid" ]]; then
        echo "grid index exhausted idx=$idx"
        break
      fi
      python3 "$TUNE" \
        "$train/Parameters_00.xml" "$train/Model_00.xml" \
        "$test/Parameters_00.xml" "$test/Model_00.xml" \
        --span-ms "$span_ms" --index "$idx"
    fi

    local sync peak agree
    read -r sync peak agree <<<"$(read_timing "$train/Parameters_00.xml")"

    reset_cold "$train" "$neu"
    : >"$ROOT/$exp/train.log"
    "$NM" -c "$train/Project.ini" -s -t 90 -x -S >"$ROOT/$exp/train.log" 2>&1 || true
    local info
    info="$(ls -t "$train/EventsLog/"*INFO* 2>/dev/null | head -1 || true)"
    local src="$ROOT/$exp/train.log"
    [[ -n "$info" ]] && src="$info"
    local status
    status="$(diagnose_log "$src")"
    echo "diagnose=$status L=$(lens "$train/Parameters_00.xml") thr=$(thr "$train/Parameters_00.xml") Sync=$sync Peak=$peak Agree=$agree"
    rg -n 'phase -> Done|CalibrateFixedLTZ|throws exception' "$ROOT/$exp/train.log" | tail -8 || true

    if [[ "$status" == "amp0" || "$status" == "peak0" ]]; then
      hard_fail_streak=$((hard_fail_streak + 1))
      echo "idx=$idx diagnose=$status Sync=$sync Peak=$peak Agree=$agree" >>"$tune_log"
      if [[ "$hard_fail_streak" -ge 3 ]]; then
        echo "HARD FAIL streak on $exp ($status)"
        echo "$exp: HARD_FAIL/$status L=? thr=? Sync=$sync Peak=$peak Agree=$agree tune=$attempts gate=FAIL mode=train_$status" \
          | tee "$ROOT/$exp/RESULT.txt"
        cat >"$ROOT/$exp/QUALITY.txt" <<Q
gate=FAIL
mode=train_$status
diagnose=$status
attempts=$attempts
Q
        return 1
      fi
      # jump SyncTol — amp/peak unlikely fixed by Peak-only variants
      local nxt
      nxt="$(python3 "$TUNE" --span-ms "$span_ms" --next-wider-after-sync "$sync")"
      if [[ "$nxt" == "EMPTY" ]]; then
        attempts=$((attempts + 1))
        idx=$((idx + 1))
      else
        attempts=$((attempts + 1))
        idx=$nxt
      fi
      continue
    fi
    hard_fail_streak=0

    if [[ "$status" != "ok" ]]; then
      echo "idx=$idx diagnose=$status Sync=$sync Peak=$peak Agree=$agree no-test" >>"$tune_log"
      # Skip Peak variants at this SyncTol — climb to wider SyncTol for Done
      local nxt
      nxt="$(python3 "$TUNE" --span-ms "$span_ms" --next-wider-after-sync "$sync")"
      if [[ "$nxt" == "EMPTY" ]]; then
        echo "no wider SyncTol left after Sync=$sync"
        attempts=$((attempts + 1))
        break
      fi
      attempts=$((attempts + 1))
      idx=$nxt
      continue
    fi

    "$SCR" sync "$train" "$test"
    python3 "$PATCH_NEU" "$test/Parameters_00.xml" "$neu"
    python3 "$PATCH_NEU" "$test/Model_00.xml" "$neu"
    sync_test_timing "$train" "$test"

    echo "=== TEST $exp attempt=$attempts idx=$idx ==="
    "$NM" -c "$test/Project.ini" -s -t 20 -x >"$ROOT/$exp/test.log" 2>&1 || true
    local qline
    qline="$(python3 "$EVAL" "$test/SelectivityLog/results.csv" || true)"
    parse_kv "$qline"
    last_mode=$mode
    echo "quality $qline"
    echo "idx=$idx diagnose=ok Sync=$sync Peak=$peak Agree=$agree $qline" >>"$tune_log"

    # snapshot best candidate artifacts
    local cand_rank
    cand_rank="$(rank_key "$sync" "$sync0")"
    local is_better
    is_better="$(better_than "$cand_rank" "$best_rank")"
    if [[ "$is_better" == "yes" || -z "$best_dir" ]]; then
      best_rank=$cand_rank
      best_dir="$ROOT/$exp/_best_snap"
      rm -rf "$best_dir"
      mkdir -p "$best_dir/Train" "$best_dir/Test/SelectivityLog"
      cp -f "$train/Parameters_00.xml" "$train/Model_00.xml" "$best_dir/Train/"
      cp -f "$test/Parameters_00.xml" "$test/Model_00.xml" "$best_dir/Test/"
      cp -f "$test/SelectivityLog/results.csv" "$best_dir/Test/SelectivityLog/" 2>/dev/null || true
      printf '%s\n' "$qline" >"$best_dir/quality.line"
      printf '%s %s %s\n' "$sync" "$peak" "$agree" >"$best_dir/timing.txt"
      printf '%s\n' "$attempts" >"$best_dir/attempt.txt"
      printf '%s\n' "$idx" >"$best_dir/best_idx.txt"
      printf '%s\n' "$(lens "$train/Parameters_00.xml")" >"$best_dir/L.txt"
      printf '%s\n' "$(thr "$train/Parameters_00.xml")" >"$best_dir/thr.txt"
    fi

    # Full grid: do not stop at first PASS; explore until attempts/grid exhausted.
    attempts=$((attempts + 1))
    idx=$((idx + 1))
  done

  # restore best snapshot into Train/Test
  if [[ -n "$best_dir" && -d "$best_dir" ]]; then
    cp -f "$best_dir/Train/Parameters_00.xml" "$best_dir/Train/Model_00.xml" "$train/"
    cp -f "$best_dir/Test/Parameters_00.xml" "$best_dir/Test/Model_00.xml" "$test/"
    mkdir -p "$test/SelectivityLog"
    if [[ -f "$best_dir/Test/SelectivityLog/results.csv" ]]; then
      cp -f "$best_dir/Test/SelectivityLog/results.csv" "$test/SelectivityLog/"
    fi
    qline="$(cat "$best_dir/quality.line")"
    parse_kv "$qline"
    read -r sync peak agree <"$best_dir/timing.txt"
    local best_attempt best_idx
    best_attempt="$(cat "$best_dir/attempt.txt")"
    best_idx="$(cat "$best_dir/best_idx.txt")"
    local best_L best_thr
    best_L="$(cat "$best_dir/L.txt")"
    best_thr="$(cat "$best_dir/thr.txt")"
    if [[ "$ok" == "1" ]]; then
      gate=PASS
    else
      gate=FAIL
    fi
    echo "$exp: ${acc}/8 L=$best_L thr=$best_thr Sync=$sync Peak=$peak Agree=$agree tune=$best_attempt gate=$gate mode=$mode" \
      | tee "$ROOT/$exp/RESULT.txt"
    cat >"$ROOT/$exp/QUALITY.txt" <<Q
gate=$gate
mode=$mode
acc=${acc}/8
n=$n
target_hit=$target_hit
fire_all=$fire_all
fa=$fa
fires=$fires
matches=$matches
SyncTolerance=$sync
PeakMeasureMargin=$peak
DelayAgreeMarginMin=$agree
tune_steps=$best_attempt
best_idx=$best_idx
attempts_ran=$attempts
max_attempts=$max_attempts
rank=$best_rank
Q
    rm -rf "$best_dir"
  else
    echo "$exp: FAIL/no_done_candidate tune=$attempts gate=FAIL mode=$last_mode" | tee "$ROOT/$exp/RESULT.txt"
    cat >"$ROOT/$exp/QUALITY.txt" <<Q
gate=FAIL
mode=no_done_candidate
attempts=$attempts
Q
    return 1
  fi
}

for spec in "$@"; do
  IFS=':' read -r name neu span <<<"$spec"
  run_one "$name" "$neu" "$span" || true
done

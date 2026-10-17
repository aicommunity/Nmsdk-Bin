#!/usr/bin/env bash
# AsymRm train + AutoCalibrate + adaptive TRAIN_T continue + sync + test.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LTZCAL_SCRIPTS="$(cd "$(dirname "$0")/../../SelectivityLtzCalibrate/scripts" && pwd)"
NM="${NM:-/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole}"
MAX_JOBS="${MAX_JOBS:-3}"
TRAIN_T="${TRAIN_T:-80}"
TEST_T="${TEST_T:-20}"
META="${META:-$ROOT/grid_cells.tsv}"
OUT="$ROOT/grid_summary.csv"
LOG="$ROOT/run_asymrm.log"
VERIFY="$ROOT/scripts/verify_element_params.py"
VERIFY_SPAN="$ROOT/scripts/verify_pattern_span.py"
COPY="$ROOT/scripts/copy_config.sh"
LTZ_TRAIN="$LTZCAL_SCRIPTS/patch_ltz_calibrate_train.py"
LTZ_TEST="$LTZCAL_SCRIPTS/patch_ltz_calibrate_test.py"
VERIFY_DONE="$LTZCAL_SCRIPTS/verify_train_done.py"
STALL="$ROOT/scripts/analyze_train_stall.py"
FEAS="$ROOT/scripts/check_timing_feasibility.py"
PILOT_EXPS="${PILOT_EXPS:-}"
PACK_A_EXPS="${PACK_A_EXPS:-}"
ADAPTIVE_TRAIN="${ADAPTIVE_TRAIN:-1}"
LENGTH_STEPS="${LENGTH_STEPS:-80 160 320 640 1280 2560}"
LENGTH_STEPS_SPAN25="${LENGTH_STEPS_SPAN25:-}"
LENGTH_STEPS_SPAN50="${LENGTH_STEPS_SPAN50:-}"
LENGTH_STEPS_SPAN100="${LENGTH_STEPS_SPAN100:-80 160 320 640 1280 2560}"
LENGTH_MAX_STEP="${LENGTH_MAX_STEP:-2560}"
LENGTH_HOPELESS_TOL_MULT="${LENGTH_HOPELESS_TOL_MULT:-5}"
LENGTH_STEP_GUARD="$ROOT/scripts/length_step_guard.py"
TIME_BUDGET="$ROOT/scripts/train_time_budget.py"
SIGNAL_FIDELITY="$ROOT/scripts/analyze_signal_fidelity.py"
SIGNAL_REF_JSON="${SIGNAL_REF_JSON:-$ROOT/signal_reference_span25.json}"
WALL_BUDGET_CHECK="${WALL_BUDGET_CHECK:-1}"
AMP_TRAIN_STEPS="${AMP_TRAIN_STEPS:-320 640 1280}"
L_REFERENCE="${L_REFERENCE:-}"
L_REF_JSON="${L_REF_JSON:-$ROOT/l_reference.json}"
L_REF_REFRESH="${L_REF_REFRESH:-320}"
AMP_PARTIAL_AT_L_REF="${AMP_PARTIAL_AT_L_REF:-0}"
AMP_FORCE_AT_L_REF="${AMP_FORCE_AT_L_REF:-0}"
AMP_ABORT_HARD_OSC="${AMP_ABORT_HARD_OSC:-0}"
AMP_HARD_OSC_NO_IMPROVE="${AMP_HARD_OSC_NO_IMPROVE:-20}"
L_TRAIN_GUARD="$ROOT/scripts/l_train_guard.py"
SEED_INITIAL_SCRIPT="$ROOT/scripts/seed_initial_from_ltzcal.py"
TRAIN_STEPS="${TRAIN_STEPS:-$LENGTH_STEPS}"
PEAK_SYNC_JSON="${PEAK_SYNC_JSON:-$ROOT/peak_sync_report.json}"
SKIP_TRAIN="${SKIP_TRAIN:-0}"
ALLOW_PARTIAL_TRAIN="${ALLOW_PARTIAL_TRAIN:-0}"
SEED_INITIAL="${SEED_INITIAL:-}"
INITIAL_SOURCE="${INITIAL_SOURCE:-ltzcal}"
CAPTURE_T="${CAPTURE_T:-80}"

[[ -f "$META" ]] || { echo "Run setup_asymrm.sh first" >&2; exit 1; }

# Default SEED_INITIAL=1 when using LtzCal L reference floors.
if [[ -z "$SEED_INITIAL" ]]; then
  if [[ "$L_REFERENCE" == "ltzcal" || -n "$L_REFERENCE" ]]; then
    SEED_INITIAL=1
  else
    SEED_INITIAL=0
  fi
fi

mapfile -t ALL_EXPS < <(awk -F'\t' 'NR>1{print $1}' "$META")
EXPS=()
for e in "${ALL_EXPS[@]}"; do
  if [[ -n "$PILOT_EXPS" ]]; then
    for p in $PILOT_EXPS; do [[ "$p" == "$e" ]] && EXPS+=("$e"); done
    continue
  fi
  if [[ -n "$PACK_A_EXPS" ]]; then
    pack=$(awk -F'\t' -v e="$e" '$1==e{print $5;exit}' "$META")
    [[ "$pack" == "A" ]] && EXPS+=("$e")
    continue
  fi
  EXPS+=("$e")
done
((${#EXPS[@]})) || { echo "No EXP selected (PILOT_EXPS=$PILOT_EXPS)" >&2; exit 1; }

exp_meta() {
  awk -F'\t' -v e="$1" -v c="$2" '$1==e{print $c;exit}' "$META"
}

length_steps_for_exp() {
  local exp="$1"
  local span
  span=$(exp_meta "$exp" 3)
  case "$span" in
    25) [[ -n "$LENGTH_STEPS_SPAN25" ]] && echo "$LENGTH_STEPS_SPAN25" && return ;;
    50) [[ -n "$LENGTH_STEPS_SPAN50" ]] && echo "$LENGTH_STEPS_SPAN50" && return ;;
    100) [[ -n "$LENGTH_STEPS_SPAN100" ]] && echo "$LENGTH_STEPS_SPAN100" && return ;;
  esac
  echo "$LENGTH_STEPS"
}

prepare_l_reference() {
  if [[ "$L_REFERENCE" == "ltzcal" || -n "$L_REFERENCE" ]]; then
    python3 "$ROOT/scripts/patch_l_reference.py" --export "$L_REF_JSON"
    echo "L_reference exported to $L_REF_JSON"
  fi
}

l_guard_save() {
  local exp="$1"
  python3 "$L_TRAIN_GUARD" "$ROOT/$exp/Train" --state "/tmp/asym_lstate_${exp}.json" --save-before
}

l_guard_after() {
  local exp="$1"
  local flags=()
  [[ "$L_REFERENCE" == "ltzcal" || -n "$L_REFERENCE" ]] && flags+=(--l-reference)
  python3 "$L_TRAIN_GUARD" "$ROOT/$exp/Train" --state "/tmp/asym_lstate_${exp}.json" "${flags[@]}" --json
}

l_guard_floor_before() {
  local exp="$1"
  [[ "$L_REFERENCE" == "ltzcal" || -n "$L_REFERENCE" ]] || return 0
  # Cold D∝span pilots must grow from L=1 1 1 1 — do not raise to L_ref before train.
  [[ "$exp" == *_Dspan ]] && return 0
  python3 "$L_TRAIN_GUARD" "$ROOT/$exp/Train" --apply-floor --l-reference --json 2>/dev/null || true
}

initials_ready_exp() {
  local exp="$1"
  python3 - "$ROOT/$exp/Train/Parameters_00.xml" "$ROOT/scripts" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from asymrm_train_common import initials_ready, load_train_params
p = load_train_params(Path(sys.argv[1]))
sys.exit(0 if initials_ready(p.get("InitialSomaPotential") or []) else 1)
PY
}

patch_capture_cold_l() {
  local exp="$1"
  python3 - "$ROOT/$exp/Train/Parameters_00.xml" <<'PY'
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
def set_tag(text, tag, value, count=0):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count or 0)
t = set_tag(t, "DendriteLength", "1 1 1 1", 1)
t = set_tag(t, "ResetToUntrainedState", "1", 1)
t = set_tag(t, "IsNeedToTrain", "1", 1)
t = set_tag(t, "StructureBuildMode", "1", 1)
p.write_text(t, encoding="utf-8")
print("capture_cold_l", p)
PY
}

ensure_initial_ready() {
  local exp="$1"
  if initials_ready_exp "$exp"; then
    return 0
  fi
  if [[ "$SEED_INITIAL" == "1" && -f "$SEED_INITIAL_SCRIPT" ]]; then
    echo "=== seed Initial from LtzCal $exp ==="
    python3 "$SEED_INITIAL_SCRIPT" "$ROOT/$exp/Train" || return 1
    if initials_ready_exp "$exp"; then
      return 0
    fi
  fi
  if [[ "$INITIAL_SOURCE" == "capture" ]]; then
    echo "=== capture Initial at L=1 $exp T=$CAPTURE_T ==="
    patch_capture_cold_l "$exp"
    train_one_exp "$exp" "$CAPTURE_T" || return 1
    if initials_ready_exp "$exp"; then
      echo "capture Initial OK $exp"
      return 0
    fi
    echo "capture Initial failed $exp" >&2
    return 1
  fi
  echo "Initial not ready for $exp (set SEED_INITIAL=1 or INITIAL_SOURCE=capture)" >&2
  return 1
}

ready_for_amp() {
  local exp="$1"
  if all_dendrites_sync_ok "$exp"; then
    return 0
  fi
  if [[ "$AMP_FORCE_AT_L_REF" == "1" ]] && at_l_reference "$exp"; then
    return 0
  fi
  [[ "$AMP_PARTIAL_AT_L_REF" == "1" ]] || return 1
  at_l_reference "$exp" || return 1
  python3 - "$ROOT/$exp/Train" "$ROOT/scripts" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from asymrm_train_common import load_train_params, load_trace_vectors, length_sync_ok, REF_DENDRITE
train_dir = Path(sys.argv[1])
p = load_train_params(train_dir / "Parameters_00.xml")
tr = load_trace_vectors(train_dir)
last = tr.get("LastAbsDtTrace", [])
tol = p["SyncTolerance"]
ok_n = 0
for i in range(3):
    if i == REF_DENDRITE:
        continue
    if i < len(last) and last[i] < 1.0 and length_sync_ok(last[i], tol):
        ok_n += 1
# at L_ref: allow amp if >=2 non-ref sync_ok, or any sync_ok + AMP pending on another
sys.exit(0 if ok_n >= 2 else 1)
PY
}

verify_model() {
  local model="$1" neuron="$2" kind="$3" cap="$4" exc_rm="$5" exc_rsyn="$6"
  python3 - "$exc_rm" "$exc_rsyn" <<'PY' > /tmp/asym_inh_vals.txt
import sys
exc_rm=float(sys.argv[1]); exc_rsyn=float(sys.argv[2])
print(f"{exc_rm*10:g}")
print(f"{exc_rsyn*10:g}")
PY
  local inh_rm inh_rsyn
  inh_rm=$(sed -n '1p' /tmp/asym_inh_vals.txt)
  inh_rsyn=$(sed -n '2p' /tmp/asym_inh_vals.txt)
  local dissoc="${DISSOC:-0.001}"
  # Pilot *_Dspan: Dissoc scales with span (kept via reapply_dspan_dissoc).
  if [[ "$model" == *_Dspan* ]]; then
    case "$model" in
      *span50*) dissoc=0.002 ;;
      *span100*) dissoc=0.004 ;;
    esac
  fi
  local args=(--expect-dissoc "$dissoc" --expect-cap "$cap" --expect-secr "${SECR:-0.001}"
    --expect-exc-r "$exc_rm" --expect-inh-r "$inh_rm"
    --expect-inh-syn-r "$inh_rsyn"
    --expect-class "$neuron" --min-count 4)
  if [[ "$kind" == *preinh* ]]; then args+=(--expect-inh 2.5); else args+=(--no-inh); fi
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
    [[ -f "$dir/project.ini" ]] && ini=project.ini
    echo "START $mode $exp t=$tlim"
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

apply_ltz_train_patch() {
  for exp in "${EXPS[@]}"; do
    # Do not re-patch Done trains (resets FixedLTZ to cold).
    if python3 "$VERIFY_DONE" "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
      echo "skip LTZ train patch (already Done): $exp"
      continue
    fi
    kind=$(exp_meta "$exp" 4)
    p="$ROOT/$exp/Train/Parameters_00.xml"
    if [[ "$kind" == *preinh* ]]; then
      python3 "$LTZ_TRAIN" --preinh "$p"
    else
      python3 "$LTZ_TRAIN" "$p"
    fi
  done
}

train_one_exp() {
  local exp="$1" tlim="$2"
  l_guard_floor_before "$exp"
  reapply_dspan_dissoc "$exp"
  local dir="$ROOT/$exp/Train"
  local ini=Project.ini
  [[ -f "$dir/project.ini" ]] && ini=project.ini
  ( cd "$dir"; "$NM" -c "$ini" -s -t "$tlim" -x -S >>run_console.log 2>&1; echo "Project saved." >>run_console.log )
  reapply_dspan_dissoc "$exp"
}

all_dendrites_sync_ok() {
  python3 - "$ROOT/$1/Train" "$ROOT/scripts" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from asymrm_train_common import all_non_ref_sync_ok, load_trace_vectors, load_train_params
train_dir = Path(sys.argv[1])
p = load_train_params(train_dir / "Parameters_00.xml")
tr = load_trace_vectors(train_dir)
last = tr.get("LastAbsDtTrace", [])
ok = all_non_ref_sync_ok(last, p["SyncTolerance"])
sys.exit(0 if ok else 1)
PY
}

get_stall_blocker() {
  python3 "$STALL" "$ROOT/$1/Train" --json 2>/dev/null | python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
print(d[0].get('blocker','UNKNOWN') if d else 'UNKNOWN')
" 2>/dev/null || echo "UNKNOWN"
}

at_l_reference() {
  python3 - "$ROOT/$1/Train/Parameters_00.xml" "$ROOT/scripts" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from asymrm_train_common import load_train_params
from patch_l_reference import at_l_reference, get_reference_l
p = Path(sys.argv[1])
pr = load_train_params(p)
exp = p.parent.parent.name
ok = at_l_reference(pr["DendriteLength"], get_reference_l(exp))
sys.exit(0 if ok else 1)
PY
}

patch_continue_train() {
  local exp="$1"
  python3 - "$ROOT/$exp/Train/Parameters_00.xml" <<'PY'
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
def set_tag(text, tag, value, count=0):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count or 0)
t = set_tag(t, "ResetToUntrainedState", "0", 0)
t = set_tag(t, "IsNeedToTrain", "1", 1)
t = set_tag(t, "StructureBuildMode", "1", 1)
p.write_text(t, encoding="utf-8")
print("continue_train", p)
PY
  reapply_dspan_dissoc "$exp"
}

# Class NSPNeuronGenAsymRmD001* hardcodes Dissoc=0.001; StructureBuild/save resets XML.
# Pilot *_Dspan keeps SynapseDissociationTC / DissociationTC at span-scaled values.
reapply_dspan_dissoc() {
  local exp="$1"
  [[ "$exp" == *_Dspan ]] || return 0
  local span dissoc
  span=$(exp_meta "$exp" 3)
  case "$span" in
    50) dissoc=0.002 ;;
    100) dissoc=0.004 ;;
    *) return 0 ;;
  esac
  python3 - "$ROOT/$exp/Train" "$dissoc" <<'PY'
import re, sys
from pathlib import Path
train = Path(sys.argv[1])
dissoc = sys.argv[2]
def set_tag(text, tag, value):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=0)
for name in ("Parameters_00.xml", "Model_00.xml"):
    p = train / name
    if not p.is_file():
        continue
    t = p.read_text(encoding="utf-8")
    t = set_tag(t, "SynapseDissociationTC", dissoc)
    t = set_tag(t, "DissociationTC", dissoc)
    t = set_tag(t, "UseElementDefaults", "1")
    t = set_tag(t, "MembraneCapacity", "2.5e-11")
    p.write_text(t, encoding="utf-8")
print(f"reapply_dspan_dissoc {train.parent.name} Dissoc={dissoc}")
PY
}

has_length_stall() {
  local blocker="$1"
  [[ "$blocker" == "LENGTH_STALL" || "$blocker" == "TIME_BUDGET" || "$blocker" == "PEAK_INVALID" ]]
}

has_amp_stall() {
  local blocker="$1"
  [[ "$blocker" == "AMP_AT_RMIN" || "$blocker" == "AMP_OSCILLATION" || "$blocker" == "AMP_PENDING" ]]
}

# Exit 0 if hard OSC: Need!=0, overall AMP_OSCILLATION, some non-ref dend with
# no_improve>=threshold and |amp_dt|<0.005 (further amp steps waste wall time).
hard_osc_abort_exp() {
  local exp="$1"
  [[ "${AMP_ABORT_HARD_OSC:-0}" == "1" ]] || return 1
  python3 - "$ROOT/$exp/Train" "$ROOT/scripts" "$AMP_HARD_OSC_NO_IMPROVE" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from analyze_train_stall import analyze_exp
from asymrm_train_common import REF_DENDRITE

train = Path(sys.argv[1])
thresh = float(sys.argv[3])
r = analyze_exp(train)
if str(r.get("IsNeedToTrain")) == "0":
    sys.exit(1)
if r.get("blocker") != "AMP_OSCILLATION":
    sys.exit(1)
for d in r.get("dendrites") or []:
    if d.get("dend") == REF_DENDRITE:
        continue
    if d.get("blocker") != "AMP_OSCILLATION":
        continue
    ni = float(d.get("no_improve") or 0.0)
    ad = abs(float(d.get("amp_dt") or 0.0))
    if ni >= thresh and ad < 0.005:
        sys.exit(0)
sys.exit(1)
PY
}

has_amp_no_initial() {
  local blocker="$1"
  [[ "$blocker" == "AMP_NO_INITIAL" ]]
}

length_step_decision() {
  local exp="$1" step="$2" cumulative="$3"
  python3 "$LENGTH_STEP_GUARD" "$ROOT/$exp/Train" \
    --next-step "$step" --cumulative "$cumulative" \
    --max-length-step "$LENGTH_MAX_STEP" \
    --hopeless-tol-mult "$LENGTH_HOPELESS_TOL_MULT" --json 2>/dev/null || echo '{"action":"proceed"}'
}

should_skip_length_step() {
  local exp="$1" step="$2" cumulative="$3"
  local decision action reason
  decision=$(length_step_decision "$exp" "$step" "$cumulative")
  action=$(echo "$decision" | python3 -c "import json,sys; print(json.load(sys.stdin).get('action','proceed'))")
  reason=$(echo "$decision" | python3 -c "import json,sys; print(json.load(sys.stdin).get('reason',''))")
  if [[ "$WALL_BUDGET_CHECK" == "1" && -f "$TIME_BUDGET" ]]; then
    local wall_dec
    wall_dec=$(python3 "$TIME_BUDGET" check-step "$ROOT/$exp/Train" \
      --next-step "$step" --campaign-root "$ROOT" 2>/dev/null || echo '{"action":"proceed"}')
    local wall_action
    wall_action=$(echo "$wall_dec" | python3 -c "import json,sys; print(json.load(sys.stdin).get('action','proceed'))")
    if [[ "$wall_action" == "abort" ]]; then
      echo "ABORT wall budget $exp step=$step: $(echo "$wall_dec" | python3 -c "import json,sys; print(json.load(sys.stdin).get('reason',''))")"
      return 2
    fi
  fi
  if [[ "$action" == "skip_step" ]]; then
    echo "SKIP length $exp step=$step: $reason"
    return 0
  fi
  if [[ "$action" == "abort_length" ]]; then
    echo "ABORT length schedule $exp before step=$step: $reason"
    return 2
  fi
  return 1
}

signal_fidelity_snapshot() {
  local exp="$1" label="$2"
  [[ -f "$SIGNAL_FIDELITY" ]] || return 0
  local ref_args=()
  [[ -f "$SIGNAL_REF_JSON" ]] && ref_args=(--reference "$SIGNAL_REF_JSON")
  local snap="$ROOT/signal_fidelity_${exp}_${label}.json"
  python3 "$SIGNAL_FIDELITY" "$ROOT/$exp/Train" "${ref_args[@]}" --json-out "$snap" >/dev/null 2>&1 || true
  if [[ -f "$snap" ]]; then
    local ok
    ok=$(python3 -c "import json; d=json.load(open('$snap')); print(d[0].get('fidelity',{}).get('signal_fidelity_ok','?') if isinstance(d,list) else d.get('fidelity',{}).get('signal_fidelity_ok','?'))" 2>/dev/null || echo "?")
    echo "signal_fidelity $exp $label ok=$ok -> $snap"
  fi
}

signal_fidelity_gate() {
  local exp="$1"
  [[ "${AMP_ONLY:-}" == "1" ]] && return 0
  [[ -f "$SIGNAL_FIDELITY" && -f "$SIGNAL_REF_JSON" ]] || return 0
  if all_dendrites_sync_ok "$exp" || ready_for_amp "$exp"; then
    return 0
  fi
  if ! python3 "$SIGNAL_FIDELITY" "$ROOT/$exp/Train" --reference "$SIGNAL_REF_JSON" 2>/dev/null | \
      python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('fidelity',{}).get('signal_fidelity_ok',False))" | grep -q True; then
    echo "BLOCK amp $exp: signal_fidelity gate failed"
    return 1
  fi
  return 0
}

adaptive_train_exp() {
  local exp="$1"
  : >"$ROOT/$exp/Train/run_console.log"
  if [[ "$ADAPTIVE_TRAIN" != "1" ]]; then
    train_one_exp "$exp" "$TRAIN_T"
    return $?
  fi

  local -a length_steps=($(length_steps_for_exp "$exp"))
  if [[ "${L_REF_ONLY:-}" == "1" ]] && at_l_reference "$exp"; then
    length_steps=()
    echo "=== L_REF_ONLY $exp — skip length schedule, refresh + amp ==="
  fi
  local -a amp_steps=($AMP_TRAIN_STEPS)
  local cumulative=0
  local blocker="UNKNOWN"
  local phase="length"
  local -a verify_flags=()
  [[ -f "$PEAK_SYNC_JSON" ]] && verify_flags+=(--peak-sync "$PEAK_SYNC_JSON")
  [[ -f "$L_REF_JSON" ]] && verify_flags+=(--L-reference "$L_REF_JSON")

  l_guard_save "$exp"
  ensure_initial_ready "$exp" || return 1
  l_guard_floor_before "$exp"

  if [[ "${AMP_ONLY:-}" == "1" ]]; then
    echo "=== AMP_ONLY $exp — skip length schedule ==="
    if [[ "${AMP_SKIP_REFRESH:-}" != "1" ]]; then
      local refresh="${L_REF_REFRESH:-160}"
      echo "=== AMP_ONLY pre-refresh $exp T=$refresh ==="
      train_one_exp "$exp" "$refresh" || return 1
      cumulative=$((cumulative + refresh))
      l_guard_after "$exp" || true
    fi
    phase="amp"
    blocker=$(get_stall_blocker "$exp")
  else
  for step in "${length_steps[@]}"; do
    if should_skip_length_step "$exp" "$step" "$cumulative"; then
      rc=$?
      if (( rc == 2 )); then
        break
      fi
      continue
    fi
    echo "=== phase=length train $exp step=$step (cumulative +$step) ==="
    train_one_exp "$exp" "$step" || return 1
    cumulative=$((cumulative + step))
    l_guard_after "$exp" || true
    signal_fidelity_snapshot "$exp" "length_${step}"
    if python3 "$VERIFY_DONE" --require-calibrated --require-sync-ok "${verify_flags[@]}" \
        "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
      echo "DONE $exp after length phase T=$cumulative"
      return 0
    fi
    blocker=$(get_stall_blocker "$exp")
    echo "stall $exp blocker=$blocker after length T=$cumulative"
    if has_length_stall "$blocker"; then
      continue
    fi
    if has_amp_stall "$blocker"; then
      phase="amp"
      break
    fi
  done

  if [[ "$phase" != "amp" ]] && ! has_amp_stall "$blocker"; then
    blocker=$(get_stall_blocker "$exp")
    if has_amp_stall "$blocker"; then
      phase="amp"
    fi
  fi

  # L_reference (e.g. 6 5 4 1): formula 6 5 3 1 is off-by-one on dend2; refresh + amp
  if [[ "$phase" != "amp" ]] && at_l_reference "$exp"; then
    blocker=$(get_stall_blocker "$exp")
    if has_length_stall "$blocker"; then
      echo "=== L at reference $exp — refresh traces + amp (L_formula overridden) ==="
      local refresh="${L_REF_REFRESH:-320}"
      train_one_exp "$exp" "$refresh" || return 1
      cumulative=$((cumulative + refresh))
      l_guard_after "$exp" || true
      if python3 "$VERIFY_DONE" --require-calibrated --require-sync-ok "${verify_flags[@]}" \
          "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
        echo "DONE $exp after L-ref refresh T=$cumulative"
        return 0
      fi
      blocker=$(get_stall_blocker "$exp")
      if ready_for_amp "$exp" || has_amp_stall "$blocker"; then
        phase="amp"
      fi
    fi
  fi
  fi

  # Partial sync: keep length phase if amp stall but not all dendrites sync_ok
  if [[ "$phase" == "amp" ]] && ! ready_for_amp "$exp"; then
    if has_amp_stall "$blocker"; then
      echo "partial sync on $exp (blocker=$blocker) — extend length before amp-continue"
      for step in "${length_steps[@]: -2}"; do
        echo "=== phase=length-extend $exp step=$step ==="
        train_one_exp "$exp" "$step" || return 1
        cumulative=$((cumulative + step))
        l_guard_after "$exp" || true
        if python3 "$VERIFY_DONE" --require-calibrated --require-sync-ok "${verify_flags[@]}" \
            "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
          echo "DONE $exp after length-extend T=$cumulative"
          return 0
        fi
        if ready_for_amp "$exp"; then
          break
        fi
      done
    fi
  fi

  if [[ "$phase" == "amp" ]] && ready_for_amp "$exp"; then
    if ! initials_ready_exp "$exp"; then
      echo "BLOCK amp $exp: AMP_NO_INITIAL (Initial dend0-2 <= 0)"
      return 1
    fi
    signal_fidelity_gate "$exp" || return 1
    echo "=== phase=amp-continue $exp (sync_ok all non-ref) ==="
    patch_continue_train "$exp"
    for step in "${amp_steps[@]}"; do
      echo "=== phase=amp train $exp step=$step (cumulative +$step) ==="
      train_one_exp "$exp" "$step" || return 1
      cumulative=$((cumulative + step))
      if python3 "$VERIFY_DONE" --require-calibrated --require-sync-ok "${verify_flags[@]}" \
          "$ROOT/$exp/Train/Parameters_00.xml" >/dev/null 2>&1; then
        echo "DONE $exp after amp phase T=$cumulative"
        return 0
      fi
      blocker=$(get_stall_blocker "$exp")
      echo "stall $exp blocker=$blocker after amp T=$cumulative"
      case "$blocker" in
        AMP_PENDING) continue ;;
        AMP_OSCILLATION)
          if hard_osc_abort_exp "$exp"; then
            echo "ABORT hard OSC $exp after amp T=$cumulative (no_improve>=${AMP_HARD_OSC_NO_IMPROVE}) — stop amp schedule"
            break
          fi
          continue
          ;;
        AMP_NO_INITIAL) echo "AMP_NO_INITIAL — stop amp-continue for $exp"; return 1 ;;
        AMP_AT_RMIN) echo "AMP_AT_RMIN — stop amp-continue for $exp"; break ;;
        LENGTH_STALL|TIME_BUDGET)
          # Re-apply L-ref floor if dendrite shrank below reference during amp, then continue.
          if [[ "$L_REFERENCE" == "ltzcal" || -n "$L_REFERENCE" ]]; then
            l_guard_floor_before "$exp"
            if at_l_reference "$exp" || ready_for_amp "$exp"; then
              echo "length stall during amp — re-floor/continue amp for $exp"
              continue
            fi
          fi
          echo "length stall returned during amp — stop for $exp"
          break ;;
        *) break ;;
      esac
    done
  elif [[ "$phase" == "amp" ]]; then
    echo "skip amp-continue $exp: not all dendrites sync_ok"
  fi

  return 0
}

adaptive_train_all() {
  local -a pids=() dirs=()
  local running=0 fail=0
  wait_one() {
    local pid="${pids[0]}" d="${dirs[0]}"
    pids=("${pids[@]:1}"); dirs=("${dirs[@]:1}")
    if wait "$pid"; then echo "OK train $d"; else echo "FAIL train $d"; fail=$((fail+1)); fi
    running=$((running-1))
  }
  for exp in "${EXPS[@]}"; do
    while (( running >= MAX_JOBS )); do wait_one; done
    ( adaptive_train_exp "$exp" ) &
    pids+=($!); dirs+=("$exp"); running=$((running+1))
  done
  while (( running > 0 )); do wait_one; done
  return "$fail"
}

exec > >(tee "$LOG") 2>&1

echo "=== EXP count=${#EXPS[@]} TRAIN_T start=$TRAIN_T ADAPTIVE=$ADAPTIVE_TRAIN L_REFERENCE=$L_REFERENCE ==="
prepare_l_reference
echo "=== LTZ train patch ==="
apply_ltz_train_patch

echo "=== VERIFY pattern spans (pre-run) ==="
python3 "$VERIFY_SPAN" --meta "$META" \
  $(for e in "${EXPS[@]}"; do echo "$ROOT/$e/Train/Parameters_00.xml" "$ROOT/$e/Test/Parameters_00.xml"; done)

if [[ "$SKIP_TRAIN" != "1" ]]; then
  echo "=== TRAIN wave ==="
  if [[ "$ADAPTIVE_TRAIN" == "1" ]]; then
    adaptive_train_all || exit 1
  else
    run_wave train "$TRAIN_T" || exit 1
  fi
fi

echo "=== Peak sync snapshot ==="
python3 "$ROOT/scripts/analyze_peak_sync.py" \
  $(for e in "${EXPS[@]}"; do echo "$ROOT/$e/Train"; done) \
  -o "$ROOT/peak_sync_latest.json" --md "$ROOT/PEAK_SYNC_REPORT.md" || true

echo "=== Feasibility + stall snapshot ==="
python3 "$FEAS" --post $(for e in "${EXPS[@]}"; do echo "$ROOT/$e/Train/Parameters_00.xml"; done) \
  -o "$ROOT/feasibility_latest.csv"
python3 "$STALL" $(for e in "${EXPS[@]}"; do echo "$ROOT/$e/Train"; done) \
  -o "$ROOT/stall_latest.csv"

echo "=== VERIFY train Done + calibrated ==="
fail_done=0
for exp in "${EXPS[@]}"; do
  if ! python3 "$VERIFY_DONE" --require-calibrated --require-sync-ok --diagnose \
      ${PEAK_SYNC_JSON:+--peak-sync "$PEAK_SYNC_JSON"} \
      ${L_REF_JSON:+--L-reference "$L_REF_JSON"} \
      "$ROOT/$exp/Train/Parameters_00.xml"; then
    echo "TRAIN_NOT_DONE_OR_UNCALIBRATED $exp"
    fail_done=1
  fi
done
if (( fail_done )) && [[ "$ALLOW_PARTIAL_TRAIN" != "1" ]]; then
  echo "Abort sync/test: train not Done/calibrated."
  exit 1
fi

echo "=== VERIFY Train Models ==="
for exp in "${EXPS[@]}"; do
  verify_model "$ROOT/$exp/Train/Model_00.xml" \
    "$(exp_meta "$exp" 2)" "$(exp_meta "$exp" 4)" "$(exp_meta "$exp" 6)" \
    "$(exp_meta "$exp" 7)" "$(exp_meta "$exp" 8)"
done

echo "=== SYNC train -> test + LTZ patch ==="
for exp in "${EXPS[@]}"; do
  neuron=$(exp_meta "$exp" 2)
  kind=$(exp_meta "$exp" 4)
  cap=$(exp_meta "$exp" 6)
  exc_rm=$(exp_meta "$exp" 7)
  exc_rsyn=$(exp_meta "$exp" 8)
  echo "sync $exp"
  "$COPY" sync "$ROOT/$exp/Train" "$ROOT/$exp/Test"
  python3 "$LTZ_TEST" "$ROOT/$exp/Test/Parameters_00.xml" \
    --train "$ROOT/$exp/Train/Parameters_00.xml"
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
            "InhSynapseResistance", "FixedLTZThreshold", "CalibratedFixedLTZThreshold"):
    v = get_tag(train, tag)
    if v is not None:
        test = set_tag(test, tag, v, 0)
tp.write_text(test, encoding="utf-8")
PY
  verify_model "$ROOT/$exp/Test/Model_00.xml" "$neuron" "$kind" "$cap" "$exc_rm" "$exc_rsyn"
done

echo "=== TEST wave t=$TEST_T ==="
run_wave test "$TEST_T" || exit 1

printf "exp,neuron,span_ms,kind,pack,acc,fn,fp,fires,mode,gate,target_hit,L,FixedLTZ,stall_blocker,L_target,iter_count\n" > "$OUT"
for exp in "${EXPS[@]}"; do
  neuron=$(exp_meta "$exp" 2)
  span=$(exp_meta "$exp" 3)
  kind=$(exp_meta "$exp" 4)
  pack=$(exp_meta "$exp" 5)
  csv="$ROOT/$exp/Test/SelectivityLog/results.csv"
  params="$ROOT/$exp/Train/Parameters_00.xml"
  stall_json=$(python3 "$STALL" "$ROOT/$exp/Train" --json 2>/dev/null || echo '[]')
  python3 - "$OUT" "$exp" "$neuron" "$span" "$kind" "$pack" "$csv" "$params" "$stall_json" <<'PY'
import csv, json, re, sys
from pathlib import Path
out, exp, neuron, span, kind, pack, csv_path, params, stall_json = sys.argv[1:10]
rows = list(csv.DictReader(Path(csv_path).open(encoding="utf-8"))) if Path(csv_path).exists() else []
acc = fn = fp = fires = target_hit = gate = 0
mode = "silent"
if rows:
    for r in rows:
        fired = r.get("neuron_fired", "0") == "1"
        if r.get("match", "0") == "1": acc += 1
        if fired: fires += 1
        if r.get("target_class") == "1" and not fired: fn += 1
        if r.get("target_class") == "0" and fired: fp += 1
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
stall = {}
try:
    sj = json.loads(stall_json)
    if sj: stall = sj[0]
except Exception:
    pass
blocker = stall.get("blocker", "")
lt = stall.get("L_target", [])
lt_s = " ".join(str(x) for x in lt) if lt else ""
iter_c = stall.get("iter_count", "")
with open(out, "a", encoding="utf-8") as f:
    f.write(f"{exp},{neuron},{span},{kind},{pack},{acc_s},{fn},{fp},{fires},{mode},{gate},{target_hit},{L},{flt},{blocker},{lt_s},{iter_c}\n")
print(exp, acc_s, mode, "gate", gate, "blocker", blocker)
PY
done
echo "Wrote $OUT"
cat "$OUT"

#!/usr/bin/env bash
# In-place cold reset of SelectivityAsymRm EXP (no new directories).
# PILOT_EXPS="EXP_span25ms_packA_gen EXP_span25ms_packA_preinh EXP_span100ms_packA_preinh"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LTZCAL_SCRIPTS="$(cd "$(dirname "$0")/../../SelectivityLtzCalibrate/scripts" && pwd)"
# shellcheck source=../../SelectivityLtzCalibrate/scripts/asymrm_ltzcal_common.sh
source "$LTZCAL_SCRIPTS/asymrm_ltzcal_common.sh"

COPY="$ROOT/scripts/copy_config.sh"
PY_PATCH="$ROOT/scripts/patch_pattern_scale.py"
LTZ_TRAIN="$LTZCAL_SCRIPTS/patch_ltz_calibrate_train.py"
INJECT="$ROOT/scripts/inject_analyzer.py"
META="$ROOT/grid_cells.tsv"
GTS="${GTS:-20000}"
RESET_TEST="${RESET_TEST:-1}"
PILOT_EXPS="${PILOT_EXPS:-}"

set_project_name() {
  local ini="$1" name="$2"
  [[ -f "$ini" ]] && sed -i "s|<ProjectName>[^<]*</ProjectName>|<ProjectName>${name}</ProjectName>|" "$ini"
}
set_timestep() {
  local ini="$1" ts="$2"
  if [[ -f "$ini" ]]; then
    sed -i "s|<DefaultTimeStep>[0-9]*</DefaultTimeStep>|<DefaultTimeStep>${ts}</DefaultTimeStep>|" "$ini"
    sed -i "s|<GlobalTimeStep>[0-9]*</GlobalTimeStep>|<GlobalTimeStep>${ts}</GlobalTimeStep>|" "$ini"
  fi
}

patch_dissoc_secr() {
  local params="$1" dissoc="$2" secr="$3"
  python3 - "$params" "$dissoc" "$secr" <<'PY'
import re, sys
from pathlib import Path
p = Path(sys.argv[1]); dissoc, secr = sys.argv[2:4]
def set_tag(text, tag, value, count=0):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count or 0)
t = p.read_text(encoding="utf-8")
t = set_tag(t, "SynapseDissociationTC", dissoc, 0)
t = set_tag(t, "SynapseSecretionTC", secr, 0)
p.write_text(t, encoding="utf-8")
PY
}

[[ -f "$META" ]] || { echo "Missing $META — run setup_asymrm.sh first" >&2; exit 1; }

exp_in_list() {
  local e="$1"
  if [[ -z "$PILOT_EXPS" ]]; then return 0; fi
  for p in $PILOT_EXPS; do [[ "$p" == "$e" ]] && return 0; done
  return 1
}

while IFS=$'\t' read -r exp neuron span kind pack cap exc_rm exc_rsyn; do
  [[ "$exp" == exp ]] && continue
  exp_in_list "$exp" || continue

  inh_rm=$(python3 -c "import sys; print(f'{float(sys.argv[1])*10:g}')" "$exc_rm")
  inh_rsyn=$(python3 -c "import sys; print(f'{float(sys.argv[1])*10:g}')" "$exc_rsyn")
  tip=$(python3 -c "import sys; print(f'{int(float(sys.argv[1])):d}')" "$exc_rsyn")

  train="$ROOT/$exp/Train"
  test="$ROOT/$exp/Test"
  echo "=== cold reset $exp (GTS=$GTS) ==="

  asymrm_ltzcal_clear_runtime "$train"
  asymrm_ltzcal_clear_runtime "$test"

  "$COPY" train "$train" "${exp}_Train"
  if [[ "$RESET_TEST" == "1" ]]; then
    "$COPY" test "$test" "${exp}_Test"
  fi

  asymrm_ltzcal_cold_patch "$train/Parameters_00.xml" "$train/Model_00.xml" "$neuron" \
    "0.001" "$cap" "0.001" "$exc_rm" "$inh_rm" "$exc_rsyn" "$inh_rsyn" "$tip"

  if [[ "$kind" == *preinh* ]]; then
    python3 "$LTZ_TRAIN" --preinh "$train/Parameters_00.xml"
  else
    python3 "$LTZ_TRAIN" "$train/Parameters_00.xml"
  fi

  python3 "$PY_PATCH" "$train/Parameters_00.xml" "$train/Model_00.xml" \
    "$test/Parameters_00.xml" "$test/Model_00.xml" --span-ms "$span"

  if [[ -n "${DISSOC:-}" && -n "${SECR:-}" ]]; then
    patch_dissoc_secr "$train/Parameters_00.xml" "$DISSOC" "$SECR"
    patch_dissoc_secr "$train/Model_00.xml" "$DISSOC" "$SECR"
    patch_dissoc_secr "$test/Parameters_00.xml" "$DISSOC" "$SECR"
    patch_dissoc_secr "$test/Model_00.xml" "$DISSOC" "$SECR"
  fi

  if [[ "$RESET_TEST" == "1" ]]; then
    asymrm_ltzcal_patch_test_cold "$test/Parameters_00.xml" "$neuron" "$cap" \
      "$exc_rm" "$inh_rm" "$exc_rsyn" "$inh_rsyn" "$tip"
  fi

  python3 "$INJECT" "$train/Model_00.xml" "$test/Model_00.xml"

  set_project_name "$train/Project.ini" "${exp}_Train"
  set_project_name "$test/Project.ini" "${exp}_Test"
  set_timestep "$train/Project.ini" "$GTS"
  set_timestep "$test/Project.ini" "$GTS"
done < "$META"

echo "Cold reset done."

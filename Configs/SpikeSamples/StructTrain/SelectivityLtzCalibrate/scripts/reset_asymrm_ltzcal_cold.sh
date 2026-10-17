#!/usr/bin/env bash
# In-place cold reset of existing AsymRmLtzCal EXP (no new directories).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=asymrm_ltzcal_common.sh
source "$SCRIPT_DIR/asymrm_ltzcal_common.sh"

GRID="$ROOT/AsymRmLtzCal"
COPY="$ROOT/scripts/copy_config.sh"
PY_PATCH="$ROOT/scripts/patch_pattern_scale.py"
LTZ_TRAIN="$ROOT/scripts/patch_ltz_calibrate_train.py"
INJECT="$ROOT/scripts/inject_analyzer.py"
META="$GRID/grid_cells.tsv"
GTS=10000
RESET_TEST="${RESET_TEST:-1}"

CAP="2.5e-11"
EXC_RM="1e7"
INH_RM="1e8"
EXC_RSYN="8.6e7"
INH_RSYN="8.6e8"
TIP="86000000"

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

[[ -f "$META" ]] || { echo "Missing $META — run setup_asymrm_ltzcal.sh first" >&2; exit 1; }

while IFS=$'\t' read -r exp neuron span kind pack cap exc_rm exc_rsyn; do
  [[ "$exp" == exp ]] && continue
  train="$GRID/$exp/Train"
  test="$GRID/$exp/Test"
  echo "=== cold reset $exp ==="

  asymrm_ltzcal_clear_runtime "$train"
  asymrm_ltzcal_clear_runtime "$test"

  "$COPY" train "$train" "${exp}_Train"
  if [[ "$RESET_TEST" == "1" ]]; then
    "$COPY" test "$test" "${exp}_Test"
  fi

  asymrm_ltzcal_cold_patch "$train/Parameters_00.xml" "$train/Model_00.xml" "$neuron" \
    "0.001" "$cap" "0.001" "$exc_rm" "$INH_RM" "$EXC_RSYN" "$INH_RSYN" "$TIP"

  if [[ "$kind" == *preinh* ]]; then
    python3 "$LTZ_TRAIN" --preinh "$train/Parameters_00.xml"
  else
    python3 "$LTZ_TRAIN" "$train/Parameters_00.xml"
  fi

  python3 "$PY_PATCH" "$train/Parameters_00.xml" "$train/Model_00.xml" \
    "$test/Parameters_00.xml" "$test/Model_00.xml" --span-ms "$span"

  if [[ "$RESET_TEST" == "1" ]]; then
    asymrm_ltzcal_patch_test_cold "$test/Parameters_00.xml" "$neuron" "$cap" \
      "$exc_rm" "$INH_RM" "$EXC_RSYN" "$INH_RSYN" "$TIP"
  else
    python3 - "$test/Parameters_00.xml" "$neuron" "$cap" "$exc_rm" <<'PY'
import re, sys
from pathlib import Path
pp, neuron, cap, exc_rm = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
def set_tag(text, tag, value, count=0):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count or 0)
t = pp.read_text(encoding="utf-8")
t = set_tag(t, "NeuronClassName", neuron, 1)
t = set_tag(t, "MembraneCapacity", cap, 0)
t = set_tag(t, "SynapseDissociationTC", "0.001", 0)
pp.write_text(t, encoding="utf-8")
PY
  fi

  python3 "$INJECT" "$train/Model_00.xml" "$test/Model_00.xml"

  set_project_name "$train/Project.ini" "${exp}_Train"
  set_project_name "$test/Project.ini" "${exp}_Test"
  set_timestep "$train/Project.ini" "$GTS"
  set_timestep "$test/Project.ini" "$GTS"
done < "$META"

echo "Cold reset done for $(awk 'NR>1' "$META" | wc -l) EXP."

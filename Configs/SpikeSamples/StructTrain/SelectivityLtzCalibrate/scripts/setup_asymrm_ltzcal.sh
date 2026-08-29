#!/usr/bin/env bash
# AsymRmLtzCal: Pack A × span 100/50/25 × gen|preinh + AutoCalibrate LTZ (peak 0.99).
# Cold patch parity with SelectivityAsymRm/setup_asymrm.sh + LTZ train patch only.
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
VERIFY="$ROOT/scripts/verify_pattern_span.py"
WATCH_PATCH="$ROOT/scripts/patch_watch_pattern_legend.py"
META="$GRID/grid_cells.tsv"
GTS=10000

GEN="NSPNeuronGenAsymRmD001C25e12"
PRE="NSPNeuronGenPreinh2_5AsymRmD001C25e12"
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

mkdir -p "$GRID"
printf "exp\tneuron\tspan_ms\tkind\tpack\tcap\texc_rm\texc_rsyn\n" > "$META"

declare -a CELLS=(
  "EXP_span100ms_packA_gen|${GEN}|100|gen"
  "EXP_span100ms_packA_preinh|${PRE}|100|preinh"
  "EXP_span50ms_packA_gen|${GEN}|50|gen"
  "EXP_span50ms_packA_preinh|${PRE}|50|preinh"
  "EXP_span25ms_packA_gen|${GEN}|25|gen"
  "EXP_span25ms_packA_preinh|${PRE}|25|preinh"
)

for cell in "${CELLS[@]}"; do
  IFS='|' read -r exp neuron span kind <<<"$cell"
  train="$GRID/$exp/Train"
  test="$GRID/$exp/Test"
  echo "=== setup $exp ==="
  mkdir -p "$train" "$test"
  "$COPY" train "$train" "${exp}_Train"
  "$COPY" test "$test" "${exp}_Test"

  asymrm_ltzcal_cold_patch "$train/Parameters_00.xml" "$train/Model_00.xml" "$neuron" \
    "0.001" "$CAP" "0.001" "$EXC_RM" "$INH_RM" "$EXC_RSYN" "$INH_RSYN" "$TIP"

  if [[ "$kind" == preinh ]]; then
    python3 "$LTZ_TRAIN" --preinh "$train/Parameters_00.xml"
  else
    python3 "$LTZ_TRAIN" "$train/Parameters_00.xml"
  fi

  python3 "$PY_PATCH" "$train/Parameters_00.xml" "$train/Model_00.xml" \
    "$test/Parameters_00.xml" "$test/Model_00.xml" --span-ms "$span"

  asymrm_ltzcal_patch_test_cold "$test/Parameters_00.xml" "$neuron" "$CAP" \
    "$EXC_RM" "$INH_RM" "$EXC_RSYN" "$INH_RSYN" "$TIP"

  python3 "$INJECT" "$train/Model_00.xml" "$test/Model_00.xml"

  set_project_name "$train/Project.ini" "${exp}_Train"
  set_project_name "$test/Project.ini" "${exp}_Test"
  set_timestep "$train/Project.ini" "$GTS"
  set_timestep "$test/Project.ini" "$GTS"

  cat >"$train/README.md" <<EOF
## ${exp} — Train (AsymRmLtzCal Pack A)
NeuronClass=\`${neuron}\` kind=${kind} span=${span}ms GTS=${GTS}
C=${CAP} ExcRm=${EXC_RM} InhRm=${INH_RM} AutoCalibrate FixedLTZ peak_fraction=0.99
EOF
  cp "$train/README.md" "$test/README.md"
  sed -i 's/Train/Test/' "$test/README.md"

  printf "%s\t%s\t%s\t%s\tA\t%s\t%s\t%s\n" \
    "$exp" "$neuron" "$span" "$kind" "$CAP" "$EXC_RM" "$EXC_RSYN" >> "$META"
done

python3 "$VERIFY" --meta "$META" "$GRID"/EXP_*/Train/Parameters_00.xml "$GRID"/EXP_*/Test/Parameters_00.xml
python3 "$WATCH_PATCH" "$GRID"/EXP_*/Train/Interface.xml "$GRID"/EXP_*/Test/Interface.xml 2>/dev/null || true
echo "AsymRmLtzCal setup done."
cat "$META"

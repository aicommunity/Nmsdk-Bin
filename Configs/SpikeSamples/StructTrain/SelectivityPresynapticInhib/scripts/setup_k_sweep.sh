#!/usr/bin/env bash
# Create PSI k-sweep Train/Test pairs. Does NOT touch EXP00–03.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"
PATCH="$ROOT/scripts/patch_neuron_class.py"
PREPARE="$ROOT/scripts/prepare_gui_psi_train.py"

setup_pair() {
  local name="$1"
  local neu="$2"
  local k="$3"
  local train="$ROOT/${name}/Train"
  local test="$ROOT/${name}/Test"
  "$SCR" train "$train" "${name}_Train"
  "$SCR" test  "$test"  "${name}_Test"
  python3 "$PATCH" "$train/Parameters_00.xml" "$neu"
  python3 "$PREPARE" "$train/Parameters_00.xml"
  python3 "$PATCH" "$test/Parameters_00.xml" "$neu"
  cat > "$ROOT/${name}/README.md" << MD
# ${name}

- \`NeuronClassName\`: \`${neu}\` (k=${k})
- Cold start + autothr: \`IsNeedToTrain=1\`, \`ResetToUntrainedState=1\`, \`StructureBuildMode=1\`, L=\`[1,1,1,1]\`
- Train: console \`-t 90 -x -S\`. Test: sync Train→Test, \`-t 20 -x\`
MD
  echo "setup ${name} ${neu} k=${k}"
}

# Default: wave 1. Pass names to set up later waves without touching EXP00–03.
if [[ $# -eq 0 ]]; then
  setup_pair EXP04_preinh_250 NSPNeuronGenPreinh2_5 2.5
  setup_pair EXP05_preinh_300 NSPNeuronGenPreinh3_0 3.0
  setup_pair EXP06_preinh_400 NSPNeuronGenPreinh4_0 4.0
else
  for spec in "$@"; do
    name="${spec%%:*}"
    rest="${spec#*:}"
    neu="${rest%%:*}"
    k="${rest#*:}"
    setup_pair "$name" "$neu" "$k"
  done
fi
echo "Setup done under $ROOT (EXP00–03 untouched)"

#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"
PATCH_NEU="$ROOT/scripts/patch_neuron_class.py"

setup_pair() {
  local name="$1"
  local neu="$2"
  local train="$ROOT/${name}/Train"
  local test="$ROOT/${name}/Test"
  "$SCR" train "$train" "${name}_Train"
  "$SCR" test  "$test"  "${name}_Test"
  sed -i 's|<IsNeedToTrain Type="b" PType="257" IoType="17">[01]</IsNeedToTrain>|<IsNeedToTrain Type="b" PType="257" IoType="17">1</IsNeedToTrain>|' "$train/Parameters_00.xml"
  sed -i 's|<StructureBuildMode Type="i" PType="257" IoType="17">[0-9]</StructureBuildMode>|<StructureBuildMode Type="i" PType="257" IoType="17">1</StructureBuildMode>|' "$train/Parameters_00.xml"
  sed -i 's|<ResetToUntrainedState Type="b" PType="257" IoType="17">[01]</ResetToUntrainedState>|<ResetToUntrainedState Type="b" PType="257" IoType="17">1</ResetToUntrainedState>|' "$train/Parameters_00.xml" || true
  python3 "$PATCH_NEU" "$train/Parameters_00.xml" "$neu"
  python3 "$ROOT/scripts/prepare_gui_psi_train.py" "$train/Parameters_00.xml"
  python3 - <<PY2
from pathlib import Path
import re
params = Path("$train/Parameters_00.xml")
text = params.read_text(encoding="utf-8")
if "ResetToUntrainedState" not in text:
    text = text.replace(
        '<IsNeedToTrain Type="b" PType="257" IoType="17">1</IsNeedToTrain>',
        '<IsNeedToTrain Type="b" PType="257" IoType="17">1</IsNeedToTrain>\n'
        '\t\t\t\t\t<ResetToUntrainedState Type="b" PType="257" IoType="17">1</ResetToUntrainedState>',
        1,
    )
else:
    text = re.sub(
        r'<ResetToUntrainedState Type="b" PType="257" IoType="17">[01]</ResetToUntrainedState>',
        '<ResetToUntrainedState Type="b" PType="257" IoType="17">1</ResetToUntrainedState>',
        text, count=1)
text = re.sub(r'<DendriteLength Type="simplevector" Size="4" elemType="i" PType="257" IoType="33">[^<]*</DendriteLength>',
              '<DendriteLength Type="simplevector" Size="4" elemType="i" PType="257" IoType="33">1 1 1 1</DendriteLength>', text, count=1)
text = re.sub(r'<TipSynapseResistance Type="simplevector" Size="4" elemType="d" PType="259" IoType="33">[^<]*</TipSynapseResistance>',
              '<TipSynapseResistance Type="simplevector" Size="4" elemType="d" PType="259" IoType="33">86000000 86000000 86000000 86000000</TipSynapseResistance>', text, count=1)
text = re.sub(r'<InitialSomaPotential Type="simplevector" Size="4" elemType="d" PType="257" IoType="33">[^<]*</InitialSomaPotential>',
              '<InitialSomaPotential Type="simplevector" Size="4" elemType="d" PType="257" IoType="33">0 0 0 0</InitialSomaPotential>', text, count=1)
text = re.sub(r'<TrainingPhase Type="i" PType="257" IoType="17">[^<]*</TrainingPhase>',
              '<TrainingPhase Type="i" PType="257" IoType="17">0</TrainingPhase>', text, count=1)
params.write_text(text, encoding="utf-8")
PY2
  python3 "$PATCH_NEU" "$test/Parameters_00.xml" "$neu"
  cat > "$ROOT/${name}/README.md" << MD
# ${name}

- \`NeuronClassName\`: \`${neu}\`
- \`AutoCalibrateFixedLTZThreshold=1\`, mode=gap_fraction, fraction=0.85
- Train: cold retrain + \`-S\`; Test: sync weights + analyzer CSV
MD
}

setup_pair EXP00_baseline_autothr NSPNeuronGen
setup_pair EXP01_preinh_050_autothr NSPNeuronGenPreinh0_5
setup_pair EXP02_preinh_100_autothr NSPNeuronGenPreinh
setup_pair EXP03_preinh_200_autothr NSPNeuronGenPreinh2_0

echo "Autothr setup done under $ROOT"

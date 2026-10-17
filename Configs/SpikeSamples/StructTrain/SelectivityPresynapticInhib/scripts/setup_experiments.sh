#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"
PATCH="$ROOT/scripts/patch_neuron_class.py"

setup_pair() {
  local name="$1"
  local neu="$2"
  local train="$ROOT/${name}/Train"
  local test="$ROOT/${name}/Test"
  "$SCR" train "$train" "${name}_Train"
  "$SCR" test  "$test"  "${name}_Test"
  # Train: cold retrain flags
  sed -i 's|<IsNeedToTrain Type="b" PType="257" IoType="17">[01]</IsNeedToTrain>|<IsNeedToTrain Type="b" PType="257" IoType="17">1</IsNeedToTrain>|' "$train/Parameters_00.xml"
  sed -i 's|<StructureBuildMode Type="i" PType="257" IoType="17">[0-9]</StructureBuildMode>|<StructureBuildMode Type="i" PType="257" IoType="17">1</StructureBuildMode>|' "$train/Parameters_00.xml"
  sed -i 's|<ResetToUntrainedState Type="b" PType="257" IoType="17">[01]</ResetToUntrainedState>|<ResetToUntrainedState Type="b" PType="257" IoType="17">1</ResetToUntrainedState>|' "$train/Parameters_00.xml" || true
  python3 "$PATCH" "$train/Parameters_00.xml" "$neu"
  # Cold start: untrained lengths/tips + ResetToUntrainedState
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
  python3 "$PATCH" "$test/Parameters_00.xml" "$neu"
  cat > "$ROOT/${name}/README.md" << MD
# ${name}

- \`NeuronClassName\`: \`${neu}\`
- Train: cold retrain (\`IsNeedToTrain=1\`, \`StructureBuildMode=1\`) + \`-S\`
- Test: sync weights from Train, analyzer CSV in \`SelectivityLog/\`
MD
}

setup_pair EXP00_baseline NSPNeuronGen
setup_pair EXP01_preinh_050 NSPNeuronGenPreinh0_5
setup_pair EXP02_preinh_100 NSPNeuronGenPreinh
setup_pair EXP03_preinh_200 NSPNeuronGenPreinh2_0

# PSI Train: cold + AutoCalibrateFixedLTZThreshold so GUI Start needs no extra edits
python3 "$ROOT/scripts/prepare_gui_psi_train.py" \
  "$ROOT/EXP01_preinh_050/Train/Parameters_00.xml" \
  "$ROOT/EXP02_preinh_100/Train/Parameters_00.xml" \
  "$ROOT/EXP03_preinh_200/Train/Parameters_00.xml"

cat > "$ROOT/README.md" << 'MD'
# SelectivityPresynapticInhib

Исследование детекции паттерна при пресинаптическом торможении tip-синапсов (`UsePresynapticInhibition`).

Прототипы Storage (без правок learner): `NSPNeuronGen` / `NSPNeuronGenPreinh0_5` / `NSPNeuronGenPreinh` / `NSPNeuronGenPreinh2_0`.

Формула: `Output = C*(1-k*PreOutput)*PreOutput`, `C=4k/R` (пик = `1/R`). См. [REPORT.md](REPORT.md), autothr: [REPORT_autothr.md](REPORT_autothr.md).

PSI Train уже готов к GUI: cold start + `AutoCalibrateFixedLTZThreshold=1`. Открыть `EXP0X_.../Train/Project.ini` в NeuroModeler и Start. После Done порог калибруется сам.

| EXP | NeuronClassName | k |
|-----|-----------------|--:|
| EXP00_baseline | NSPNeuronGen | — |
| EXP01_preinh_050 | NSPNeuronGenPreinh0_5 | 0.5 |
| EXP02_preinh_100 | NSPNeuronGenPreinh | 1.0 |
| EXP03_preinh_200 | NSPNeuronGenPreinh2_0 | 2.0 |

```bash
# GUI: File → Open → .../EXP02_preinh_100/Train/Project.ini → Start
./scripts/setup_experiments.sh
./scripts/run_experiments.sh
```
MD

echo "Setup done under $ROOT"

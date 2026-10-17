#!/usr/bin/env bash
# Create PSI k-sweep Train/Test pairs. Does NOT touch EXP00–03.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"
PATCH="$ROOT/scripts/patch_neuron_class.py"
PREPARE="$ROOT/scripts/prepare_gui_psi_train.py"

write_exp_readme() {
  local name="$1"
  local neu="$2"
  local k="$3"
  local base="$ROOT/${name}"
  cat > "$base/README.md" << MD
## ${name} — PSI k-sweep / selectivity

**Путь:** \`Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/${name}\`  
**Статус:** экспериментальный конфиг StructTrain / SelectivityPresynapticInhib

### Назначение

Пара Train/Test для влияния коэффициента пресинаптического торможения \`k\` на точность детекции паттерна (8 trials).

### Параметры нейрона

- **NeuronClassName:** \`${neu}\`
- **k (PSI):** \`${k}\`
- **Autothr:** \`AutoCalibrateFixedLTZThreshold=1\`, mode=\`gap_fraction\`, fraction=\`0.85\`
- **Cold train:** \`IsNeedToTrain=1\`, \`ResetToUntrainedState=1\`, \`StructureBuildMode=1\`, L=\`[1,1,1,1]\`

### Watch-метрики

\`DendriticSumPotential\` = avg \`SumChannelInput\` сомы (\`/4\`). Сравнивать со \`mean(DendriteNeuronAmplitude[1..4])\`.  
См. [корневой README](../README.md).

### Использование

\`\`\`bash
NeuroModelerConsole -c ${base}/Train/Project.ini -s -t 90 -x -S
# sync Train→Test, затем:
NeuroModelerConsole -c ${base}/Test/Project.ini -s -t 20 -x
\`\`\`

Серия: [\`../README.md\`](../README.md) · отчёт: [\`../REPORT_k_sweep.md\`](../REPORT_k_sweep.md).
MD

  # Enrich Train/Test README written by copy_config with k/neu
  for role in Train Test; do
    local dir="$base/${role}"
    [[ -d "$dir" ]] || continue
    local tflag=20 sflag=""
    if [[ "$role" == Train ]]; then tflag=90; sflag=" -S"; fi
    cat > "$dir/README.md" << MD
## ${name} — ${role}

**Путь:** \`Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/${name}/${role}\`  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib

### Назначение

Конфиг **${role}** для PSI k=\`${k}\` (\`${neu}\`).

### Параметры нейрона

- **NeuronClassName:** \`${neu}\`
- **k (PSI):** \`${k}\`
- **Autothr:** \`AutoCalibrateFixedLTZThreshold=1\`, mode=\`gap_fraction\`, fraction=\`0.85\`

### Watch-метрики

| Chart | Свойство | Смысл |
|---|---|---|
| Dendrite Amplitudes | \`DendriteNeuronAmplitude[i]\` | \`DendriteN_1.SumPotential\` |
| Neuron Sums | \`DendriticSumPotential\` | avg \`SumChannelInput\` сомы (≈\`/4\`) |
| Neuron Sums | \`SomaSumPotential\` | avg \`Output\` каналов сомы |

\`DendriticSumPotential ≈ mean(DendriteNeuronAmplitude[1..4]) = DendriteNeuronAmplitude[0]/4\`.  
Подробнее: [корневой README серии](../../README.md).

### Использование

\`\`\`bash
NeuroModelerConsole -c ${dir}/Project.ini -s -t ${tflag} -x${sflag}
\`\`\`

Родитель: [\`../README.md\`](../README.md) · отчёт: [\`../../REPORT_k_sweep.md\`](../../REPORT_k_sweep.md).
MD
  done
}

setup_pair() {
  local name="$1"
  local neu="$2"
  local k="$3"
  local train="$ROOT/${name}/Train"
  local test="$ROOT/${name}/Test"
  mkdir -p "$ROOT/${name}"
  "$SCR" train "$train" "${name}_Train"
  "$SCR" test  "$test"  "${name}_Test"
  python3 "$PATCH" "$train/Parameters_00.xml" "$neu"
  python3 "$PREPARE" "$train/Parameters_00.xml"
  python3 "$PATCH" "$test/Parameters_00.xml" "$neu"
  write_exp_readme "$name" "$neu" "$k"
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

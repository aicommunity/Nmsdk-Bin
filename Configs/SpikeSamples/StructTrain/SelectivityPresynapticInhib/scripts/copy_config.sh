#!/usr/bin/env bash
# Copy train/test config templates for SelectivityPresynapticInhib experiments.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_TRAIN="${ROOT}/../TimeNeuronTimeLearner"
SRC_TEST="${ROOT}/../TimeNeuronTimeLearnerTest"
EXCLUDE=(--exclude='EventsLog' --exclude='StatisticLog' --exclude='History.xml'
         --exclude='settings.qt' --exclude='SelectivityLog')

write_project_readme() {
  # $1=dst dir, $2=ProjectName, $3=role (Train|Test)
  local dst="$1"
  local name="$2"
  local role="$3"
  local parent_link
  parent_link="$(dirname "$dst")/README.md"
  cat > "$dst/README.md" << MD
## ${name} — ${role}

**Путь:** относительный каталог проекта NeuroModeler  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib

### Назначение

Конфиг **${role}** серии PSI / StructTrain. Подробное описание эксперимента — в родительском README.

### Watch-метрики

| Chart | Свойство | Смысл |
|---|---|---|
| Dendrite Amplitudes | \`DendriteNeuronAmplitude[i]\` | \`DendriteN_1.SumPotential\` |
| Neuron Sums | \`DendriticSumPotential\` | avg \`SumChannelInput\` сомы (≈\`/4\`) |
| Neuron Sums | \`SomaSumPotential\` | avg \`Output\` каналов сомы |

\`DendriticSumPotential ≈ mean(DendriteNeuronAmplitude[1..4]) = DendriteNeuronAmplitude[0]/4\`.

### Связанные материалы

- Родитель: \`${parent_link}\`
- Серия: \`$(cd "$(dirname "$0")/.." && pwd)/README.md\`
- Отчёт k-sweep: \`REPORT_k_sweep.md\` в корне серии
MD
}

copy_train() {
  local dst="$1"
  local name="$2"
  mkdir -p "$dst"
  rsync -a "${EXCLUDE[@]}" "$SRC_TRAIN/" "$dst/"
  sed -i "s|<ProjectName>TimeNeuronTimeLearner</ProjectName>|<ProjectName>${name}</ProjectName>|" "$dst/Project.ini"
  write_project_readme "$dst" "$name" "Train"
}

copy_test() {
  local dst="$1"
  local name="$2"
  mkdir -p "$dst"
  rsync -a "${EXCLUDE[@]}" "$SRC_TEST/" "$dst/"
  sed -i "s|<ProjectName>TimeNeuronTimeLearnerTest</ProjectName>|<ProjectName>${name}</ProjectName>|" "$dst/Project.ini"
  # inference: do not rebuild structure on load
  if grep -q 'StructureBuildMode' "$dst/Parameters_00.xml"; then
    sed -i 's|<StructureBuildMode Type="i" PType="257" IoType="17">[0-9]</StructureBuildMode>|<StructureBuildMode Type="i" PType="257" IoType="17">0</StructureBuildMode>|g' "$dst/Parameters_00.xml"
  fi
  write_project_readme "$dst" "$name" "Test"
  python3 "$(dirname "$0")/patch_test_model.py" "$dst/Model_00.xml"
}

sync_train_to_test() {
  local train="$1"
  local test="$2"
  python3 "$(dirname "$0")/merge_train_weights.py" "$train/Parameters_00.xml" "$test/Parameters_00.xml"
  python3 "$(dirname "$0")/inject_analyzer.py" "$train/Model_00.xml" "$test/Model_00.xml"
}

case "${1:-}" in
  train) copy_train "$2" "$3" ;;
  test)  copy_test "$2" "$3" ;;
  sync)  sync_train_to_test "$2" "$3" ;;
  *) echo "Usage: $0 train|test|sync <path> [ProjectName]" >&2; exit 1 ;;
esac

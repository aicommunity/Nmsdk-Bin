#!/usr/bin/env bash
# Copy train/test config templates for SelectivityPhaseA experiments.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_TRAIN="${ROOT}/../TimeNeuronTimeLearner"
SRC_TEST="${ROOT}/../TimeNeuronTimeLearnerTest"
EXCLUDE=(--exclude='EventsLog' --exclude='StatisticLog' --exclude='History.xml'
         --exclude='settings.qt' --exclude='SelectivityLog')

copy_train() {
  local dst="$1"
  local name="$2"
  mkdir -p "$dst"
  rsync -a "${EXCLUDE[@]}" "$SRC_TRAIN/" "$dst/"
  sed -i "s|<ProjectName>TimeNeuronTimeLearner</ProjectName>|<ProjectName>${name}</ProjectName>|" "$dst/Project.ini"
  echo "Конфиг для ${name} (Train). Родитель: $(dirname "$dst")/README.md" > "$dst/README.md"
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
  echo "Конфиг для ${name} (Test). Родитель: $(dirname "$dst")/README.md" > "$dst/README.md"
  python3 "$(dirname "$0")/patch_test_model.py" "$dst/Model_00.xml"
}

sync_train_to_test() {
  local train="$1"
  local test="$2"
  python3 "$(dirname "$0")/merge_train_weights.py" --test "$train/Parameters_00.xml" "$test/Parameters_00.xml"
  python3 "$(dirname "$0")/merge_train_model.py" "$train" "$test"
  python3 "$(dirname "$0")/inject_analyzer.py" "$test/Model_00.xml"
}

case "${1:-}" in
  train) copy_train "$2" "$3" ;;
  test)  copy_test "$2" "$3" ;;
  sync)  sync_train_to_test "$2" "$3" ;;
  *) echo "Usage: $0 train|test|sync <path> [ProjectName]" >&2; exit 1 ;;
esac

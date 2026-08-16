#!/usr/bin/env bash
# Create PSI time-expand EXP30–35 (200/300/400 ms). Does NOT touch EXP00–27.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"
PATCH_NEU="$ROOT/scripts/patch_neuron_class.py"
PREPARE="$ROOT/scripts/prepare_gui_psi_train.py"
SCALE="$ROOT/scripts/patch_pattern_scale.py"

write_exp_readme() {
  local name="$1"
  local neu="$2"
  local span_ms="$3"
  local k="$4"
  local sync="$5"
  local peak="$6"
  local agree="$7"
  local alpha="$8"
  local base="$ROOT/${name}"
  cat > "$base/README.md" << MD
## ${name} — PSI time-expand

**Путь:** \`Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/${name}\`  
**Статус:** экспериментальный конфиг StructTrain / SelectivityPresynapticInhib

### Назначение

Расширенный паттерн first→last ≈ **${span_ms} мс** (α=${alpha} vs эталон 0.48 с), baseline vs PSI k=2.5.

### Параметры

- **NeuronClassName:** \`${neu}\`
- **k (PSI):** \`${k}\`
- **SyncTolerance₀:** \`${sync}\`
- **PeakMeasureMargin₀:** \`${peak}\`
- **DelayAgreeMarginMin₀:** \`${agree}\`
- **IterationGap:** \`1.5\` (не масштабируется)
- **ISI floor:** \`1.5 мс\`
- **Autothr:** \`gap_fraction=0.85\`

### Использование

\`\`\`bash
NeuroModelerConsole -c ${base}/Train/Project.ini -s -t 90 -x -S
# sync Train→Test, затем:
NeuroModelerConsole -c ${base}/Test/Project.ini -s -t 20 -x
\`\`\`

Серия: [\`../README.md\`](../README.md) · отчёт: [\`../REPORT_time_expand.md\`](../REPORT_time_expand.md).
MD

  for role in Train Test; do
    local dir="$base/${role}"
    [[ -d "$dir" ]] || continue
    local tflag=20 sflag=""
    if [[ "$role" == Train ]]; then tflag=90; sflag=" -S"; fi
    cat > "$dir/README.md" << MD
## ${name} — ${role}

**Путь:** \`Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/${name}/${role}\`  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib (time-expand)

### Параметры

- **NeuronClassName:** \`${neu}\`
- **span:** ${span_ms} мс (α=${alpha})
- **SyncTolerance / PeakMeasureMargin / DelayAgreeMarginMin:** ${sync} / ${peak} / ${agree}

### Использование

\`\`\`bash
NeuroModelerConsole -c ${dir}/Project.ini -s -t ${tflag} -x${sflag}
\`\`\`

Родитель: [\`../README.md\`](../README.md) · [\`../../REPORT_time_expand.md\`](../../REPORT_time_expand.md).
MD
  done
}

setup_pair() {
  local name="$1"
  local neu="$2"
  local span_ms="$3"
  local k="$4"
  local train="$ROOT/${name}/Train"
  local test="$ROOT/${name}/Test"
  mkdir -p "$ROOT/${name}"
  "$SCR" train "$train" "${name}_Train"
  "$SCR" test  "$test"  "${name}_Test"

  local xmls=(
    "$train/Parameters_00.xml" "$train/Model_00.xml"
    "$test/Parameters_00.xml" "$test/Model_00.xml"
  )
  python3 "$SCALE" "${xmls[@]}" --span-ms "$span_ms"

  local vals
  vals="$(python3 - <<PY
import sys
sys.path.insert(0, "$ROOT/scripts")
from patch_pattern_scale import compute_initial
i = compute_initial($span_ms / 1000.0)
print(f"{i['sync_tol']:.6g} {i['peak_margin']:.6g} {i['agree_min']:.6g} {i['alpha']:.6g}")
PY
)"
  local sync peak agree alpha
  read -r sync peak agree alpha <<<"$vals"

  python3 "$PATCH_NEU" "$train/Parameters_00.xml" "$neu"
  python3 "$PATCH_NEU" "$train/Model_00.xml" "$neu"
  python3 "$PREPARE" "$train/Parameters_00.xml"
  python3 "$PATCH_NEU" "$test/Parameters_00.xml" "$neu"
  python3 "$PATCH_NEU" "$test/Model_00.xml" "$neu"

  local iface_train_src="$ROOT/scripts/golden_train_Interface.xml"
  local iface_test_src="$ROOT/scripts/golden_test_Interface.xml"
  if [[ -f "$iface_train_src" && -f "$iface_test_src" ]]; then
    cp -f "$iface_train_src" "$train/Interface.xml"
    cp -f "$iface_test_src" "$test/Interface.xml"
  fi

  write_exp_readme "$name" "$neu" "$span_ms" "$k" "$sync" "$peak" "$agree" "$alpha"
  echo "setup ${name} ${neu} span=${span_ms}ms SyncTol=${sync} Peak=${peak} Agree=${agree}"
}

if [[ $# -eq 0 ]]; then
  setup_pair EXP30_span200ms_baseline   NSPNeuronGen          200 —
  setup_pair EXP31_span200ms_preinh250  NSPNeuronGenPreinh2_5 200 2.5
  setup_pair EXP32_span300ms_baseline   NSPNeuronGen          300 —
  setup_pair EXP33_span300ms_preinh250  NSPNeuronGenPreinh2_5 300 2.5
  setup_pair EXP34_span400ms_baseline   NSPNeuronGen          400 —
  setup_pair EXP35_span400ms_preinh250  NSPNeuronGenPreinh2_5 400 2.5
else
  for spec in "$@"; do
    IFS=':' read -r name neu span_ms k <<<"$spec"
    setup_pair "$name" "$neu" "$span_ms" "$k"
  done
fi

#!/usr/bin/env bash
# Cold-patch FastSpan EXPs: neuron class, L=1 tips, span scale, timing margins.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY_PATCH="$ROOT/scripts/patch_pattern_scale.py"
INJECT="$ROOT/scripts/inject_analyzer.py"

PREINH_FAST="NSPNeuronGenPreinh2_5D002C25e11"
FAST="NSPNeuronGenD002C25e11"

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

write_readme() {
  local dir="$1" role="$2" exp="$3" neuron="$4" span="$5" kind="$6" gts="$7" ltz_note="$8"
  cat >"$dir/README.md" <<EOF
## ${exp} — ${role}

**Путь:** \`Bin/Configs/SpikeSamples/StructTrain/SelectivityFastSpan/${exp}/${role}\`

### Параметры

- **NeuronClassName:** \`${neuron}\`
- **kind:** ${kind}
- **span:** ${span} мс
- **GlobalTimeStep:** ${gts}
- **Element defaults:** DissociationTC=0.002, MembraneCapacity=2.5e-10 (UseElementDefaults via UploadClass)
${ltz_note}
### Использование

\`\`\`bash
NeuroModelerConsole -c Project.ini -s -t 160 -x -S   # Train
NeuroModelerConsole -c Project.ini -s -t 20 -x       # Test
\`\`\`

Родитель: [\`../../REPORT.md\`](../../REPORT.md).
EOF
}

cold_patch() {
  local params="$1" model="$2" neuron="$3" use_defaults="$4" dissoc="$5" cap="$6"
  python3 - "$params" "$model" "$neuron" "$use_defaults" "$dissoc" "$cap" <<'PY'
import re, sys
from pathlib import Path
params_path, model_path = Path(sys.argv[1]), Path(sys.argv[2])
neuron, use_def, dissoc, cap = sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
t = params_path.read_text(encoding="utf-8")

def set_tag(text, tag, value, count=1):
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count)

t = set_tag(t, "IsNeedToTrain", "1", count=1)
t = set_tag(t, "StructureBuildMode", "1", count=1)
t = set_tag(t, "NeuronClassName", neuron, count=1)
t = set_tag(t, "SynapseClassName", "NPSynapseBio", count=1)
t = set_tag(t, "TipSynapseResistance", "86000000 86000000 86000000 86000000", count=1)
t = set_tag(t, "DendriteLength", "1 1 1 1", count=1)
t = set_tag(t, "NumDendriteMembranePartsVec", "1 1 1 1", count=0)
t = set_tag(t, "InitialSomaPotential", "0 0 0 0", count=1)
if re.search(r"<ResetToUntrainedState\b", t):
    t = set_tag(t, "ResetToUntrainedState", "1", count=1)
t = set_tag(t, "UseElementDefaults", use_def, count=0)
t = set_tag(t, "MembraneCapacity", cap, count=0)
t = set_tag(t, "SynapseDissociationTC", dissoc, count=0)
params_path.write_text(t, encoding="utf-8")

m = model_path.read_text(encoding="utf-8")
m = re.sub(r'(<Neuron Class=")[^"]+(">)', rf'\g<1>{neuron}\2', m, count=1)
m = set_tag(m, "NeuronClassName", neuron, count=0)
m = set_tag(m, "NumDendriteMembranePartsVec", "1 1 1 1", count=0)
m = set_tag(m, "DendriteLength", "1 1 1 1", count=0)
m = set_tag(m, "UseElementDefaults", use_def, count=0)
m = set_tag(m, "MembraneCapacity", cap, count=0)
m = set_tag(m, "SynapseDissociationTC", dissoc, count=0)
m = re.sub(r'(NeuronTimeLearner\.Neuron\.Dendrite\d+)_\d+(\.ExcSynapse)', r'\1_1\2', m)
m = re.sub(r'(NeuronTimeLearner\.Neuron\.Dendrite\d+)_\d+(\.InhSynapse)', r'\1_1\2', m)
model_path.write_text(m, encoding="utf-8")
PY
}

set_fixed_ltz() {
  local params="$1" value="$2"
  python3 - "$params" "$value" <<'PY'
import re, sys
from pathlib import Path
p = Path(sys.argv[1]); v = sys.argv[2]
t = p.read_text(encoding="utf-8")
t2, n = re.subn(
    r"(<FixedLTZThreshold\b[^>]*>)[^<]*(</FixedLTZThreshold>)",
    rf"\g<1>{v}\2",
    t,
    count=1,
)
if n == 0:
    raise SystemExit(f"FixedLTZThreshold not found in {p}")
p.write_text(t2, encoding="utf-8")
PY
}

META="$ROOT/grid_cells.tsv"
printf "exp\tneuron\tspan_ms\tkind\n" > "$META"

declare -a CELLS=(
  "EXP_span100ms_fast|${FAST}|100|fast|1|0.002|2.5e-10|2000|"
  "EXP_span100ms_fast_preinh|${PREINH_FAST}|100|preinh|1|0.002|2.5e-10|2000|"
  "EXP_span50ms_fast|${FAST}|50|fast|1|0.002|2.5e-10|2000|"
  "EXP_span50ms_fast_preinh|${PREINH_FAST}|50|preinh|1|0.002|2.5e-10|2000|"
  "EXP_span25ms_fast|${FAST}|25|fast|1|0.002|2.5e-10|2000|"
  "EXP_span25ms_fast_preinh|${PREINH_FAST}|25|preinh|1|0.002|2.5e-10|2000|"
  "EXP_span25ms_fast_ts10k|${FAST}|25|fast_ts10k|1|0.002|2.5e-10|10000|0.04"
  "EXP_span25ms_fast_preinh_ts10k|${PREINH_FAST}|25|preinh_ts10k|1|0.002|2.5e-10|10000|0.04"
)

for cell in "${CELLS[@]}"; do
  IFS='|' read -r exp neuron span kind use_def dissoc cap gts fixed_ltz <<<"$cell"
  echo "=== setup $exp ==="
  train="$ROOT/$exp/Train"
  test="$ROOT/$exp/Test"
  mkdir -p "$train" "$test"

  cold_patch "$train/Parameters_00.xml" "$train/Model_00.xml" "$neuron" "$use_def" "$dissoc" "$cap"
  python3 "$PY_PATCH" "$train/Parameters_00.xml" "$train/Model_00.xml" \
    "$test/Parameters_00.xml" "$test/Model_00.xml" --span-ms "$span"

  # Cold Test Model = Train Model + analyzer (avoid stale Bio Test shells)
  python3 "$INJECT" "$train/Model_00.xml" "$test/Model_00.xml"

  python3 - "$test/Parameters_00.xml" "$neuron" "$use_def" "$dissoc" "$cap" <<'PY'
import re, sys
from pathlib import Path
def set_tag(text, tag, value, count=1):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count)
pp = Path(sys.argv[1])
neuron, use_def, dissoc, cap = sys.argv[2:6]
t = pp.read_text(encoding="utf-8")
t = set_tag(t, "NeuronClassName", neuron, 1)
t = set_tag(t, "UseElementDefaults", use_def, 0)
t = set_tag(t, "MembraneCapacity", cap, 0)
t = set_tag(t, "SynapseDissociationTC", dissoc, 0)
t = set_tag(t, "IsNeedToTrain", "0", 1)
t = set_tag(t, "StructureBuildMode", "0", 1)
t = set_tag(t, "TipSynapseResistance", "86000000 86000000 86000000 86000000", 1)
t = set_tag(t, "DendriteLength", "1 1 1 1", 1)
pp.write_text(t, encoding="utf-8")
PY

  set_project_name "$train/Project.ini" "${exp}_Train"
  set_project_name "$test/Project.ini" "${exp}_Test"
  set_timestep "$train/Project.ini" "$gts"
  set_timestep "$test/Project.ini" "$gts"
  if [[ -n "$fixed_ltz" ]]; then
    set_fixed_ltz "$train/Parameters_00.xml" "$fixed_ltz"
    set_fixed_ltz "$test/Parameters_00.xml" "$fixed_ltz"
  fi

  ltz_note=""
  if [[ -n "$fixed_ltz" ]]; then
    ltz_note="- **FixedLTZThreshold:** ${fixed_ltz}"$'\n'
  fi
  write_readme "$train" "Train" "$exp" "$neuron" "$span" "$kind" "$gts" "$ltz_note"
  write_readme "$test" "Test" "$exp" "$neuron" "$span" "$kind" "$gts" "$ltz_note"

  printf "%s\t%s\t%s\t%s\n" "$exp" "$neuron" "$span" "$kind" >> "$META"
done

echo "FastSpan setup done. Meta: $META"
cat "$META"

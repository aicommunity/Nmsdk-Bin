#!/usr/bin/env bash
# Cold-patch FastSpan EXPs: neuron class, L=1 tips, span scale, timing margins.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY_PATCH="$ROOT/scripts/patch_pattern_scale.py"

cold_patch() {
  local params="$1" model="$2" neuron="$3" use_defaults="$4" dissoc="$5" cap="$6"
  python3 - "$params" "$model" "$neuron" "$use_defaults" "$dissoc" "$cap" <<'PY'
import re, sys
from pathlib import Path
params_path, model_path = Path(sys.argv[1]), Path(sys.argv[2])
neuron, use_def, dissoc, cap = sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
t = params_path.read_text(encoding="utf-8")

def set_tag(text, tag, value, count=0):
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count)

t = set_tag(t, "IsNeedToTrain", "1", count=1)
t = set_tag(t, "NeuronClassName", neuron, count=1)
t = set_tag(t, "SynapseClassName", "NPSynapseBio", count=1)
t = set_tag(t, "TipSynapseResistance", "86000000 86000000 86000000 86000000", count=0)
t = set_tag(t, "DendriteLength", "1 1 1 1", count=0)
t = set_tag(t, "NumDendriteMembranePartsVec", "1 1 1 1", count=0)
t = set_tag(t, "InitialSomaPotential", "0 0 0 0", count=0)
if re.search(r"<ResetToUntrainedState\b", t):
    t = set_tag(t, "ResetToUntrainedState", "1", count=1)
# Neuron element defaults (inside Neuron block)
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

META="$ROOT/grid_cells.tsv"
printf "exp\tneuron\tspan_ms\tkind\n" > "$META"

declare -a CELLS=(
  "EXP_span100ms_fast|NSPNeuronGenD002C25e11|100|fast|1|0.002|2.5e-10"
  "EXP_span100ms_fast_preinh|NSPNeuronGenPreinh2_5|100|preinh|1|0.002|2.5e-10"
  "EXP_span50ms_fast|NSPNeuronGenD002C25e11|50|fast|1|0.002|2.5e-10"
  "EXP_span50ms_fast_preinh|NSPNeuronGenPreinh2_5|50|preinh|1|0.002|2.5e-10"
  "EXP_span25ms_fast|NSPNeuronGenD002C25e11|25|fast|1|0.002|2.5e-10"
  "EXP_span25ms_fast_preinh|NSPNeuronGenPreinh2_5|25|preinh|1|0.002|2.5e-10"
)

for cell in "${CELLS[@]}"; do
  IFS='|' read -r exp neuron span kind use_def dissoc cap <<<"$cell"
  echo "=== setup $exp ==="
  train="$ROOT/$exp/Train"
  test="$ROOT/$exp/Test"
  cold_patch "$train/Parameters_00.xml" "$train/Model_00.xml" "$neuron" "$use_def" "$dissoc" "$cap"
  # scale patterns + initial margins on Train and Test
  python3 "$PY_PATCH" "$train/Parameters_00.xml" "$train/Model_00.xml" \
    "$test/Parameters_00.xml" "$test/Model_00.xml" --span-ms "$span"
  # ensure Test neuron class matches
  python3 - "$test/Parameters_00.xml" "$test/Model_00.xml" "$neuron" "$use_def" "$dissoc" "$cap" <<'PY'
import re, sys
from pathlib import Path
def set_tag(text, tag, value, count=0):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count)
pp, mp = Path(sys.argv[1]), Path(sys.argv[2])
neuron, use_def, dissoc, cap = sys.argv[3:7]
t = set_tag(pp.read_text(encoding="utf-8"), "NeuronClassName", neuron, 0)
t = set_tag(t, "UseElementDefaults", use_def, 0)
t = set_tag(t, "MembraneCapacity", cap, 0)
t = set_tag(t, "SynapseDissociationTC", dissoc, 0)
pp.write_text(t, encoding="utf-8")
m = mp.read_text(encoding="utf-8")
m = re.sub(r'(<Neuron Class=")[^"]+(">)', rf'\g<1>{neuron}\2', m, count=1)
m = set_tag(m, "NeuronClassName", neuron, 0)
m = set_tag(m, "UseElementDefaults", use_def, 0)
m = set_tag(m, "MembraneCapacity", cap, 0)
m = set_tag(m, "SynapseDissociationTC", dissoc, 0)
m = re.sub(r'(NeuronTimeLearner\.Neuron\.Dendrite\d+)_\d+(\.ExcSynapse)', r'\1_1\2', m)
mp.write_text(m, encoding="utf-8")
PY
  printf "%s\t%s\t%s\t%s\n" "$exp" "$neuron" "$span" "$kind" >> "$META"
done

echo "FastSpan setup done."

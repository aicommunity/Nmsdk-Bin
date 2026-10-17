#!/usr/bin/env bash
# Create 9-cell DissociationTC x Capacity grid (cold Train + Test shells).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"

# exp_dir|neuron_class|dissoc|capacity
CELLS=(
  "EXP00CtrlExp04|NSPNeuronGen|0.005|1e-9"
  "EXPD005C5e10|NSPNeuronGenD005C5e10|0.005|5e-10"
  "EXPD005C25e11|NSPNeuronGenD005C25e11|0.005|2.5e-10"
  "EXPD002C1e9|NSPNeuronGenD002C1e9|0.002|1e-9"
  "EXPD002C5e10|NSPNeuronGenD002C5e10|0.002|5e-10"
  "EXPD002C25e11|NSPNeuronGenD002C25e11|0.002|2.5e-10"
  "EXPD001C1e9|NSPNeuronGenD001C1e9|0.001|1e-9"
  "EXPD001C5e10|NSPNeuronGenD001C5e10|0.001|5e-10"
  "EXPD001C25e11|NSPNeuronGenD001C25e11|0.001|2.5e-10"
)

cold_patch_train() {
  local params="$1"
  local model="$2"
  local neuron="$3"

  python3 - "$params" "$model" "$neuron" <<'PY'
import re, sys
from pathlib import Path
params_path = Path(sys.argv[1])
model_path = Path(sys.argv[2])
neuron = sys.argv[3]
t = params_path.read_text(encoding="utf-8")

def set_tag(text, tag, value, count=0):
    """count=0 means replace all."""
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count)

t = set_tag(t, "IsNeedToTrain", "1", count=1)
t = re.sub(
    r"(<NeuronTimeLearner\b[\s\S]*?<StructureBuildMode Type=\"i\" PType=\"257\" IoType=\"17\">)[0-9](</StructureBuildMode>)",
    r"\g<1>1\2",
    t,
    count=1,
)
t = set_tag(t, "NeuronClassName", neuron, count=1)
t = set_tag(t, "SynapseClassName", "NPSynapseBio", count=1)
t = set_tag(t, "SyncTolerance", "0.01", count=1)
t = set_tag(t, "ResistanceAdjustGain", "0.4", count=1)
t = set_tag(t, "Delay", "1.5", count=1)
t = set_tag(t, "FixedLTZThreshold", "0.0115", count=1)
t = set_tag(t, "TrainingLTZThreshold", "100", count=1)
t = set_tag(t, "UseAverageLTZonePotential", "1", count=1)
t = set_tag(t, "TipSynapseResistance", "86000000 86000000 86000000 86000000", count=1)
t = set_tag(t, "DendriteLength", "1 1 1 1", count=1)
t = set_tag(t, "InitialSomaPotential", "0 0 0 0", count=1)
# Nested learner neuron lengths if present
t = set_tag(t, "NumDendriteMembranePartsVec", "1 1 1 1", count=0)

if re.search(r"<ResetToUntrainedState\b", t):
    t = set_tag(t, "ResetToUntrainedState", "1", count=1)
else:
    t = re.sub(
        r"(<IsNeedToTrain Type=\"b\" PType=\"257\" IoType=\"17\">1</IsNeedToTrain>)",
        r'\1\n\t\t\t\t\t<ResetToUntrainedState Type="b" PType="257" IoType="17">1</ResetToUntrainedState>',
        t,
        count=1,
    )

params_path.write_text(t, encoding="utf-8")

# Model must match NeuronClassName on first BuildStructure — otherwise template
# NSPNeuronGen is built first and switching class breaks tip links (amp=0).
m = model_path.read_text(encoding="utf-8")
m = re.sub(r'(<Neuron Class=")[^"]+(">)', rf'\g<1>{neuron}\2', m, count=1)
m = set_tag(m, "NeuronClassName", neuron, count=0)
m = set_tag(m, "NumDendriteMembranePartsVec", "1 1 1 1", count=0)
m = set_tag(m, "DendriteLength", "1 1 1 1", count=0)
m = set_tag(m, "TipSynapseResistance", "86000000 86000000 86000000 86000000", count=0)
# Point tip links at segment _1 (cold L=1)
m = re.sub(r'(NeuronTimeLearner\.Neuron\.Dendrite\d+)_\d+(\.ExcSynapse)', r'\1_1\2', m)
model_path.write_text(m, encoding="utf-8")
PY
}

post_sync_patch_test() {
  local train="$1"
  local test="$2"
  local neuron="$3"
  python3 - "$train/Parameters_00.xml" "$test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
train = Path(sys.argv[1]).read_text(encoding="utf-8")
tp = Path(sys.argv[2])
test = tp.read_text(encoding="utf-8")
neuron = sys.argv[3]

def set_tag(text, tag, value, count=1):
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count)

def get_tag(text, tag):
    m = re.search(rf"<{tag}\b[^>]*>([^<]*)</{tag}>", text)
    return m.group(1) if m else None

test = set_tag(test, "NeuronClassName", neuron)
test = set_tag(test, "SyncTolerance", "0.01")
flt = get_tag(train, "FixedLTZThreshold")
if flt:
    test = set_tag(test, "FixedLTZThreshold", flt)
tp.write_text(test, encoding="utf-8")
PY
}

META="$ROOT/grid_cells.tsv"
printf "exp\tneuron_class\tdissoc\tcapacity\n" > "$META"

for cell in "${CELLS[@]}"; do
  IFS='|' read -r exp neuron dissoc cap <<<"$cell"
  echo "=== setup $exp ($neuron) ==="
  "$SCR" train "$ROOT/$exp/Train" "${exp}_Train"
  "$SCR" test  "$ROOT/$exp/Test"  "${exp}_Test"
  cold_patch_train "$ROOT/$exp/Train/Parameters_00.xml" "$ROOT/$exp/Train/Model_00.xml" "$neuron"
  "$SCR" sync "$ROOT/$exp/Train" "$ROOT/$exp/Test"
  post_sync_patch_test "$ROOT/$exp/Train" "$ROOT/$exp/Test" "$neuron"
  printf "%s\t%s\t%s\t%s\n" "$exp" "$neuron" "$dissoc" "$cap" >> "$META"
done

echo "Grid ready under $ROOT ($(wc -l < "$META") lines in grid_cells.tsv)"

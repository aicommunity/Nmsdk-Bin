#!/usr/bin/env bash
# Tier B2: Branch learner + fast neuron on compressed spans with AutoCalibrate LTZ.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GRID="$ROOT/BranchFastSpan"
COPY="$ROOT/scripts/copy_config_branch.sh"
PY_PATCH="$ROOT/scripts/patch_pattern_scale.py"
LTZ_TRAIN="$ROOT/scripts/patch_ltz_calibrate_train.py"
VERIFY="$ROOT/scripts/verify_pattern_span.py"
WATCH_PATCH="$ROOT/scripts/patch_watch_pattern_legend.py"
META="$ROOT/grid_branch.tsv"

FAST="NSPNeuronGenD002C25e11"

set_project_name() {
  local ini="$1" name="$2"
  [[ -f "$ini" ]] && sed -i "s|<ProjectName>[^<]*</ProjectName>|<ProjectName>${name}</ProjectName>|" "$ini"
}

cold_patch_branch() {
  local params="$1" model="$2" neuron="$3"
  python3 - "$params" "$model" "$neuron" <<'PY'
import re, sys
from pathlib import Path
params_path, model_path = Path(sys.argv[1]), Path(sys.argv[2])
neuron = sys.argv[3]
t = params_path.read_text(encoding="utf-8")
def set_tag(text, tag, value, count=1):
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count)
t = set_tag(t, "IsNeedToTrain", "1", 1)
t = set_tag(t, "StructureBuildMode", "1", 1)
t = set_tag(t, "NeuronClassName", neuron, 1)
t = set_tag(t, "SynapseClassName", "NPSynapseBio", 1)
t = set_tag(t, "ResistanceAdjustGain", "0.4", 1)
t = set_tag(t, "Delay", "1.5", 1)
t = set_tag(t, "TrainingLTZThreshold", "100", 1)
t = set_tag(t, "UseAverageLTZonePotential", "1", 1)
t = set_tag(t, "TipSynapseResistance", "86000000 86000000 86000000 86000000", 1)
t = set_tag(t, "DendriteLength", "1 1 1 1", 1)
t = set_tag(t, "InitialSomaPotential", "0 0 0 0", 1)
t = set_tag(t, "UseElementDefaults", "1", 0)
t = set_tag(t, "MembraneCapacity", "2.5e-10", 0)
t = set_tag(t, "SynapseDissociationTC", "0.002", 0)
if re.search(r"<ResetToUntrainedState\b", t):
    t = set_tag(t, "ResetToUntrainedState", "1", 1)
params_path.write_text(t, encoding="utf-8")
m = model_path.read_text(encoding="utf-8")
m = re.sub(r'(<Neuron Class=")[^"]+(">)', rf'\g<1>{neuron}\2', m, count=1)
def set_tag_m(text, tag, value, count=0):
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count or 0)
m = set_tag_m(m, "NeuronClassName", neuron, 0)
model_path.write_text(m, encoding="utf-8")
PY
}

declare -a CELLS=(
  "EXP_branch_span100_gen|${FAST}|100|branch_ltzcal"
  "EXP_branch_span25_gen|${FAST}|25|branch_ltzcal"
)

printf "exp\tneuron\tspan_ms\tkind\n" > "$META"

for cell in "${CELLS[@]}"; do
  IFS='|' read -r exp neuron span kind <<<"$cell"
  train="$GRID/$exp/Train"
  test="$GRID/$exp/Test"
  echo "=== setup $exp ==="
  mkdir -p "$train" "$test"
  "$COPY" train "$train" "${exp}_Train"
  "$COPY" test "$test" "${exp}_Test"
  cold_patch_branch "$train/Parameters_00.xml" "$train/Model_00.xml" "$neuron"
  python3 "$LTZ_TRAIN" "$train/Parameters_00.xml"
  python3 "$PY_PATCH" "$train/Parameters_00.xml" "$train/Model_00.xml" \
    "$test/Parameters_00.xml" "$test/Model_00.xml" --span-ms "$span"
  python3 - "$test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
pp, neuron = Path(sys.argv[1]), sys.argv[2]
def set_tag(text, tag, value, count=1):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count)
t = pp.read_text(encoding="utf-8")
t = set_tag(t, "NeuronClassName", neuron, 1)
t = set_tag(t, "UseElementDefaults", "1", 0)
t = set_tag(t, "MembraneCapacity", "2.5e-10", 0)
t = set_tag(t, "SynapseDissociationTC", "0.002", 0)
t = set_tag(t, "IsNeedToTrain", "0", 1)
t = set_tag(t, "StructureBuildMode", "0", 1)
pp.write_text(t, encoding="utf-8")
PY
  set_project_name "$train/Project.ini" "${exp}_Train"
  set_project_name "$test/Project.ini" "${exp}_Test"
  printf "%s\t%s\t%s\t%s\n" "$exp" "$neuron" "$span" "$kind" >> "$META"
done

python3 "$VERIFY" --meta "$META" "$GRID"/EXP_*/Train/Parameters_00.xml "$GRID"/EXP_*/Test/Parameters_00.xml
python3 "$WATCH_PATCH" "$GRID"/EXP_*/Train/Interface.xml "$GRID"/EXP_*/Test/Interface.xml 2>/dev/null || true
echo "BranchFastSpan setup done."
cat "$META"

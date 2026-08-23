#!/usr/bin/env bash
# RegressionFull480: baseline gen + preinh25 on full480 pattern, AutoCalibrate LTZ.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REG="$ROOT/RegressionFull480"
PREINH="$ROOT/../SelectivityPresynapticInhib"
COPY="$ROOT/scripts/copy_config.sh"
LTZ_PATCH="$ROOT/scripts/patch_ltz_calibrate.py"
INJECT="$ROOT/scripts/inject_analyzer.py"
META="$ROOT/grid_regression.tsv"
EXCLUDE=(--exclude='EventsLog' --exclude='StatisticLog' --exclude='History.xml'
         --exclude='settings.qt' --exclude='SelectivityLog')

cold_patch_baseline() {
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

def ensure_tag(text, tag, typ, value, anchor):
    if re.search(rf"<{tag}\b", text):
        return set_tag(text, tag, value, 0)
    ins = f'\t\t\t\t\t<{tag} Type="{typ}" PType="257" IoType="17">{value}</{tag}>'
    pat = rf"(<{anchor}\b[^>]*>[^<]*</{anchor}>)"
    return re.sub(pat, rf"\1\n{ins}", text, count=1)

t = set_tag(t, "IsNeedToTrain", "1", 1)
t = set_tag(t, "StructureBuildMode", "1", 1)
t = set_tag(t, "NeuronClassName", neuron, 1)
t = set_tag(t, "SynapseClassName", "NPSynapseBio", 1)
t = set_tag(t, "SyncTolerance", "0.02", 1)
t = ensure_tag(t, "PeakMeasureMargin", "d", "0.06", "SyncTolerance")
t = set_tag(t, "Delay", "1.5", 1)
t = set_tag(t, "ResistanceAdjustGain", "0.4", 1)
t = set_tag(t, "TrainingLTZThreshold", "100", 1)
t = set_tag(t, "UseAverageLTZonePotential", "1", 0)
t = set_tag(t, "TipSynapseResistance", "86000000 86000000 86000000 86000000", 1)
t = set_tag(t, "DendriteLength", "1 1 1 1", 1)
t = set_tag(t, "InitialSomaPotential", "0 0 0 0", 1)
t = set_tag(t, "UseElementDefaults", "0", 0)
t = set_tag(t, "LTZThreshold", "100", 1)
t = set_tag(t, "FixedLTZThreshold", "0.0115", 1)
params_path.write_text(t, encoding="utf-8")

m = model_path.read_text(encoding="utf-8")
m = re.sub(r'(<Neuron Class=")[^"]+(">)', rf'\g<1>{neuron}\2', m, count=1)
def set_tag_m(text, tag, value, count=0):
    pat = rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)"
    return re.sub(pat, rf"\g<1>{value}\2", text, count=count or 0)
m = set_tag_m(m, "NeuronClassName", neuron, 0)
m = set_tag_m(m, "DendriteLength", "1 1 1 1", 0)
m = set_tag_m(m, "TipSynapseResistance", "86000000 86000000 86000000 86000000", 0)
m = re.sub(r'(NeuronTimeLearner\.Neuron\.Dendrite\d+)_\d+(\.ExcSynapse)', r'\1_1\2', m)
m = re.sub(r'(NeuronTimeLearner\.Neuron\.Dendrite\d+)_\d+(\.InhSynapse)', r'\1_1\2', m)
model_path.write_text(m, encoding="utf-8")
PY
}

setup_exp() {
  local exp="$1" neuron="$2" golden_exp="$3"
  local train="$REG/$exp/Train"
  local test="$REG/$exp/Test"
  local golden_train="$PREINH/${golden_exp}/Train"
  local golden_test="$PREINH/${golden_exp}/Test"
  echo "=== setup $exp ($neuron) from $golden_exp ==="
  mkdir -p "$train" "$test"
  rsync -a "${EXCLUDE[@]}" "$golden_train/" "$train/"
  rsync -a "${EXCLUDE[@]}" "$golden_test/" "$test/"
  sed -i "s|<ProjectName>[^<]*</ProjectName>|<ProjectName>${exp}_Train</ProjectName>|" "$train/Project.ini"
  sed -i "s|<ProjectName>[^<]*</ProjectName>|<ProjectName>${exp}_Test</ProjectName>|" "$test/Project.ini"
  cold_patch_baseline "$train/Parameters_00.xml" "$train/Model_00.xml" "$neuron"
  python3 "$LTZ_PATCH" "$train/Parameters_00.xml"
  python3 "$INJECT" "$train/Model_00.xml" "$test/Model_00.xml"
  python3 - "$test/Parameters_00.xml" "$neuron" <<'PY'
import re, sys
from pathlib import Path
pp, neuron = Path(sys.argv[1]), sys.argv[2]
def set_tag(text, tag, value, count=1):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count)
t = pp.read_text(encoding="utf-8")
t = set_tag(t, "NeuronClassName", neuron, 1)
t = set_tag(t, "IsNeedToTrain", "0", 1)
t = set_tag(t, "StructureBuildMode", "0", 1)
t = set_tag(t, "UseElementDefaults", "0", 0)
pp.write_text(t, encoding="utf-8")
PY
  if grep -q 'StructureBuildMode' "$test/Parameters_00.xml"; then
    sed -i 's|<StructureBuildMode Type="i" PType="257" IoType="17">[0-9]</StructureBuildMode>|<StructureBuildMode Type="i" PType="257" IoType="17">0</StructureBuildMode>|g' "$test/Parameters_00.xml"
  fi
  python3 "$ROOT/scripts/patch_test_model.py" "$test/Model_00.xml"
}

setup_exp EXP_baseline_gen NSPNeuronGen EXP00_baseline_margprops
setup_exp EXP_baseline_preinh25 NSPNeuronGenPreinh2_5 EXP04_preinh_250_margprops

echo "Regression setup done. Meta: $META"
cat "$META"

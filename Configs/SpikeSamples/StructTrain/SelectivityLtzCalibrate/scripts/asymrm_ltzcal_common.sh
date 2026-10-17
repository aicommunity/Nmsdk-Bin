# Shared Pack A cold-patch helpers (parity with SelectivityAsymRm/setup_asymrm.sh).
# Source from setup_asymrm_ltzcal.sh / reset_asymrm_ltzcal_cold.sh — do not execute directly.

asymrm_ltzcal_cold_patch() {
  local params="$1" model="$2" neuron="$3"
  local dissoc="${4:-0.001}" cap="${5:-2.5e-11}" secr="${6:-0.001}"
  local exc_rm="${7:-1e7}" inh_rm="${8:-1e8}" exc_rsyn="${9:-8.6e7}" inh_rsyn="${10:-8.6e8}" tip="${11:-86000000}"
  python3 - "$params" "$model" "$neuron" "1" "$dissoc" "$cap" "$secr" \
    "$exc_rm" "$inh_rm" "$exc_rsyn" "$inh_rsyn" "$tip" <<'PY'
import re, sys
from pathlib import Path
params_path, model_path = Path(sys.argv[1]), Path(sys.argv[2])
neuron, use_def, dissoc, cap, secr = sys.argv[3:8]
exc_rm, inh_rm, exc_rsyn, inh_rsyn, tip = sys.argv[8:13]

def set_tag(text, tag, value, count=1):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count)

def ensure_after(text, after, tag, value):
    if re.search(rf"<{tag}\b", text):
        return set_tag(text, tag, value, 0)
    return re.sub(
        rf"(<{after}\b[^>]*>[^<]*</{after}>)",
        rf'\1\n\t\t\t\t\t\t\t<{tag} Type="d" PType="257" IoType="17">{value}</{tag}>',
        text, count=1,
    )

def patch(t):
    t = set_tag(t, "IsNeedToTrain", "1", count=1)
    t = set_tag(t, "StructureBuildMode", "1", count=1)
    t = set_tag(t, "NeuronClassName", neuron, count=1)
    t = set_tag(t, "SynapseClassName", "NPSynapseBio", count=1)
    tip4 = f"{tip} {tip} {tip} {tip}"
    t = set_tag(t, "TipSynapseResistance", tip4, count=1)
    t = set_tag(t, "DendriteLength", "1 1 1 1", count=1)
    t = set_tag(t, "NumDendriteMembranePartsVec", "1 1 1 1", count=0)
    t = set_tag(t, "InitialSomaPotential", "0 0 0 0", count=1)
    if re.search(r"<ResetToUntrainedState\b", t):
        t = set_tag(t, "ResetToUntrainedState", "1", count=1)
    t = set_tag(t, "UseElementDefaults", use_def, count=0)
    t = set_tag(t, "MembraneCapacity", cap, count=0)
    t = set_tag(t, "SynapseDissociationTC", dissoc, count=0)
    for tag, val in [
        ("SynapseSecretionTC", secr),
        ("ExcMembraneResistance", exc_rm),
        ("InhMembraneResistance", inh_rm),
        ("ExcSynapseResistance", exc_rsyn),
        ("InhSynapseResistance", inh_rsyn),
    ]:
        t = ensure_after(t, "SynapseDissociationTC", tag, val)
    return t

t = patch(params_path.read_text(encoding="utf-8"))
params_path.write_text(t, encoding="utf-8")

m = model_path.read_text(encoding="utf-8")
m = re.sub(r'(<Neuron Class=")[^"]+(">)', rf'\g<1>{neuron}\2', m, count=1)
m = patch(m)
m = re.sub(r'(NeuronTimeLearner\.Neuron\.Dendrite\d+)_\d+(\.ExcSynapse)', r'\1_1\2', m)
m = re.sub(r'(NeuronTimeLearner\.Neuron\.Dendrite\d+)_\d+(\.InhSynapse)', r'\1_1\2', m)
model_path.write_text(m, encoding="utf-8")
PY
}

asymrm_ltzcal_patch_test_cold() {
  local test_params="$1" neuron="$2" cap="$3" exc_rm="$4" inh_rm="$5" exc_rsyn="$6" inh_rsyn="$7" tip="$8"
  python3 - "$test_params" "$neuron" "$cap" "$exc_rm" "$inh_rm" "$exc_rsyn" "$inh_rsyn" "$tip" <<'PY'
import re, sys
from pathlib import Path
def set_tag(text, tag, value, count=1):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count)
def ensure_after(text, after, tag, value):
    if re.search(rf"<{tag}\b", text):
        return set_tag(text, tag, value, 0)
    return re.sub(rf"(<{after}\b[^>]*>[^<]*</{after}>)",
                  rf'\1\n\t\t\t\t\t\t\t<{tag} Type="d" PType="257" IoType="17">{value}</{tag}>', text, count=1)
pp = Path(sys.argv[1])
neuron, cap, exc_rm, inh_rm, exc_rsyn, inh_rsyn, tip = sys.argv[2:9]
t = pp.read_text(encoding="utf-8")
t = set_tag(t, "NeuronClassName", neuron, 1)
t = set_tag(t, "UseElementDefaults", "1", 0)
t = set_tag(t, "MembraneCapacity", cap, 0)
t = set_tag(t, "SynapseDissociationTC", "0.001", 0)
for tag, val in [("SynapseSecretionTC","0.001"),("ExcMembraneResistance",exc_rm),
                 ("InhMembraneResistance",inh_rm),("ExcSynapseResistance",exc_rsyn),
                 ("InhSynapseResistance",inh_rsyn)]:
    t = ensure_after(t, "SynapseDissociationTC", tag, val)
t = set_tag(t, "IsNeedToTrain", "0", 1)
t = set_tag(t, "StructureBuildMode", "0", 1)
tip4 = f"{tip} {tip} {tip} {tip}"
t = set_tag(t, "TipSynapseResistance", tip4, 1)
t = set_tag(t, "DendriteLength", "1 1 1 1", 1)
pp.write_text(t, encoding="utf-8")
PY
}

asymrm_ltzcal_clear_runtime() {
  local dir="$1"
  rm -rf "$dir/History.xml" "$dir/StatisticLog" "$dir/EventsLog" "$dir/SelectivityLog" \
    "$dir/run_console.log" "$dir/run_console_t"*.log "$dir/settings.qt" 2>/dev/null || true
}

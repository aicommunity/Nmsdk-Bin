#!/usr/bin/env bash
# Cold-patch SelectivityAsymRm: 18 EXP = pack A/B/C × span 100/50/25 × gen|preinh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY_PATCH="$ROOT/scripts/patch_pattern_scale.py"
INJECT="$ROOT/scripts/inject_analyzer.py"
COPY="$ROOT/scripts/copy_config.sh"
VERIFY="$ROOT/scripts/verify_pattern_span.py"
VERIFY_EL="$ROOT/scripts/verify_element_params.py"
WATCH_PATCH="$ROOT/scripts/patch_watch_pattern_legend.py"
META="$ROOT/grid_cells.tsv"
GTS=20000

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

cold_patch() {
  local params="$1" model="$2" neuron="$3" use_defaults="$4"
  local dissoc="$5" cap="$6" secr="$7"
  local exc_rm="$8" inh_rm="$9" exc_rsyn="${10}" inh_rsyn="${11}" tip="${12}"
  python3 - "$params" "$model" "$neuron" "$use_defaults" "$dissoc" "$cap" "$secr" \
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

printf "exp\tneuron\tspan_ms\tkind\tpack\tcap\texc_rm\texc_rsyn\n" > "$META"

# pack|neuron_gen|neuron_pre|cap|exc_rm|inh_rm|exc_rsyn|inh_rsyn|tip
PACKS=(
  "A|NSPNeuronGenAsymRmD001C25e12|NSPNeuronGenPreinh2_5AsymRmD001C25e12|2.5e-11|1e7|1e8|8.6e7|8.6e8|86000000"
  "B|NSPNeuronGenAsymRmD001C1e11|NSPNeuronGenPreinh2_5AsymRmD001C1e11|1e-11|1e7|1e8|5e7|5e8|50000000"
  "C|NSPNeuronGenAsymRmD001C25e12Rm5e6|NSPNeuronGenPreinh2_5AsymRmD001C25e12Rm5e6|2.5e-11|5e6|5e7|8.6e7|8.6e8|86000000"
)
SPANS=(100 50 25)

for prow in "${PACKS[@]}"; do
  IFS='|' read -r pack ngen npre cap exc_rm inh_rm exc_rsyn inh_rsyn tip <<<"$prow"
  for span in "${SPANS[@]}"; do
    for kind in gen preinh; do
      if [[ "$kind" == gen ]]; then neuron="$ngen"; else neuron="$npre"; fi
      exp="EXP_span${span}ms_pack${pack}_${kind}"
      echo "=== setup $exp ==="
      train="$ROOT/$exp/Train"
      test="$ROOT/$exp/Test"
      mkdir -p "$train" "$test"
      "$COPY" train "$train" "${exp}_Train"
      "$COPY" test "$test" "${exp}_Test"

      cold_patch "$train/Parameters_00.xml" "$train/Model_00.xml" "$neuron" "1" \
        "0.001" "$cap" "0.001" "$exc_rm" "$inh_rm" "$exc_rsyn" "$inh_rsyn" "$tip"

      python3 "$PY_PATCH" "$train/Parameters_00.xml" "$train/Model_00.xml" \
        "$test/Parameters_00.xml" "$test/Model_00.xml" --span-ms "$span"

      python3 "$INJECT" "$train/Model_00.xml" "$test/Model_00.xml"

      python3 - "$test/Parameters_00.xml" "$neuron" "$cap" "$exc_rm" "$inh_rm" "$exc_rsyn" "$inh_rsyn" "$tip" <<'PY'
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

      set_project_name "$train/Project.ini" "${exp}_Train"
      set_project_name "$test/Project.ini" "${exp}_Test"
      set_timestep "$train/Project.ini" "$GTS"
      set_timestep "$test/Project.ini" "$GTS"

      cat >"$train/README.md" <<EOF2
## ${exp} — Train
NeuronClass=\`${neuron}\` pack=${pack} kind=${kind} span=${span}ms GTS=${GTS}
C=${cap} ExcRm=${exc_rm} InhRm=${inh_rm} ExcRsyn=${exc_rsyn} InhRsyn=${inh_rsyn}
EOF2
      cp "$train/README.md" "$test/README.md"
      sed -i 's/Train/Test/' "$test/README.md"

      printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
        "$exp" "$neuron" "$span" "$kind" "$pack" "$cap" "$exc_rm" "$exc_rsyn" >> "$META"

      # element verify after train cold_patch (Model may not have applied until train run)
      python3 "$VERIFY" --meta "$META" "$train/Parameters_00.xml" "$test/Parameters_00.xml"
    done
  done
done

echo "=== patch Watch Interface ==="
mapfile -t IFACES < <(find "$ROOT" -path '*/EXP_*/Train/Interface.xml' -o -path '*/EXP_*/Test/Interface.xml' | sort)
if ((${#IFACES[@]})); then
  python3 "$WATCH_PATCH" "${IFACES[@]}" || true
fi

echo "=== final span verify ==="
python3 "$VERIFY" --meta "$META" "$ROOT"/EXP_*/Train/Parameters_00.xml "$ROOT"/EXP_*/Test/Parameters_00.xml
echo "AsymRm setup done. Meta:"
cat "$META"

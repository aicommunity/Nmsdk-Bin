#!/usr/bin/env bash
# AsymRmLtzCalBranch: Branch learner + Pack A AsymRm × span 100/50/25 × gen|preinh + CalibrateLtz.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GRID="$ROOT/AsymRmLtzCalBranch"
COPY="$ROOT/scripts/copy_config_branch.sh"
PY_PATCH="$ROOT/scripts/patch_pattern_scale.py"
LTZ_TRAIN="$ROOT/scripts/patch_ltz_calibrate_train.py"
VERIFY="$ROOT/scripts/verify_pattern_span.py"
WATCH_PATCH="$ROOT/scripts/patch_watch_pattern_legend.py"
META="$GRID/grid_cells.tsv"
GTS=2000

GEN="NSPNeuronGenAsymRmD001C25e12"
PRE="NSPNeuronGenPreinh2_5AsymRmD001C25e12"
CAP="2.5e-11"
EXC_RM="1e7"
INH_RM="1e8"
EXC_RSYN="8.6e7"
INH_RSYN="8.6e8"
TIP="86000000"

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

cold_patch_branch_pack_a() {
  local params="$1" model="$2" neuron="$3"
  python3 - "$params" "$model" "$neuron" "$CAP" "$EXC_RM" "$INH_RM" "$EXC_RSYN" "$INH_RSYN" "$TIP" <<'PY'
import re, sys
from pathlib import Path
params_path, model_path = Path(sys.argv[1]), Path(sys.argv[2])
neuron, cap, exc_rm, inh_rm, exc_rsyn, inh_rsyn, tip = sys.argv[3:10]

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
    t = set_tag(t, "InitialSomaPotential", "0 0 0 0", count=1)
    t = set_tag(t, "ResistanceAdjustGain", "0.4", count=1)
    t = set_tag(t, "Delay", "1.5", count=1)
    t = set_tag(t, "TrainingLTZThreshold", "100", count=1)
    t = set_tag(t, "UseAverageLTZonePotential", "1", count=1)
    if re.search(r"<ResetToUntrainedState\b", t):
        t = set_tag(t, "ResetToUntrainedState", "1", count=1)
    else:
        t = ensure_after(t, "IsNeedToTrain", "ResetToUntrainedState", "1")
    t = set_tag(t, "UseElementDefaults", "1", count=0)
    t = set_tag(t, "MembraneCapacity", cap, count=0)
    t = set_tag(t, "SynapseDissociationTC", "0.001", count=0)
    for tag, val in [
        ("SynapseSecretionTC", "0.001"),
        ("ExcMembraneResistance", exc_rm),
        ("InhMembraneResistance", inh_rm),
        ("ExcSynapseResistance", exc_rsyn),
        ("InhSynapseResistance", inh_rsyn),
    ]:
        t = ensure_after(t, "SynapseDissociationTC", tag, val)
    return t

params_path.write_text(patch(params_path.read_text(encoding="utf-8")), encoding="utf-8")
m = model_path.read_text(encoding="utf-8")
m = re.sub(r'(<Neuron Class=")[^"]+(">)', rf'\g<1>{neuron}\2', m, count=1)
m = patch(m)
model_path.write_text(m, encoding="utf-8")
PY
}

mkdir -p "$GRID"
printf "exp\tneuron\tspan_ms\tkind\tpack\tcap\texc_rm\texc_rsyn\n" > "$META"

declare -a CELLS=(
  "EXP_branch_span100_packA_gen|${GEN}|100|gen"
  "EXP_branch_span100_packA_preinh|${PRE}|100|preinh"
  "EXP_branch_span50_packA_gen|${GEN}|50|gen"
  "EXP_branch_span50_packA_preinh|${PRE}|50|preinh"
  "EXP_branch_span25_packA_gen|${GEN}|25|gen"
  "EXP_branch_span25_packA_preinh|${PRE}|25|preinh"
)

for cell in "${CELLS[@]}"; do
  IFS='|' read -r exp neuron span kind <<<"$cell"
  train="$GRID/$exp/Train"
  test="$GRID/$exp/Test"
  echo "=== setup $exp ==="
  mkdir -p "$train" "$test"
  "$COPY" train "$train" "${exp}_Train"
  "$COPY" test "$test" "${exp}_Test"
  cold_patch_branch_pack_a "$train/Parameters_00.xml" "$train/Model_00.xml" "$neuron"
  if [[ "$kind" == preinh ]]; then
    python3 "$LTZ_TRAIN" --preinh "$train/Parameters_00.xml"
  else
    python3 "$LTZ_TRAIN" "$train/Parameters_00.xml"
  fi
  python3 "$PY_PATCH" "$train/Parameters_00.xml" "$train/Model_00.xml" \
    "$test/Parameters_00.xml" "$test/Model_00.xml" --span-ms "$span"
  python3 - "$test/Parameters_00.xml" "$neuron" "$CAP" "$EXC_RM" "$INH_RM" \
    "$EXC_RSYN" "$INH_RSYN" "$TIP" <<'PY'
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
  printf "%s\t%s\t%s\t%s\tA\t%s\t%s\t%s\n" \
    "$exp" "$neuron" "$span" "$kind" "$CAP" "$EXC_RM" "$EXC_RSYN" >> "$META"
done

python3 "$VERIFY" --meta "$META" "$GRID"/EXP_*/Train/Parameters_00.xml "$GRID"/EXP_*/Test/Parameters_00.xml
python3 "$WATCH_PATCH" "$GRID"/EXP_*/Train/Interface.xml "$GRID"/EXP_*/Test/Interface.xml 2>/dev/null || true
echo "AsymRmLtzCalBranch setup done."
cat "$META"

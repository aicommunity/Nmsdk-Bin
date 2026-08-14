#!/usr/bin/env bash
# EXP02 GUI-trained weights + autothr recalibration (no cold reset).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_TRAIN="$ROOT/EXP02_preinh_100/Train"
DST="$ROOT/EXP02_preinh_100_gui_autothr"
SCR="$ROOT/scripts/copy_config.sh"
PATCH_AUTO="$ROOT/scripts/patch_autothr.py"
PATCH_NEU="$ROOT/scripts/patch_neuron_class.py"

rm -rf "$DST"
mkdir -p "$DST"
rsync -a --exclude='EventsLog' --exclude='StatisticLog' --exclude='settings.qt' \
  "$SRC_TRAIN/" "$DST/Train/"
"$SCR" test "$DST/Test" "EXP02_preinh_100_gui_autothr_Test"

python3 "$PATCH_AUTO" "$DST/Train/Parameters_00.xml"
python3 "$PATCH_NEU" "$DST/Test/Parameters_00.xml" NSPNeuronGenPreinh

python3 - <<PY
from pathlib import Path
import re
p = Path("$DST/Train/Parameters_00.xml")
text = p.read_text(encoding="utf-8")
# Re-run training from saved weights to trigger EndOfLearning + autothr
text = re.sub(r'<IsNeedToTrain Type="b" PType="257" IoType="17">[01]</IsNeedToTrain>',
              '<IsNeedToTrain Type="b" PType="257" IoType="17">1</IsNeedToTrain>', text, count=1)
text = re.sub(r'<StructureBuildMode Type="i" PType="257" IoType="17">[0-9]</StructureBuildMode>',
              '<StructureBuildMode Type="i" PType="257" IoType="17">0</StructureBuildMode>', text, count=1)
text = re.sub(r'<ResetToUntrainedState Type="b" PType="257" IoType="17">[01]</ResetToUntrainedState>',
              '<ResetToUntrainedState Type="b" PType="257" IoType="17">0</ResetToUntrainedState>', text, count=1)
if "ResetToUntrainedState" not in text:
    text = text.replace(
        '<IsNeedToTrain Type="b" PType="257" IoType="17">1</IsNeedToTrain>',
        '<IsNeedToTrain Type="b" PType="257" IoType="17">1</IsNeedToTrain>\n'
        '\t\t\t\t\t<ResetToUntrainedState Type="b" PType="257" IoType="17">0</ResetToUntrainedState>',
        1)
text = re.sub(r'<TrainingPhase Type="i" PType="257" IoType="17">[^<]*</TrainingPhase>',
              '<TrainingPhase Type="i" PType="257" IoType="17">0</TrainingPhase>', text, count=1)
p.write_text(text, encoding="utf-8")
PY

cat > "$DST/README.md" << 'MD'
# EXP02_preinh_100_gui_autothr

Копия GUI-обученного [`EXP02_preinh_100/Train`](../EXP02_preinh_100/Train/) (L=`[49,44,25,1]`).

- `AutoCalibrateFixedLTZThreshold=1`, cold reset **выключен**
- `IsNeedToTrain=1`, `StructureBuildMode=0` — один проход train для калибровки порога на готовых весах
MD

echo "Setup $DST"
echo "Run: NeuroModelerConsole -c $DST/Train/Project.ini -s -t 600 -x -S"

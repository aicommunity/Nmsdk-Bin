#!/usr/bin/env bash
# Setup all Phase A experiment config folders.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCR="$ROOT/scripts/copy_config.sh"
TRAIN_SRC="/home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearner/Parameters_00.xml"

setup_exp00() {
  $SCR train "$ROOT/EXP00_baseline/Train" EXP00_baseline_Train
  $SCR test  "$ROOT/EXP00_baseline/Test"  EXP00_baseline_Test
  cp "$TRAIN_SRC" "$ROOT/EXP00_baseline/Train/Parameters_00.xml"
  $SCR sync "$ROOT/EXP00_baseline/Train" "$ROOT/EXP00_baseline/Test"
}

setup_exp01_thr() {
  local thr="$1"
  local dir="$ROOT/EXP01_ltz_threshold_sweep/Test_thr${thr//./}"
  $SCR test "$dir" "EXP01_Test_thr${thr//./}"
  $SCR sync "$ROOT/EXP00_baseline/Train" "$dir"
  sed -i "s|<FixedLTZThreshold Type=\"d\" PType=\"257\" IoType=\"17\">[^<]*</FixedLTZThreshold>|<FixedLTZThreshold Type=\"d\" PType=\"257\" IoType=\"17\">${thr}</FixedLTZThreshold>|g" "$dir/Parameters_00.xml"
  sed -i "s|<LTZThreshold Type=\"d\" PType=\"257\" IoType=\"17\">[^<]*</LTZThreshold>|<LTZThreshold Type=\"d\" PType=\"257\" IoType=\"17\">${thr}</LTZThreshold>|g" "$dir/Parameters_00.xml"
}

setup_exp02() {
  local avg="$1"
  local dir="$ROOT/EXP02_ltzone_average_mode/Test_avg${avg}"
  $SCR test "$dir" "EXP02_Test_avg${avg}"
  $SCR sync "$ROOT/EXP00_baseline/Train" "$dir"
  sed -i "s|<UseAverageLTZonePotential Type=\"b\" PType=\"257\" IoType=\"17\">[01]</UseAverageLTZonePotential>|<UseAverageLTZonePotential Type=\"b\" PType=\"257\" IoType=\"17\">${avg}</UseAverageLTZonePotential>|g" "$dir/Parameters_00.xml"
}

setup_retrain_exp() {
  local name="$1"
  local tol="$2"
  local gain="$3"
  $SCR train "$ROOT/${name}/Train" "${name}_Train"
  $SCR test  "$ROOT/${name}/Test"  "${name}_Test"
  sed -i 's|<ResetToUntrainedState Type="b" PType="257" IoType="17">[01]</ResetToUntrainedState>|<ResetToUntrainedState Type="b" PType="257" IoType="17">1</ResetToUntrainedState>|' "$ROOT/${name}/Train/Parameters_00.xml" || true
  sed -i 's|<IsNeedToTrain Type="b" PType="257" IoType="17">[01]</IsNeedToTrain>|<IsNeedToTrain Type="b" PType="257" IoType="17">1</IsNeedToTrain>|' "$ROOT/${name}/Train/Parameters_00.xml"
  sed -i 's|<StructureBuildMode Type="i" PType="257" IoType="17">[0-9]</StructureBuildMode>|<StructureBuildMode Type="i" PType="257" IoType="17">1</StructureBuildMode>|' "$ROOT/${name}/Train/Parameters_00.xml"
  if [[ -n "$tol" ]]; then
    sed -i "s|<SyncTolerance Type=\"d\" PType=\"257\" IoType=\"17\">[^<]*</SyncTolerance>|<SyncTolerance Type=\"d\" PType=\"257\" IoType=\"17\">${tol}</SyncTolerance>|" "$ROOT/${name}/Train/Parameters_00.xml"
  fi
  if [[ -n "$gain" ]]; then
    sed -i "s|<ResistanceAdjustGain Type=\"d\" PType=\"257\" IoType=\"17\">[^<]*</ResistanceAdjustGain>|<ResistanceAdjustGain Type=\"d\" PType=\"257\" IoType=\"17\">${gain}</ResistanceAdjustGain>|" "$ROOT/${name}/Train/Parameters_00.xml"
  fi
}

setup_exp06() {
  local tc="$1"
  local thr="$2"
  local dir="$ROOT/EXP06_ltzone_integration/Test_tc${tc//./}_thr${thr//./}"
  $SCR test "$dir" "EXP06_tc${tc//./}_thr${thr//./}"
  $SCR sync "$ROOT/EXP00_baseline/Train" "$dir"
  python3 "$ROOT/scripts/patch_ltzone_integration.py" "$dir" "$tc" "$thr"
}

setup_exp00
for thr in 0.0115 0.0120 0.0125 0.0130 0.0135; do setup_exp01_thr "$thr"; done
setup_exp02 1
setup_exp02 0
setup_retrain_exp EXP03_sync_tolerance_015 0.015 ""
setup_retrain_exp EXP04_sync_tolerance_010 0.010 ""
setup_retrain_exp EXP05_resistance_gain_025 "" 0.25
for tc in 0.001 0.00144 0.003; do
  for thr in 0.0115 0.012 0.013; do
    setup_exp06 "$tc" "$thr"
  done
done
echo "All experiment configs created under $ROOT"

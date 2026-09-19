# Post-train tuning in the teacher module (PostTune)

**Russian:** [`POST_TRAIN_TUNING.ru.md`](POST_TRAIN_TUNING.ru.md)  
**See also:** [`RELIABILITY_MAP.md`](RELIABILITY_MAP.md) §4.7 · [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md)

After length sync and amp normalize, the learner can apply the **tip-resistance + silent mid FixedLTZ** recipe inside C++ (`NNeuronTimeLearner` / `NNeuronTimeLearnerBranch`) without requiring Python `apply_tiprmin` / silent probe.

**Default: ON** (`EnablePostTrainTuning=true` in `ADefault`). Old XML without the property gets PostTune on cold retrain.

## Phases

| | TimeLearner | Branch |
|--|--|--|
| 0–1 | Sync → Normalize | same |
| 2 | Done | Done |
| 3 | **PostTune** | CalibrateLtz (legacy, tuning **OFF** only) |
| 4 | — | **PostTune** |

With tuning ON, Branch skips `ScaleTipResistancesForParallelActivation` and `kPhaseCalibrateLtz`.

## Tip modes (default CanonRmin=1)

0 Off · 1 CanonRmin `2e7×(N−1)+8.6e7` · 2 FlatLastR `8.6e7×N` · 3 KeepDone · 4 SearchSynthetic

## Synthetic foils

Target first; then shifts, adjacent swaps, ×0.5/×2, zero-one-ISI; drop empty/dupes; cap `PostTrainSyntheticFoilCount`.  
Mid: `0.5*(tgt+max_foil_below)` else `tgt*0.99`.

## Scripts

`post_train_hygiene` skips Python tiprmin when PostTune TipR already canon/flat.  
`phase8_tiprmin_gate.py --skip-tipr-mid` keeps Train TipR/mid and only overlays Test for gate.

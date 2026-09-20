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

## Mid probes (phase8 / phase9 / pack A parity)

**TipR** in Train PostTune; **silent mid** in Test inference (same C++, no Python tiprmin/mid).

| Class | Mid metric | Gate |
|-------|------------|------|
| Branch | soma peak | `phase8 --skip-tipr-mid` |
| TL | LTZ peak (Auto) | `phase9 --skip-tipr-mid` |

Train free-run may leave `FixedLTZ=1.0` when landscape is bad; Test `MaybeStartInferenceMidProbes` plays Matrix pack A as-is and writes mid + `posttune_complete.flag`. Gate two-pass when thr is silent.

SearchSynthetic keeps Training-iteration probes. Mid: `0.5*(tgt+max_foil_below)` else `tgt*0.99`.

Verify P0: Branch25 CanonRmin / off / AsymRm25 FlatLastR → fires `10000000` — [`_repro/POSTTUNE_VERIFY_RESULT.md`](_repro/POSTTUNE_VERIFY_RESULT.md).

## Scripts

`post_train_hygiene` skips Python tiprmin when PostTune TipR already canon/flat.  
`phase8_tiprmin_gate.py --skip-tipr-mid` / `phase9_preinh_bc_gate.py --skip-tipr-mid`: C++ inference mid then gate.

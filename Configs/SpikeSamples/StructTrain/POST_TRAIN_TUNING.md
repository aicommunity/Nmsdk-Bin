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

With tuning ON, Branch skips `ScaleTipResistancesForParallelActivation` during Normalize→CalibrateLtz; SearchSynthetic still runs ScaleTipR once as KeepDone revert snapshot.

## Tip modes (default CanonRmin=1)

0 Off · 1 CanonRmin `2e7×(N−1)+8.6e7` · 2 FlatLastR `8.6e7×N` · 3 KeepDone · 4 SearchSynthetic (trial BestTips if `landscape_ok`; free-run fail → `free_run_reject_best` → KeepDone/ScaleTipR)

## Timing

`AutoScaleIterationGap=true` (default): `EffectiveIterationGap = span + settle + slack` — XML `IterationGap=1.5` does not raise the floor.  
Canon: [`docs/TIMING_AND_GAP.ru.md`](docs/TIMING_AND_GAP.ru.md).

## Mid probes (phase8 / phase9 / pack A parity)

**TipR** in Train PostTune; **silent mid** in Test inference (same C++, no Python tiprmin/mid).

| Class | Mid metric | Gate |
|-------|------------|------|
| Branch | shared soma amp (`soma_amp_sum`) | `phase8 --skip-tipr-mid` |
| TL | LTZ peak (Auto) | `phase9 --skip-tipr-mid` |

Train free-run may leave `FixedLTZ=1.0` when landscape is bad; Test `MaybeStartInferenceMidProbes` plays Matrix pack A as-is and writes mid + `posttune_complete.flag`. Gate two-pass when thr is silent.

SearchSynthetic (mode=4) runs **only** in the Train PostTune loop (`PostTrainTipSearchIters=12`). BestTips update when trial `LandscapeOk` and `gap > BestGap`; after `apply_best`, Train free-run mid must also pass — else `free_run_reject_best` → snapshot (`search_reverted=1`). Train always leaves **silent** mid after Search so Test C++ inference mid can run.  
**Test-only / `--skip-train` smoke ≠ Search validation**. Accept via `posttune_verify --case br100_search` (no skip-train): TipR≠keep **or** `search_reverted=1`; mid `cpp`; fires **`10000000`**. See [`POST_TRAIN_VERIFY.ru.md`](POST_TRAIN_VERIFY.ru.md) §V5b.

Mid: `0.5*(tgt+max_foil_below)` else `tgt*0.99`.

Verify P0: Branch25 CanonRmin / off / AsymRm25 FlatLastR → fires `10000000` — [`_repro/POSTTUNE_VERIFY_RESULT.md`](_repro/POSTTUNE_VERIFY_RESULT.md).

AutoScale emergency rollback: set `AutoScaleIterationGap=0` (or ADefault false + pin on posttune clones only). See [`docs/TIMING_AND_GAP.ru.md`](docs/TIMING_AND_GAP.ru.md).

## Scripts

`post_train_hygiene` skips Python tiprmin when PostTune TipR already canon/flat.  
`phase8_tiprmin_gate.py --skip-tipr-mid` / `phase9_preinh_bc_gate.py --skip-tipr-mid`: C++ inference mid then gate.

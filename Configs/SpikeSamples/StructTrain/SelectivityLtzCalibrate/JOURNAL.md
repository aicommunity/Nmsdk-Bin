# SelectivityLtzCalibrate — журнал

## 2026-08-23

- Создана кампания `SelectivityLtzCalibrate/` по плану глубокого анализа.
- `ANALYSIS_structural_learning.md` — полный текст плана §1–§14.
- RegressionFull480: setup + run (EXP_baseline_gen, EXP_baseline_preinh25).
- FastSpanLtzCal: setup 6 EXP (span 25/50/100 × gen/preinh).
- BranchFastSpan: setup 2 EXP (span 25/100, TimeNeuronTimeLearnerBranch + D002C25e11).
- C++: `MatchMode` в `NPatternResponseAnalyzer`; `PatternRecognition()` в classic/Branch learner.

## 2026-08-23 (debt fix)

- **Sync pipeline:** `merge_train_model.py` + in-place `inject_analyzer.py` — test Model не перезаписывается train Model.
- **Cold train:** `patch_ltz_calibrate_train.py` (UseFixedLTZ=0, gap_fraction 0.85); regression setup — fresh `TimeNeuronTimeLearner/Model_00.xml` + `ResetToUntrainedState=1`.
- **Smoke sync:** `smoke_sync_regression.sh` — golden EXP00 5/8, EXP04 6/8 после sync.
- **Branch sync parity:** `copy_config_branch.sh` + `inject_analyzer_branch.py` in-place.
- **Data hygiene:** `.gitignore` для runtime; источник весов — `Train/Parameters_00.xml`.

## Backlog (вне sprint)

- B3 двухпорог LTZ; B1b soma-profile readout; C1 full PatternRecognition; C2–C4 contrastive/order readout; Tier D Exc/Inh/PeakMargin/TS10k; Full480LtzCal; A1 fallback sweep при fail autocal.

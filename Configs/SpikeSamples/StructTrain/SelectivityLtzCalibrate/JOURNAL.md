# SelectivityLtzCalibrate — журнал

## 2026-08-23

- Создана кампания `SelectivityLtzCalibrate/` по плану глубокого анализа.
- `ANALYSIS_structural_learning.md` — полный текст плана §1–§14.
- RegressionFull480: setup + run (EXP_baseline_gen, EXP_baseline_preinh25).
- FastSpanLtzCal: setup 6 EXP (span 25/50/100 × gen/preinh).
- BranchFastSpan: setup 2 EXP (span 25/100, TimeNeuronTimeLearnerBranch + D002C25e11).
- C++: `MatchMode` в `NPatternResponseAnalyzer`; `PatternRecognition()` в classic/Branch learner.

- Separability (FastSpan baseline, offline): `separability_fastspan_baseline.csv` — ISI template **8/8**, LTZ ROC **6/8** на всех 8 EXP → readout bottleneck подтверждён.

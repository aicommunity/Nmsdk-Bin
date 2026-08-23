# LTZ AutoCalibrate — алгоритм (SelectivityLtzCalibrate)

Краткая спецификация для regression (full480) и Tier 0 (FastSpan).

## Режимы калибровки (`CalibrateLTZThresholdMode`)

| Mode | Формула | Использование |
|------|---------|---------------|
| 0 gap_fraction | `min + f·(max−min)` | Regression golden (EXP00/EXP04): f=0.85, min=0.0115, max=0.05 |
| 1 peak_fraction | `max·f` | Tier 0 FastSpanLtzCal: f=0.99, min=0.001, max=0.10 (preinh) |

## Протокол train

1. Cold start: `ResetToUntrainedState=1`, `DendriteLength=1 1 1 1`, `UseFixedLTZThreshold=0`, `LTZThreshold=100`.
2. Обучение до `IsNeedToTrain=0` (Done): `TrainingPhase=2`, `AllDendritesSynced ∧ AllSynapsesNormalized`.
3. При Done: `CalibrateFixedLTZThresholdFromTraining()` → `FixedLTZThreshold`, `CalibratedFixedLTZThreshold` (runtime state).
4. Save (`-S`): веса и `FixedLTZThreshold` персистятся в `Parameters_00.xml` (**authoritative**).

## Sync Train → Test

1. `merge_train_weights.py` — Parameters train → Parameters test.
2. `merge_train_model.py` — weight-теги learner в **существующий** test Model (не заменять Model целиком).
3. `inject_analyzer.py` — in-place добавить `PatternResponseAnalyzer` + links.
4. `patch_ltz_calibrate_test.py` — `UseFixedLTZThreshold=1`, скопировать `FixedLTZ` из train.

**Важно:** `Train/Model_00.xml` может иметь stale `DendriteLength` (L=97 vs Parameters L=49). Источник истины — **Parameters**.

## Tier 0b (условно)

Если после peak_fraction grid остаётся `fire_all`: порт `CalibrateFixedLTZFromParallelPeak` из `NNeuronTimeLearnerBranch` в classic learner (parallel peak snapshot vs min/max gap).

## Backlog

- B3: двухпороговая LTZ (target vs distractor ROC)
- C2–C4: contrastive training, per-dendrite wiring, order-sensitive soma readout
- Tier D: Exc/Inh split, adaptive PeakMargin, TS10k sweep

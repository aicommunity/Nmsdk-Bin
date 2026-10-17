# LTZ AutoCalibrate — алгоритм (SelectivityLtzCalibrate)

Краткая спецификация для warm gate, Tier 0 (FastSpan) и optional cold Bio.

## Gate (перед grid / C++)

1. `smoke_sync_regression.sh` — golden EXP00/EXP04 после sync → 5/8 + 6/8.
2. `run_regression_warm.sh` — `verify_regression.py --mode warm` → `REGRESSION.md` с двумя **PASS**.
3. Cold Bio `run_regression.sh` — **optional**; не блокирует Tier 0 (`REGRESSION_COLD.md`).

## Режимы калибровки (`CalibrateLTZThresholdMode`)

| Mode | Формула | Использование |
|------|---------|---------------|
| 0 gap_fraction | `min + f·(max−min)` | Golden / optional cold Bio: f=0.85, min=0.0115, max=0.05 |
| 1 peak_fraction | `max·f` | Tier 0 FastSpanLtzCal: f=0.99, min=0.001, max=0.10 (preinh) |

## Протокол train (FastSpan / Branch)

1. Cold start: `ResetToUntrainedState=1`, `DendriteLength=1 1 1 1`, `UseFixedLTZThreshold=0`, `LTZThreshold=100`, fresh template Model.
2. Обучение до `IsNeedToTrain=0` (Done): `TrainingPhase=2`.
3. При Done: `CalibrateFixedLTZThresholdFromTraining()` → `FixedLTZThreshold`, `CalibratedFixedLTZThreshold`.
4. Save (`-S`): веса и `FixedLTZThreshold` в `Parameters_00.xml` (**authoritative**).
5. **Train gate:** `verify_train_done.py` перед sync — abort если FixedLTZ ещё 0.0115 / not Done.

## Sync Train → Test

1. `merge_train_weights.py` — Parameters train → Parameters test.
2. `merge_train_model.py` — weight-теги learner в **существующий** test Model (не заменять Model целиком).
3. `inject_analyzer.py` — in-place добавить `PatternResponseAnalyzer` + links.
4. `patch_ltz_calibrate_test.py` — `UseFixedLTZThreshold=1`, скопировать `FixedLTZ` из train.

**Важно:** `Train/Model_00.xml` может иметь stale `DendriteLength`. Источник истины — **Parameters**.

## Tier 0b (условно)

Если train Done, но grid остаётся `fire_all`: offline LTZ sweep → Branch CalibrateLtz → при необходимости порт `CalibrateFixedLTZFromParallelPeak` в classic.

## Backlog

- B1: offline dual-thr / FP diagnostics vs distractors (`MatchMode=1` = ISI oracle — не neuron gate)
- B3: двухпороговая LTZ (target vs distractor ROC)
- C2–C4: contrastive training, per-dendrite wiring, peak-timing FP-reject на soma
- Tier D: Exc/Inh split, adaptive PeakMargin, TS10k sweep

## Цель этапа (канон)

Pattern vs silence: trial0 (trained) → fire; trials 1–7 (distractors) → silence. Gate: `target_hit ∧ Acc≥4 ∧ ¬fire_all`. Operational MatchMode=0.

# SelectivityPresynapticInhib — Auto LTZ Threshold Report

Date: 2026-08-14  
См. также: [REPORT.md](REPORT.md) (fixed thr, PSI prototypes), [SelectivityPhaseA/REPORT.md](../SelectivityPhaseA/REPORT.md).

## 1. Механизм

После `EndOfLearning()` (до `SetIsNeedToTrain(false)`) опционально вызывается `CalibrateFixedLTZThresholdFromTraining()` в [`NNeuronTimeLearner`](../../../../Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp).

**Трекинг:** на каждой training-итерации (при `TrainingLTZThreshold=100`) записываются min/max `LTZone.Potential`. На последней итерации с `AllDendritesSynced()` — snapshot в `LastSyncedMinLTZ` / `LastSyncedMaxLTZ`.

**Режимы** (`CalibrateLTZThresholdMode`):

| mode | формула |
|------|---------|
| 0 gap_fraction (default) | `thr = min + f·(max − min)` |
| 1 peak_fraction | `thr = max · f` |

Clamp: `[CalibrateLTZThresholdMin, CalibrateLTZThresholdMax]`, default `f=0.85`, min=0.0115, max=0.05.  
Результат пишется в `FixedLTZThreshold` + `UseFixedLTZThreshold=1`; trace — `CalibratedFixedLTZThreshold`.

Параметры opt-in: `AutoCalibrateFixedLTZThreshold=false` по умолчанию (поведение без изменений).

## 2. Config map

| EXP | Neuron | Autothr | Train Done | L | Calibrated FixedLTZ | Test accuracy |
|-----|--------|:-------:|:----------:|---|--------------------:|:-------------:|
| EXP00_baseline | NSPNeuronGen | off | да | 49 41 25 1 | 0.0115 | **4/8** |
| EXP00_baseline_autothr | NSPNeuronGen | on | да | 49 41 25 1 | **0.01254** | **4/8** |
| EXP01_preinh_050 | Preinh0_5 | off | нет* | 1 1 1 1 | 0.0115 | 1/8 |
| EXP01_preinh_050_autothr | Preinh0_5 | on | нет* | 1 1 1 1 | 0.0115† | 1/8 |
| EXP02_preinh_100 (GUI train) | Preinh | off | да | 49 44 25 1 | 0.0115 | **1/8** |
| EXP02_preinh_100_autothr | Preinh | on | нет* | 1 1 1 1 | 0.0115† | 1/8 |
| EXP03_preinh_200 | Preinh2_0 | off | нет* | 1 1 1 1 | 0.0115 | 1/8 |
| EXP03_preinh_200_autothr | Preinh2_0 | on | нет* | 1 1 1 1 | 0.0115† | 1/8 |

\* Console cold-train PSI: `peakValid=0`, L не растёт (см. [REPORT.md](REPORT.md)). GUI-train EXP02 — успешный эталон.  
† Калибровка пропущена / clamp min: нет валидного LTZ snapshot (`LastSyncedMaxLTZ≈0`).

## 3. EXP00 — baseline autothr

Калибровка (iter=27, synced):

```
min=3.8e-05  max=0.014744  f=0.85  →  FixedLTZ=0.012538
```

CSV: [`EXP00_baseline_autothr/Test/SelectivityLog/results.csv`](EXP00_baseline_autothr/Test/SelectivityLog/results.csv)

| trial | class | ISI | ltz_max | fired | t_rel | match |
|------:|------:|-----|--------:|:-----:|------:|:-----:|
| 0 | 1 | 0.08/0.16/0.24 | 0.011815 | 1 | 0.482 | 1 |
| 1 | 0 | 0.24/0.16/0.08 | 0.010778 | 0 | -1 | 1 |
| 2 | 0 | 0.16/0.08/0.24 | 0.011808 | 1 | 0.485 | 0 |
| 3 | 0 | 0.16/0.16/0.16 | 0.010756 | 0 | -1 | 1 |
| 4 | 0 | 0.02/0.22/0.24 | 0.011765 | 1 | 0.483 | 0 |
| 5 | 0 | 0.24/0.22/0.02 | 0.011712 | 1 | 0.484 | 0 |
| 6 | 0 | 0.04/0.04/0.40 | 0.011732 | 1 | 0.482 | 0 |
| 7 | 0 | 0.40/0.04/0.04 | 0.011231 | 0 | -1 | 1 |

**Accuracy 4/8** — как fixed thr=0.0115. Поднятие порога до 0.01254 не отсекло FP (trials 2,4,5,6): их `ltz_max` на trained trial всё ещё ≥0.0118.

## 4. EXP02 case study (GUI-обученный PSI)

Train: L=`[49,44,25,1]`, `InitialSomaPotential≈0.0366`, `peakRel≈0.516 s`, `FixedLTZThreshold=0.0115` (без autothr).

Test fixed thr=0.0115 (sync после GUI-train, последний прогон):

| trial | class | ltz_max | fired | t_rel | match |
|------:|------:|--------:|:-----:|------:|:-----:|
| 0 | 1 | 0.01499 | 1 | 0.246 | 1 |
| 1 | 0 | 0.01523 | 1 | 0.247 | 0 |
| 2 | 0 | 0.01538 | 1 | 0.247 | 0 |
| 3 | 0 | 0.01483 | 1 | 0.330 | 0 |
| 4 | 0 | 0.01576 | 1 | 0.226 | 0 |
| 5 | 0 | 0.01560 | 1 | 0.247 | 0 |
| 6 | 0 | 0.01489 | 1 | 0.231 | 0 |
| 7 | 0 | 0.01532 | 1 | 0.407 | 0 |

**1/8** — fire на всех 8, но `t_rel` уже не ~5 ms (сырой L=1), а **0.03–0.40 s** (раньше пика ~0.48 s). Порог 0.0115 ниже типичного `ltz_max` (~0.012–0.013) → ранние срабатывания.

Manual sweep на тех же весах: thr ∈ {0.0125, 0.0130, 0.0135, 0.0140} → **1/8** (все non-target всё ещё fire).

**Вывод по EXP02:** одной autothr по train-LTZ недостаточно для PSI: baseline LTZ при PSI уже близок к peak; нужен успешный train +, возможно, более высокий fraction или peak_fraction mode. Autothr на cold PSI batch не активируется (train не Done).

## 5. Сравнение с Phase A

| Метод | EXP00 accuracy | Примечание |
|-------|:--------------:|------------|
| Phase A fixed 0.0115 | 4/8 | baseline |
| Phase A manual thr=0.0135 | **6/8** | test-only sweep |
| Preinh EXP00 autothr (train) | 4/8 | thr=0.01254 auto |
| Preinh EXP02 GUI fixed | 1/8 | PSI, thr=0.0115 |

Autothr gap_fraction воспроизводит идею Phase A (поднять thr по observed LTZ), но **train-only** snapshot на baseline даёт thr=0.01254 < 0.0135 Phase A → тот же 4/8.

## 6. Заключение

- Реализована опциональная пост-обучающая калибровка `FixedLTZThreshold` (gap_fraction / peak_fraction).
- **Baseline:** autothr работает (thr 0.0115→0.01254), accuracy **не улучшилась** (4/8).
- **PSI (console cold):** train по-прежнему не сходится → autothr не применяется.
- **PSI (GUI EXP02):** train OK, но fixed thr даёт mass FP; manual thr до 0.014 не помог — проблема шире порога (timing/selectivity при PSI+высоком baseline).
- Рекомендация: для PSI повторить GUI-train с `AutoCalibrateFixedLTZThreshold=1` на успешных весах; рассмотреть `peak_fraction` или больший `CalibrateLTZThresholdFraction`; отдельно — стабилизация cold PSI train.

## Команды

```bash
./scripts/setup_autothr_experiments.sh
./scripts/run_autothr_experiments.sh
```

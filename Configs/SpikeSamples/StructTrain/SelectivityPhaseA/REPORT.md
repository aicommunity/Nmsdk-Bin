# Selectivity Phase A — Config Experiments Report

Date: 2026-08-13  
Baseline reference: [`TimeNeuronTimeLearner/Test`](../TimeNeuronTimeLearner/Test/) (4/8)

Инфраструктура:
- `NeuroModelerConsole -S` / `--save-project` — Save после расчёта ([`App/NeuroModelerConsole/main.cpp`](../../../../../App/NeuroModelerConsole/main.cpp))
- `NPatternResponseAnalyzer` CSV: `ltz_potential_max`, `soma_amp_0..3`, `soma_amp_sum`
- Шаблоны `TimeNeuronTimeLearner/{Train,Test}` (канон layout)

## 1. Config map

| EXP | Train | Test | Changed params | Retrain? | Accuracy |
|-----|-------|------|----------------|:--------:|:--------:|
| EXP00 | [`EXP00_baseline/Train`](EXP00_baseline/Train/) | [`EXP00_baseline/Test`](EXP00_baseline/Test/) | контроль | нет | **4/8** |
| EXP01 | веса EXP00 | [`EXP01_ltz_threshold_sweep/Test_thr*`](EXP01_ltz_threshold_sweep/) | `FixedLTZThreshold` | нет | **6/8** (thr=0.0135) |
| EXP02 | веса EXP00 | [`Test_avg0`](EXP02_ltzone_average_mode/Test_avg0/), [`Test_avg1`](EXP02_ltzone_average_mode/Test_avg1/) | `UseAverageLTZonePotential` | нет | 4/8 / 4/8 |
| EXP03 | [`EXP03.../Train`](EXP03_sync_tolerance_015/Train/) | [`Test`](EXP03_sync_tolerance_015/Test/) | `SyncTolerance=0.015` | да + `-S` | **3/8** |
| EXP04 | [`EXP04.../Train`](EXP04_sync_tolerance_010/Train/) | [`Test`](EXP04_sync_tolerance_010/Test/) | `SyncTolerance=0.010` | да + `-S` | **4/8** |
| EXP05 | [`EXP05.../Train`](EXP05_resistance_gain_025/Train/) | [`Test`](EXP05_resistance_gain_025/Test/) | `ResistanceAdjustGain=0.25` | да + `-S` | **4/8** |
| EXP06 | веса EXP00 | [`Test_tc*`](EXP06_ltzone_integration/), [`Test_npltzone_*`](EXP06_ltzone_integration/) | тип компонента LTZone (`NPLTZone`) / τ / порог | нет | **6/8** (= EXP01 thr) |

## 2. Baseline metrics (EXP00)

CSV: [`EXP00_baseline/Test/SelectivityLog/results.csv`](EXP00_baseline/Test/SelectivityLog/results.csv)  
`FixedLTZThreshold=0.0115`, `UseAverageLTZonePotential=1`, L=`[49,41,25,1]`

| trial | class | ISI | ltz_max | soma0 | soma1 | soma2 | soma3 | fired | match |
|------:|------:|-----|--------:|------:|------:|------:|------:|:-----:|:-----:|
| 0 | 1 | 0.08/0.16/0.24 | 0.011815 | 0.01446 | 0.01566 | 0.02209 | 0.01583 | 1 | 1 |
| 1 | 0 | 0.24/0.16/0.08 | 0.010778 | 0.01605 | 0.01599 | 0.02232 | 0.01583 | 0 | 1 |
| 2 | 0 | 0.16/0.08/0.24 | 0.011808 | 0.01605 | 0.01599 | 0.02232 | 0.01583 | 1 | 0 |
| 3 | 0 | 0.16/0.16/0.16 | 0.010756 | 0.01067 | 0.01058 | 0.01578 | 0.01578 | 0 | 1 |
| 4 | 0 | 0.02/0.22/0.24 | 0.011765 | 0.01798 | 0.01863 | 0.02925 | 0.02294 | 1 | 0 |
| 5 | 0 | 0.24/0.22/0.02 | 0.011712 | 0.01810 | 0.01870 | 0.02927 | 0.01821 | 1 | 0 |
| 6 | 0 | 0.04/0.04/0.40 | 0.011732 | 0.02312 | 0.02537 | 0.03730 | 0.01738 | 1 | 0 |
| 7 | 0 | 0.40/0.04/0.04 | 0.011231 | 0.02496 | 0.02537 | 0.03730 | 0.01738 | 0 | 1 |

Accuracy **4/8**. FP: permute mid, close-start, close-end, early cluster.

## 3. LTZ separability analysis

По EXP00 snapshot:

```
min(ltz_max | trained) = 0.0118145
max(ltz_max | FP)      = 0.0118082
gap                    = 0.0000063
```

**Separable by scalar LTZ at a fixed snapshot: NO** (gap ≪ 0.0005).

Важно: `ltz_potential_max` **зависит от порога**. Спайк сбрасывает/ограничивает потенциал, поэтому offline-sweep по EXP00 CSV **завышает** отказ trained (предсказывал FN на trial 0 при thr≥0.012). Confirm-прогоны это опровергли: при росте thr пик trained тоже растёт.

## 4. EXP01 — FixedLTZ sweep

Offline (по EXP00 CSV, невалиден как предиктор FN):

| thr | offline acc | FP | FN |
|-----|:-----------:|----|----|
| 0.0115 | 4/8 | 2,4,5,6 | — |
| ≥0.012 | 7/8 | — | 0 |

Confirm (реальный прогон):

| thr | accuracy | fired trained | оставшиеся FP |
|-----|:--------:|:-------------:|---------------|
| 0.0115 | 4/8 | да | 2,4,5,6 |
| 0.0120 | 4/8 | да | 2,4,5,6 |
| 0.0125 | 4/8 | да | 2,4,5,6 |
| 0.0130 | **5/8** | да | 2,4,6 (trial 5 тишина) |
| 0.0135 | **6/8** | да | **4, 6** (permute mid и close-end тишина) |

Лучший config-only результат фазы A: **`FixedLTZThreshold=0.0135` → 6/8**.  
Оставшиеся FP: близкая пара в начале (trial 4) и ранний кластер (trial 6) — их `ltz_max` при этом пороге **выше** trained (0.01363 / 0.01372 vs 0.01379).

## 5. EXP02 — UseAverageLTZonePotential

| режим | accuracy | примечание |
|-------|:--------:|------------|
| avg=1 (baseline) | 4/8 | как EXP00 |
| avg=0 (sum) | 4/8 | те же 4 FP при thr=0.0115 |

Sum без подъёма порога не улучшает избирательность: все 4 soma масштабируются одинаково, бинарное решение не меняется.

## 6. EXP03–04 — SyncTolerance (retrain + `-S`)

После Save Train Model скопирован в Test (`inject_analyzer.py`), иначе StructureBuildMode=0 оставлял baseline L=49/41/25/1.

| EXP | SyncTolerance | L after Save | IsNeedToTrain after `-S` | accuracy |
|-----|---------------|--------------|--------------------------|:--------:|
| EXP03 | 0.015 | **49 / 41 / 27 / 1** | 1 (Done за 160 с не зафиксирован) | **3/8** |
| EXP04 | 0.010 | **50 / 41 / 25 / 1** | 1 | **4/8** |

EXP03: late cluster (trial 7) стал FP (`ltz_max≈0.01150`, `t_rel=0.858`) — ужесточение tol сдвинуло L2 25→27 и размыло отвержение позднего кластера.

EXP04: soma0 amp упала (~0.007 vs 0.014) — `missing tip Dendrite1_50` в логе обучения; структура L=50 не полностью согласована. Accuracy осталась 4/8, запас trained над порогом меньше (0.01170).

## 7. EXP05 — ResistanceAdjustGain=0.25

После `-S`: L=`[49,41,25,1]`, R как у baseline. Accuracy **4/8**, CSV совпадает с EXP00.  
Cold retrain за 160 с не ушёл от уже settled длин (старт с копии обученного конфига + ResetToUntrained мог не сериализоваться). Gain в Test Parameters остался 0.4 (merge копирует только веса, не gain) — на inference это не влияет.

## 8. EXP06 — тип компонента LTZone и временная интеграция

Здесь «класс» = **имя C++-компонента** LTZone в Model, не метка сэмпла `target_class`.  
Имя `NPulseLTZone` **не зарегистрировано** в PulseLibrary. Зарегистрированный интегратор: **`NPLTZone`** ([`NPulseLibrary.cpp`](../../../../../Libraries/Nmsdk-PulseLib/Core/NPulseLibrary.cpp) `UploadClass("NPLTZone", ...)`). Интеграция = сглаживание с `TimeConstant` перед порогом.

Сетка `Test_tc*_thr*` с `Class=NPulseLTZone` падала с `name not found: NPulseLTZone` и фактически работала как `NPulseLTZoneThreshold` + изменённый Threshold:

| TimeConstant (имя папки) | Threshold | accuracy |
|--------------------------|-----------|:--------:|
| * (все tc) | 0.0115 | 4/8 |
| * | 0.012 | 4/8 |
| * | 0.013 | 5/8 |

Реальный интегратор `NPLTZone`, `TimeConstant=0.00144`:

| конфиг | accuracy |
|--------|:--------:|
| [`Test_npltzone_tc000144_thr00115`](EXP06_ltzone_integration/Test_npltzone_tc000144_thr00115/) | 4/8 |
| [`Test_npltzone_tc000144_thr00135`](EXP06_ltzone_integration/Test_npltzone_tc000144_thr00135/) | **6/8** |

Числа **идентичны** EXP01 с тем же порогом: интеграция с τ=0.00144 не даёт дополнительного контраста относительно мгновенного порога.

Первый (сломанный) EXP06 прогон на битом Model (Parameters записан поверх Model) завис на ~2 ч — процесс убит.

## 9. Best result

- **Best EXP:** EXP01 `Test_thr00135` (и эквивалент EXP06 NPLTZone thr=0.0135)
- **Best accuracy:** **6/8**
- **Recommended snapshot:** [`EXP01_ltz_threshold_sweep/Test_thr00135/Parameters_00.xml`](EXP01_ltz_threshold_sweep/Test_thr00135/Parameters_00.xml)  
  `FixedLTZThreshold=0.0135`, веса нейрона = EXP00 Train (`L=49/41/25/1`)
- Оставшиеся FP: trial 4 (close pair start), trial 6 (early cluster)

## 10. Conclusion and next steps

- Scalar LTZ **не разделяет** trained и все FP в одном snapshot (gap ≈ 6e-6).
- Подъём `FixedLTZThreshold` до **0.0135** — единственный рычаг фазы A, давший **+2/8** (permute mid и close-end отсекаются). Close-start и early-cluster остаются выше trained peak.
- `UseAverageLTZonePotential=0`, ужесточение `SyncTolerance`, `ResistanceAdjustGain=0.25`, `NPLTZone` integration **не** улучшают метрику сверх EXP01.
- Retrain с более жёстким sync **ухудшил** EXP03 (3/8).
- **Рекомендация:** фаза C (отложена) — inference gating / contrastive, иначе потолок config-only ≈ 6/8.

### Saved artifact configs (обученные нейроны)

| путь | содержимое |
|------|------------|
| [`EXP00_baseline/Train`](EXP00_baseline/Train/) | копия baseline-обученного нейрона (`IsNeedToTrain=0`, L=49/41/25/1) |
| [`EXP03_sync_tolerance_015/Train`](EXP03_sync_tolerance_015/Train/) | `-S` после cold-ish train, L=49/41/27/1 |
| [`EXP04_sync_tolerance_010/Train`](EXP04_sync_tolerance_010/Train/) | `-S`, L=50/41/25/1 (tip Dendrite1_50 warning) |
| [`EXP05_resistance_gain_025/Train`](EXP05_resistance_gain_025/Train/) | `-S`, L=49/41/25/1, gain=0.25 |

### Замечания по пайплайну

- `sync` должен копировать **Model** из Train (`inject_analyzer.py`), иначе Test при `StructureBuildMode=0` игнорирует новые длины.
- Save пишет `TipSynapseResistance` с запятой (locale); `merge_train_weights.py` нормализует в точки.
- После `-t 160 -S` у EXP03–05 `IsNeedToTrain` остался 1 — Done за 160 с не зафиксирован (длины всё же изменились).

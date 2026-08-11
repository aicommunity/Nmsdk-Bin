# NNeuronTimeLearner — алгоритм обучения

Обучение временного паттерна: один burst `NDatasetMatrix` (fan-out `Generator1`) на все дендриты; **one-dendrite-per-burst** Sync против снимка `PrevPeakRel` прошлой пачки; затем нормализация амплитуд синапсами.

Реализация: [`Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp`](../../../../../Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp).

## Wiring

```
DatasetMatrix.Generator1.Output
        │ fan-out
        ├─► Dendrite1_{L1}.ExcSynapse1
        ├─► Dendrite2_{L2}.ExcSynapse1
        ├─► …
        └─► DendriteN_{LN}.ExcSynapse1   (якорь длины, обычно L=1)
```

- `InputPattern` / `MatrixData`: ISI-слоты `N×1` (кумулятивны: `t += isi` в Dataset и в `ExpectedPulseRelTimes`).
- Пример: `0.01, 0.08, 0.16, 0.24` → абсолютные времена `[0.01, 0.09, 0.25, 0.49]`.
- `SyncInputPatternToDataset()` до/после `Dataset->Build/Reset`.
- После роста длины: tip-only link; proximal `Input` отсоединяется.

## Фазы

| Phase | Имя | Действие |
|-------|-----|----------|
| 0 | Sync | Подбор `DendriteLength[k]` по одному дендриту за пачку vs `PrevPeakRel[N-1]` |
| 1 | Normalize | Подбор `NumSynapse[i]` по амплитуде vs `InitialSomaPotential[i]` |
| 2 | Done | Фиксация `TrainingPattern` / индексов на нейроне, порог LTZ |

## Итерация (Sync)

1. Ждём новый импульс и `EffectiveIterationGap = max(IterationGap, span+settle+slack)` от старта предыдущей пачки.
2. `BeginTrainingIteration` — `ExpectedPulseRelTimes = cumsum(ISI)`.
3. Каждый такт: `MeasureMaxPotentialAndTime` (окно до `span + SettleMargin`, settle растёт с `max(DendriteLength)`).
4. `FinishTrainingIteration`:
   - `SomaPeakValid[i]`, `PeakRel[i] = Tpeak[i]-T0`, `DelayFromPulse[i] = Tpeak[i]-(T0+Expected[i])`
   - **Первая пачка:** bootstrap — только `CommitPrevPeakSnapshot()`, без роста
   - Иначе: `ActiveDendrite = (CountIteration-1) % (N-1)`; только он получает `ChangeDendriteStatus`
   - `dt = PrevPeakRel[N-1] - PeakRel[k]` (не мгновенный пик ref этой пачки)
   - `RefreshDendLastAbsDtFromPrevAnchor` — все `i` vs Prev-якорь для `AllDendritesSynced`
   - `ApplyPendingDendriteLengthChanges` — обычно один индекс; шаг `ΔL ≈ |dt|/EstDelayPerSeg`
   - `CommitPrevPeakSnapshot()` для следующей пачки
5. `EndOfLearning` → Normalize, когда все `|DendLastAbsDt[i]| ≤ SyncTolerance` и пики valid.

Структура меняется в **конце** пачки (inter-burst gap).

## Критерий dt / эталон

```
ref = N - 1
k   = ActiveDendrite   // one-dendrite-per-burst

delay[k]   = TimeOfMax[k] - (FirstImpulseTime + Expected[k])
peakRel[k] = TimeOfMax[k] - FirstImpulseTime

dt = PrevPeakRel[ref] - PeakRel[k]   // якорь = снимок ПРОШЛОЙ пачки

если bootstrap (!HasPrevPeakSnapshot): только сохранить Prev*, DendStatus=0
иначе если !valid: эвристика роста если length[k] ≤ length[ref]
иначе amp-collapse / no-improve → `DendBestEffortSynced` (принят без |dt|≤tol)
иначе если |dt| ≤ SyncTolerance или sign-flip → DendStatus=0
иначе dt>0 → растить; dt<0 → укорачивать
```

`AllDendritesSynced`: для каждого `i < N−1` либо `|DendLastAbsDt[i]| ≤ SyncTolerance`, либо `DendBestEffortSynced[i]` (дальнейший рост бесполезен из‑за схлопывания амплитуды).

Эталонный дендрит `N-1` не растёт. Неактивные в этой пачке всегда `DendStatus=0`.
Шаг длины ограничен `kMaxLengthStep` (8) и `ΔL ≈ |dt|/EstDelayPerSeg`.

## Параметры sample

| Параметр | Значение |
|----------|----------|
| `NumInputDendrite` | 4 |
| `InputPattern` | `0.01, 0.08, 0.16, 0.24` (span ≈ 0.49 s) |
| `IterationGap` / `Delay` | 1.5 s (≥ span + settle) |
| `SyncTolerance` | 0.02 s |
| `NeuronClassName` | `NSPNeuronGen` |

Физический потолок выравнивания: `Δt_max ≈ MaxDendriteLength × ~0.01 s`.

Прогон: `NeuroModelerConsole -c …/Project.ini -s -t 60 -x`.

## Отличия от прежней batch-схемы

| | Было | Сейчас |
|--|------|--------|
| Кого меняем | все `DendStatus≠0` за пачку | один `ActiveDendrite` |
| Эталон | `TimeOfMax[N-1]` этой пачки | `PrevPeakRel[N-1]` прошлой пачки |
| Done | все `DendStatus==0` | все `DendLastAbsDt[i] ≤ SyncTolerance` |

## Known limitations

- Normalize может не дойти до Done за ограниченное модельное время (амплитуда на длинных дендритах ниже `InitialSomaPotential`).
- Warning `PrepareDataset rejected data on Dataset` относится к файловому `NDataset`, не к `DatasetMatrix` sample.

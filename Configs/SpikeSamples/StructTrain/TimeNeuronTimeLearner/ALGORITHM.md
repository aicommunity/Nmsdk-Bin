# NNeuronTimeLearner — алгоритм обучения

Обучение временного паттерна: один burst `NDatasetMatrix` (fan-out `Generator1`) на все дендриты; дендрит *k* подстраивается по импульсу *k*; последний дендрит — эталон синхронизации; затем нормализация амплитуд синапсами.

Реализация: [`Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp`](../../../../../Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp).

## Wiring

```
DatasetMatrix.Generator1.Output
        │ fan-out
        ├─► Dendrite1_{L1}.ExcSynapse1
        ├─► Dendrite2_{L2}.ExcSynapse1
        ├─► …
        └─► DendriteN_{LN}.ExcSynapse1   (эталон, обычно L=1)
```

- `InputPattern` / `MatrixData`: ISI-слоты `N×1` (например `0.01, 0.03, 0.06, 0.07`).
- Синхронизация паттерна: `SyncInputPatternToDataset()` до/после `Dataset->Build/Reset`.
- После роста длины: tip-only link; proximal `Input` отсоединяется.

## Фазы

| Phase | Имя | Действие |
|-------|-----|----------|
| 0 | Sync | Подбор `DendriteLength[0..N-2]` по рассинхронизации пиков на сомах |
| 1 | Normalize | Подбор `NumSynapse[i]` по амплитуде vs `InitialSomaPotential[i]` |
| 2 | Done | Фиксация `TrainingPattern` / индексов на нейроне, порог LTZ |

## Итерация (Sync)

1. Ждём новый импульс и `IterationGap` от старта предыдущей пачки.
2. `BeginTrainingIteration` — окна измерения от `ExpectedPulseRelTimes`.
3. Каждый такт: `MeasureMaxPotentialAndTime` (первый локальный max после импульса *i*).
4. `FinishTrainingIteration`:
   - `SomaPeakValid[i] = (amp > kMinMeasurableSomaAmp) && PeakSeen`
   - `ChangeDendriteStatus` для всех *i*
   - `ApplyPendingDendriteLengthChanges` — **batch** всех `DendStatus ≠ 0` (не worst-first)
5. `EndOfLearning` → Normalize, когда все `DendStatus[0..N-2]==0`, valid peaks и `|dsyn| ≤ SyncTolerance`.

Структура меняется в **конце** итерации (между пачками), не в `BeginTrainingIteration`.

## Критерий dt / эталон

```
ref = N - 1
dt  = TimeOfMax[ref] - TimeOfMax[num]

если !SomaPeakValid[num] или !SomaPeakValid[ref]:
  не считать synced; эвристика роста если length[num] ≤ length[ref]
иначе если |dt| ≤ SyncTolerance или dt==0 → DendStatus=0
иначе если sign-flip PrevDissynchronization×dt < 0 и |dt|↓ → DendStatus=0
иначе dt>0 → расти (+1); dt<0 → укорачивать (−1)
```

Эталонный дендрит всегда `DendStatus[N-1]=0`.

## Рост длины (batch)

`ApplyPendingDendriteLengthChanges`:

1. Для всех `i < N-1` с `DendStatus≠0` обновить `DendriteLength` (с guard'ами min/max).
2. `Neuron->NumDendriteMembranePartsVec = DendriteLength` → `Neuron->Build()`.
3. Новые сегменты из `TakeObject` должны получить `Activity=true` и `Init()` (иначе `Calculate` no-op → amp=0).
4. Relink всех tip → `Generator1`; proximal disconnect.

Корневая причина прежнего `amp=0` после роста: новые мембраны без `InitFlag` / каналов до CreateLink кабеля — исправлено в `NPulseNeuron::BuildStructure`.

## Параметры sample

| Параметр | Значение |
|----------|----------|
| `NumInputDendrite` | 4 |
| `InputPattern` | `0.01, 0.03, 0.06, 0.07` |
| `IterationGap` / `Delay` | 0.5 s |
| `SyncTolerance` | 0.02 s |
| `NeuronClassName` | `NSPNeuronGen` |

Прогон: `NeuroModelerConsole -c …/Project.ini -s -t 30 -x`.

## Отличия от NNeuronLearner

| | NNeuronLearner | NNeuronTimeLearner |
|--|----------------|-------------------|
| Вход | `Source1..N` per dendrite | один `Generator1` fan-out |
| Смена длины | начало итерации | конец итерации (batch) |
| Stop Sync | sign-flip / dt==0 | SyncTolerance + sign-flip + `SomaPeakValid` |
| Relink | только свой Source | все tip → Generator1 |

## Known limitations

- Фаза Normalize за 30 s модельного времени может не дойти до `Done`: амплитуда на длинных дендритах ниже `InitialSomaPotential` (калибровка при `length=1`), `SynapseStatus` остаётся 1.
- Warning `PrepareDataset rejected data on Dataset` относится к файловому `NDataset` в дереве, не к `DatasetMatrix` sample.
- При `amp≈0` без `Init`/`Activity` на новом tip Sync раньше ложно сходился; теперь блокируется `SomaPeakValid`.

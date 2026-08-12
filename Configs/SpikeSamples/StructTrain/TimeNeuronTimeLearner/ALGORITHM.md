# NNeuronTimeLearner — алгоритм обучения

Обучение временного паттерна: один burst `NDatasetMatrix` (fan-out `Generator1`) на все дендриты; **joint train** — one-dendrite-per-burst подбор длины плюс нормализация амплитуд синапсами (как `NNeuronLearner`).

Реализация: [`Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp`](../../../../../Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp).

## Wiring

```
DatasetMatrix.Generator1.Output
        │ fan-out
        ├─► Dendrite1_{L1}.ExcSynapse*
        ├─► Dendrite2_{L2}.ExcSynapse*
        ├─► …
        └─► DendriteN_{LN}.ExcSynapse*   (якорь длины, обычно L=1)
```

- `InputPattern` / `MatrixData`: ISI-слоты `N×1`. Относительно **первого импульса** (`FirstImpulseTime`): `Expected = [0, ISI_1, ISI_1+ISI_2, …]` (пример `0.01,0.08,0.16,0.24` → `[0, 0.08, 0.24, 0.48]`).
- После роста: tip-only link; proximal `Input` отсоединяется.

## Фазы

| Phase | Имя | Действие |
|-------|-----|----------|
| 0 | Joint train | Длина активного дендрита + синапсы всех сом |
| 1 | (legacy) | Не выставляется |
| 2 | Done | `TrainingPattern` / индексы на нейроне |

`EndOfLearning` → Done при `AllDendritesSynced() ∧ AllSynapsesNormalized()` (без Sync→Normalize).

## Итерация

1. `EffectiveIterationGap = max(IterationGap, span+settle+slack)`.
2. `BeginTrainingIteration` — cumsum ISI.
3. `MeasureMaxPotentialAndTime`: для `i < N−1` окно ±margin вокруг `Expected[i]+(L_i−1)·EstDelayPerSeg`, не заходя в зону пика следующего импульса; эталон — `pattern_end+settle`.
4. `FinishTrainingIteration`:
   - bootstrap, пока нет **valid ref peak** (`HasPrevPeakSnapshot` только при `PrevPeakValid[ref]`) — **без роста**;
   - иначе `ChangeDendriteStatus(active)` → `RefreshDendLastAbsDtFromPrevAnchor` → `ChangeSynapseStatus` для всех;
   - apply: длина, затем синапсы на новом tip;
   - `CommitPrevPeakSnapshot` (Prev копируется всегда; флаг HasPrev — только если ref valid).

## Критерий длины

```
needed[k] = PrevPeakRel[ref] - Expected[k]
delay_len = (L-1)·EstDelayPerSeg
delay_use = DelayFromPulse  если согласован с delay_len / peak_model (±margin)
          иначе delay_len
dt = needed - delay_use
```

**Гейты:** нет `peakValid` у активного дендрита → `DendStatus=0` (не ΔL). Нет valid Prev ref → не ΔL. Invalid/dead tip: только accept/best-effort при `|needed−delay_len|≤tol` или amp-collapse@cap — **без** `DendStatus=±1`.

`ApplyPending`: `ΔL ≈ |dt|/EstDelayPerSeg`, cap `kMaxLengthStep`, **anti-overshoot**; при провале tip-link — один `Build`+Relink retry.

Ожидание sample: `L0 > L1 > L2 > L3=1` (~49 / ~41 / ~25 / 1).

## Нормализация синапсов

Цель: `MaxIterSomaAmp[i] → InitialSomaPotential[i]` (захват **только при L==1** на полном пике).

- Пока `Initial<=0` — синапсы не меняются (`SynapseStatus=0`).
- `kMaxSynapsesPerDend = 128` (экспериментальный потолок).
- `AllSynapsesNormalized`: amp в ε от Initial **или** best-effort@cap **или** dead tip (`amp < 1e-6`) при уже синхронизированной длине.
- `AllDendritesSynced`: dead tip + `|needed−delay_len|≤tol` / best-effort — без требования `peakValid`.
- На более длинных дендритах обычно больше синапсов; полный cap может потребовать `-t 120+`.

## Параметры sample

| Параметр | Значение |
|----------|----------|
| `NumInputDendrite` | 4 |
| `InputPattern` | `0.01, 0.08, 0.16, 0.24` |
| `IterationGap` / `Delay` | 1.5 s |
| `SyncTolerance` | 0.02 s |
| `NeuronClassName` | `NSPNeuronGen` |

Прогон обучения: `NeuroModelerConsole -c …/Project.ini -s -t 120 -x`.

Осциллограммы: компонент `UStatisticDoubleMatrix` → `StatisticLog/` (`SomaNeuronAmplitude`, `SomaSumPotential`, Generator1).

## Known limitations

- При сильной attenuation даже 128 tip-синапсов могут не дотянуть amp до Initial → best-effort Done.
- Fan-out на все дендриты даёт кросс-пики на других ISI; критерий H1 — отсутствие пары пиков sync с Δt≈0.08 (L0≈L1), а не отсутствие любых вторичных пиков.
- Warning `PrepareDataset rejected data on Dataset` — файловый `NDataset`, не `DatasetMatrix` sample.

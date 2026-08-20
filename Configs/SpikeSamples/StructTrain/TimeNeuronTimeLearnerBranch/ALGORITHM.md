# NNeuronTimeLearnerBranch — алгоритм обучения

Один дендрит: N импульсов паттерна подключаются на **разном расстоянии** от единственной сомы. `NumInputDendrite=N` — число импульсов, не дендритов. **На сому входные синапсы не ставятся** — только на сегменты `Dendrite1_*`.

Реализация: [`Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearnerBranch.cpp`](../../../../../Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearnerBranch.cpp).

## Физика

```
Generator1 (импульс N-1) → Dendrite1_1.ExcSynapse*   (якорь, не растёт)
Generator1 (импульс N-2) → Dendrite1_{L2}
…
Generator1 (импульс 0)   → Dendrite1_{L0}
Dendrite1_Lmax → … → Dendrite1_1 → Soma1
```

`DendriteLength[k]` = сегмент синапса импульса k (`≥1` = `Dendrite1_{seg}`). Cold при N=4: **`[1, 1, 1, 1]`** — все импульсы на первом сегменте дендрита.

Dataset: `NumFeatures=1`, `MaxSpikesPerFeature=N`. `InputPattern` — ISI N×1.

## Обратная синхронизация

Необученные импульсы `0..k-1` глушатся (mute).

1. Импульс N−1 на `Dendrite1_1`: запомнить `StoredPeakRel[N-1]` (якорь, длина не растёт).
2. Импульс k = N−2 … 0: `T* = mean(StoredPeakRel[j], j>k)`, `needed = T* − Expected[k]`.
3. Нормализация amp/R **только для активного k** в той же пачке, что и ΔL.
4. После length+amp: `PulseSynced[k]=true`, переход к k−1.

Done: все `PulseSynced[0..N-2]` и amp в ε (или best-effort).

После sync+amp обучение **не** сразу ставит recognition-порог. Два завершающих этапа:

1. **Параллельная нормализация R (1/N):** mute-обученные tip-R рассчитаны на один активный синапс. При recognition все N tip на одной цепи суммируют ток → `TipSynapseResistance[k] *= N` (`ScaleTipResistancesForParallelActivation`), затем все tip подключаются к `Generator1`.
2. **Калибровка FixedLTZ:** фаза `CalibrateLtz` — один прогон паттерна с `TrainingLTZ` (без раннего спайка). Итерация **ждёт полный cable settle** (не early `all_locked`), иначе пик занижается. Непрерывный max сомы/`LTZ` → `FixedLTZThreshold = peak × CalibrateLTZThresholdFraction` (по умолчанию **0.99**, mode=`peak_fraction`, clamp `[CalibrateLTZThresholdMin, CalibrateLTZThresholdMax]`, max по умолчанию **1.0**). Затем `phase → Done`, `IsNeedToTrain=0`.

Ожидаемые позиции: `L0 > L1 > L2 ≥ 1`, якорь `DendriteLength[N-1] ≥ 1` (обычно остаётся на 1).

## Линковка Generator1 → ExcSynapse1

- **Train (mute):** `RebuildGeneratorSynapseLinks` снимает все старые связи Generator→`Dendrite1_*.ExcSynapse1`, затем подключает **только** активный импульс → **ровно 1** link.
- **Done / recognition:** подключаются все N финальных tip-synapse → **ровно N** links на `{L0,…,L(N−1)}`.
- При росте кабеля (шаг до `kMaxLengthStep=8`) старый сегмент явно отцепляется (`DetachBranchExcSynapseAtSegment`), иначе на `Generator1.Output` накапливаются stale links (например `1,9,17,25,33,41`).
- Внешний tap `Generator1.Output → PatternResponseAnalyzer.StimulusInputs` при cleanup **не** удаляется.
- **Проверка:** после Done число подключённых tip-synapse == N; сегменты уникальны и `L[k] > L[k+1]` для k < N−2.

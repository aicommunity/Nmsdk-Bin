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

Ожидаемые позиции: `L0 > L1 > L2 ≥ 1`, якорь `DendriteLength[N-1] ≥ 1` (обычно остаётся на 1).

# NNeuronTimeLearnerBranch — алгоритм обучения

Один дендрит: N импульсов паттерна подключаются на **разном расстоянии** от единственной сомы. `NumInputDendrite=N` — число импульсов, не дендритов.

Реализация: [`Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearnerBranch.cpp`](../../../../../Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearnerBranch.cpp).

## Физика

```
GeneratorN (импульс N-1) → Soma1.ExcSynapse     (якорь, pos=0, не растёт)
Generator3 (импульс N-2) → Dendrite1_{L2}
…
Generator1 (импульс 0)   → Dendrite1_{L0}
Dendrite1_Lmax → … → Dendrite1_1 → Soma1
```

`DendriteLength[k]` = позиция синапса импульса k (`0` = сома, `≥1` = сегмент цепи). Cold при N=4: **`[1, 1, 1, 0]`** — 1 сома + 1 сегмент дендрита, не четыре дендрита.

Dataset: `NumFeatures=N`, `MaxSpikesPerFeature=1`. `InputPattern` снаружи — ISI N×1; внутри — абсолютные времена 1×N.

## Обратная синхронизация

Необученные импульсы `0..k-1` глушатся (mute).

1. Импульс N−1 на Soma1: запомнить `StoredPeakRel[N-1]` (вырожденный случай).
2. Импульс k = N−2 … 0: `T* = mean(StoredPeakRel[j], j>k)`, `needed = T* − Expected[k]`.
   Не использовать mean(PeakRel−Expected) как целевую кабельную задержку — это ломает coincidence.
3. Нормализация amp/R **только для активного k** в той же пачке, что и ΔL.
4. После length+amp: `PulseSynced[k]=true`, переход к k−1.

Done: все `PulseSynced[0..N-2]` и amp в ε (или best-effort).

Ожидаемые позиции: `L0 > L1 > L2 ≥ 1`, якорь `DendriteLength[N-1]=0`. Числа не обязаны совпасть с TimeLearner `[49,41,25,1]` (другая топология).

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

1. **Параллельная нормализация R (1/N + amp-eq):** mute-обученные tip-R рассчитаны на один активный синапс; якорь `N−1` **не** amp-tune в mute (`ChangeSynapseResistanceStatus` early-return), поэтому его `InitialSomaPotential` обычно ~10× выше distal. Перед recognition: `I_ref = mean(Initial[0..N−2])`, затем `TipSynapseResistance[k] *= N × (Initial[k] / I_ref)` (`ScaleTipResistancesForParallelActivation`; при `Initial≤0` — только `×N`). Solo-вклады выравниваются, каждый tip даёт ~1/N суммарной проводимости. Затем все tip подключаются к `Generator1`.
2. **Калибровка FixedLTZ:** фаза `CalibrateLtz` — один прогон паттерна с `TrainingLTZ` (без раннего спайка). Итерация **ждёт полный cable settle** (не early `all_locked`), иначе пик занижается. Непрерывный max сомы/`LTZ` → `FixedLTZThreshold = peak × CalibrateLTZThresholdFraction` (по умолчанию **0.99**, mode=`peak_fraction`, clamp `[CalibrateLTZThresholdMin, CalibrateLTZThresholdMax]`, max по умолчанию **1.0**). Затем `phase → Done`, `IsNeedToTrain=0`.

Ожидаемые позиции: `L0 > L1 > L2 ≥ 1`, якорь `DendriteLength[N-1] ≥ 1` (обычно остаётся на 1).

## Линковка Generator1 → ExcSynapse1

- **Train (mute):** `RebuildGeneratorSynapseLinks` снимает все старые связи Generator→`Dendrite1_*.ExcSynapse1`, затем подключает **только** активный импульс → **ровно 1** link.
- **Done / recognition:** подключаются все N финальных tip-synapse → **ровно N** links на `{L0,…,L(N−1)}`.
- При росте кабеля (шаг до `kMaxLengthStep=8`) старый сегмент явно отцепляется (`DetachBranchExcSynapseAtSegment`), иначе на `Generator1.Output` накапливаются stale links (например `1,9,17,25,33,41`).
- Внешний tap `Generator1.Output → PatternResponseAnalyzer.StimulusInputs` при cleanup **не** удаляется.
- **Проверка:** после Done число подключённых tip-synapse == N; сегменты уникальны и `L[k] > L[k+1]` для k < N−2.

## EnableNextSegmentInhibition (default false)

Когда `true`, тот же `Generator1` для каждого tip k дополнительно идёт на тормозной синапс следующего сегмента:

```
Exc @ Dendrite1_{L[k]}.ExcSynapse1
Inh @ Dendrite1_{L[k]+1}.InhSynapse1   (Type=1, Resistance=SynapseResistanceBase)
```

- Длина кабеля: `ChainLengthMax() = max(L[0..N−2]) + 1` (место под Inh на maxL+1; якорь Inh@2 при L=1).
- **Mute:** active tip → Exc+Inh (**2** links). **Done / CalibrateLtz:** все пары → **2N** links.
- Amp/Initial mute видят пару Exc+Inh → согласовано с recognition. Отдельный тюнинг Inh R в первом прогоне не делается.
- При `false` поведение как baseline (только Exc, N links).

Пример при `L=[69,42,25,1]`: Inh на `{70,43,26,2}`.

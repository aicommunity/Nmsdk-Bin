# TimeNeuronTimeLearnerBranchTest_NextSegInh

Тест селективности после обучения с **`EnableNextSegmentInhibition=1`**
([`TimeNeuronTimeLearnerBranch_NextSegInh`](../TimeNeuronTimeLearnerBranch_NextSegInh/)).

Алгоритм: [../TimeNeuronTimeLearnerBranch/ALGORITHM.md](../TimeNeuronTimeLearnerBranch/ALGORITHM.md).

## Проводка (из learner)

| pulse | Exc | Inh |
|------:|-----|-----|
| 0 | Dendrite1_89 | Dendrite1_90 |
| 1 | Dendrite1_46 | Dendrite1_47 |
| 2 | Dendrite1_25 | Dendrite1_26 |
| 3 | Dendrite1_1 | Dendrite1_2 |

`StructureBuildMode=0` (сохраняем обученную топологию Exc+Inh). `FixedLTZ≈0.065`.

## Прогон

```bash
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranchTest_NextSegInh/Project.ini \
  -s -t 20 -x
```

## Метрики

| | baseline amp-eq | static Inh (старый XML) | **trained NextSegInh** |
|--|:---:|:---:|:---:|
| **acc** | 6/8 | 7/8 | **7/8** |
| fn | 0 | 1 | **0** |
| fp | 2 | 0 | **1** (trial 6) |

| trial | class | fired | soma_sum | match |
|------:|------:|------:|---------:|------:|
| 0 | 1 | 1 | 0.0650 | 1 |
| 1 | 0 | 0 | 0.0340 | 1 |
| 2 | 0 | 0 | 0.0629 | 1 |
| 3 | 0 | 0 | 0.0493 | 1 |
| 4 | 0 | 0 | 0.0637 | 1 |
| 5 | 0 | 0 | 0.0345 | 1 |
| 6 | 0 | 1 | 0.0676 | 0 |
| 7 | 0 | 0 | 0.0329 | 1 |

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
Analyzer: `PostPatternWindow=0.5`, `LateResponseWindow=1.5`.

## Прогон

```bash
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranchTest_NextSegInh/Project.ini \
  -s -t 20 -x
```

## Метрики

| | baseline amp-eq | static Inh (старый XML) | **trained NextSegInh** |
|--|:---:|:---:|:---:|
| **acc (match)** | 6/8 | 7/8 | **7/8** |
| fn | 0 | 1 | **0** |
| fp | 2 | 0 | **1** (trial 6) |
| late_fp | — | — | **4** (1,2,5,7) |
| late_fn | — | — | **0** |

| trial | class | fired | late | late_t_rel | soma_sum | match | error_class |
|------:|------:|------:|-----:|-----------:|---------:|------:|:-----------:|
| 0 | 1 | 1 | 0 | — | 0.0650 | 1 | ok |
| 1 | 0 | 0 | 1 | 1.23 | 0.0650 | 1 | late_fp |
| 2 | 0 | 0 | 1 | 0.99 | 0.0650 | 1 | late_fp |
| 3 | 0 | 0 | 0 | — | 0.0507 | 1 | ok |
| 4 | 0 | 0 | 0 | — | 0.0637 | 1 | ok |
| 5 | 0 | 0 | 1 | 1.29 | 0.0650 | 1 | late_fp |
| 6 | 0 | 1 | 0 | — | 0.0676 | 0 | fp |
| 7 | 0 | 0 | 1 | 1.20 | 0.0650 | 1 | late_fp |

`match` / `neuron_fired` — только in-window. `late_fp` — nontarget без in-window fire, но LTZone поднялся после `PostPatternWindow` (GUI «пара поздних спайков»).

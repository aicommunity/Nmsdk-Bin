# TimeNeuronTimeLearnerBranchTest

Тест селективности обученного `NNeuronTimeLearnerBranch` на 8 стимулах (1 целевой + 7 отрицательных). Алгоритм: [../TimeNeuronTimeLearnerBranch/ALGORITHM.md](../TimeNeuronTimeLearnerBranch/ALGORITHM.md).

## Прогон

```bash
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranchTest/Project.ini \
  -s -t 20 -x
```

## Состояние модели (после обучения с R×N + CalibrateLtz)

- `DendriteLength = [69, 42, 25, 1]`
- `TipSynapseResistance` — уже после **R×N** (обучение)
- `FixedLTZThreshold ≈ 0.066` — после **CalibrateLtz** (`peak×0.99`)
- `IsNeedToTrain = 0`

## Результаты (`SelectivityLog/results.csv`)

| trial | target_class | neuron_fired | match | soma_amp_sum |
|-------|--------------|--------------|-------|--------------|
| 0 | 1 | 1 | **1** | 0.0660 |
| 1 | 0 | 0 | **1** | 0.0468 |
| 2 | 0 | 0 | **1** | 0.0660 |
| 3 | 0 | 0 | **1** | 0.0483 |
| 4 | 0 | 1 | 0 | 0.0661 |
| 5 | 0 | 0 | **1** | 0.0411 |
| 6 | 0 | 1 | 0 | 0.0686 |
| 7 | 0 | 0 | **1** | 0.0426 |

**Точность: 6/8** (FN=0, FP=2: trials 4 и 6). Достигнуто автоматически этапами Done обучения (без ручного масштаба R / подбора thr).

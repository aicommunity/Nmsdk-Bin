# TimeNeuronTimeLearnerBranchTest

Тест селективности обученного `NNeuronTimeLearnerBranch` на 8 стимулах (1 целевой + 7 отрицательных). Алгоритм: [../TimeNeuronTimeLearnerBranch/ALGORITHM.md](../TimeNeuronTimeLearnerBranch/ALGORITHM.md).

## Прогон

```bash
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranchTest/Project.ini \
  -s -t 20 -x
```

## Состояние модели (после amp-eq R×N×(I/I_ref) + CalibrateLtz)

- `DendriteLength = [85, 46, 25, 1]`
- `TipSynapseResistance` — после **R×N×(Initial/I_ref)** (проксимальный tip R≈4.28e8)
- `FixedLTZThreshold ≈ 0.0728` — после **CalibrateLtz** (`peak×0.99`)
- `IsNeedToTrain = 0`

## Результаты (`SelectivityLog/results.csv`)

| trial | target_class | neuron_fired | match | soma_amp_sum |
|-------|--------------|--------------|-------|--------------|
| 0 | 1 | 1 | **1** | 0.0728 |
| 1 | 0 | 0 | **1** | 0.0426 |
| 2 | 0 | 1 | 0 | 0.0729 |
| 3 | 0 | 0 | **1** | 0.0559 |
| 4 | 0 | 0 | **1** | 0.0719 |
| 5 | 0 | 0 | **1** | 0.0418 |
| 6 | 0 | 1 | 0 | 0.0751 |
| 7 | 0 | 0 | **1** | 0.0431 |

**Точность: 6/8** (FN=0, FP=2: trials 2 и 6).

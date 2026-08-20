# TimeNeuronTimeLearnerBranchTest

Тест селективности обученного `NNeuronTimeLearnerBranch` на 8 стимулах (1 целевой + 7 отрицательных). Алгоритм обучения: [../TimeNeuronTimeLearnerBranch/ALGORITHM.md](../TimeNeuronTimeLearnerBranch/ALGORITHM.md).

## Прогон

```bash
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranchTest/Project.ini \
  -s -t 20 -x
```

## Состояние модели

- `DendriteLength = [85, 46, 25, 1]`
- `Generator1.Output` → 4 связи: `Dendrite1_85/46/25/1.ExcSynapse1`
- `IsNeedToTrain = 0`
- Сопротивления синапсов: `R_test = 4 × R_trained` (нормализация 1/N при параллельной активации)
- **`FixedLTZThreshold = LTZThreshold = LTZone.Threshold = 0.0724`**

## Подбор порога LTZ

Unconstrained-пики (`thr=1.0`, без спайка):

| trial | class | soma_amp_sum |
|-------|-------|--------------|
| 0 | 1 | **0.0730** |
| 1 | 0 | 0.0425 |
| 2 | 0 | **0.0751** |
| 3 | 0 | 0.0559 |
| 4 | 0 | 0.0718 |
| 5 | 0 | 0.0417 |
| 6 | 0 | **0.1070** |
| 7 | 0 | 0.0431 |

Рабочее окно для 6/8: `thr ∈ (0.0718, 0.0730)` — цель срабатывает, 5 негативов отсекаются; trials 2 и 6 остаются FP (пик выше цели).

Выбрано **`0.0724`**. Артефакты sweep: [`ltz_sweep/`](ltz_sweep/).

## Результаты (`SelectivityLog/results.csv`) — thr=0.0724

| trial | target_class | neuron_fired | match | soma_amp_sum |
|-------|--------------|--------------|-------|--------------|
| 0 | 1 | 1 | **1** | 0.0724 |
| 1 | 0 | 0 | **1** | 0.0425 |
| 2 | 0 | 1 | 0 | 0.0725 |
| 3 | 0 | 0 | **1** | 0.0559 |
| 4 | 0 | 0 | **1** | 0.0718 |
| 5 | 0 | 0 | **1** | 0.0417 |
| 6 | 0 | 1 | 0 | 0.0750 |
| 7 | 0 | 0 | **1** | 0.0431 |

**Точность: 6/8** (FN=0, FP=2: permute mid / early-cluster). Совпадает с лучшим config-only результатом Phase A для классического TimeLearner.

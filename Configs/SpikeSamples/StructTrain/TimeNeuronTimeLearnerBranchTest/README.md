# TimeNeuronTimeLearnerBranchTest

Тест селективности обученного `NNeuronTimeLearnerBranch` на 8 стимулах (1 целевой + 7 отрицательных). Алгоритм обучения: [../TimeNeuronTimeLearnerBranch/ALGORITHM.md](../TimeNeuronTimeLearnerBranch/ALGORITHM.md).

## Прогон

```bash
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranchTest/Project.ini \
  -s -t 160 -x
```

## Состояние после переноса (2026-08-20)

Из train-конфига перенесены согласованные `Parameters_00.xml` + `Model_00.xml`:

- `DendriteLength = [85, 46, 25, 1]`
- `Generator1.Output` → **4** связи: `Dendrite1_85/46/25/1.ExcSynapse1` (без stale `9,17,25,33,41`)
- `IsNeedToTrain = 0`

## Результаты (`SelectivityLog/results.csv`)

| trial | target_class | neuron_fired | match |
|-------|-------------|--------------|-------|
| 0 | 1 | 1 | 1 |
| 1–7 | 0 | 1 | 0 |

- Целевой паттерн (trial 0): **корректное срабатывание** (`neuron_fired=1`, `match=1`).
- Отрицательные стимулы: ложные срабатывания (`neuron_fired=1` на всех) → `match=0`.
- Точность по `match`: **1/8**; топология связей и обучение корректны, селективность требует отдельной настройки LTZ/порога.

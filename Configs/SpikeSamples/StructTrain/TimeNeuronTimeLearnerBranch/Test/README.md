# TimeNeuronTimeLearnerBranchTest

Тест селективности обученного `NNeuronTimeLearnerBranch` на 8 стимулах (1 целевой + 7 отрицательных). Алгоритм: [../TimeNeuronTimeLearnerBranch/ALGORITHM.md](../TimeNeuronTimeLearnerBranch/ALGORITHM.md).

Analyzer: `PostPatternWindow=0.5`, `LateResponseWindow=1.5`.

Watch (`Interface.xml` tab_1 верхний): `InputPattern`, `Generator1.Output`, `Neuron.DendriticSumPotential`, `Neuron.SomaSumPotential`, `LTZone.Potential (вход)`.

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

| trial | class | fired | late | late_t_rel | soma_sum | match | error_class |
|------:|------:|------:|-----:|-----------:|---------:|------:|:-----------:|
| 0 | 1 | 1 | 0 | — | 0.0728 | 1 | ok |
| 1 | 0 | 0 | 1 | 1.21 | 0.0728 | 1 | late_fp |
| 2 | 0 | 1 | 0 | — | 0.0729 | 0 | fp |
| 3 | 0 | 0 | 0 | — | 0.0559 | 1 | ok |
| 4 | 0 | 0 | 0 | — | 0.0719 | 1 | ok |
| 5 | 0 | 0 | 0 | — | 0.0721 | 1 | ok |
| 6 | 0 | 1 | 0 | — | 0.0751 | 0 | fp |
| 7 | 0 | 0 | 1 | 1.17 | 0.0728 | 1 | late_fp |

**match: 6/8** (fn=0, fp=2 на 2 и 6). Дополнительно **late_fp=2** (1, 7). `late_fn=0`.


> Layout 2026-09-10: Train/Test under one root. See ../../LAYOUT.md and ../../AUDIT_REPORT.md (Branch legacy 7/8 demoted: late_fp + per_stim).

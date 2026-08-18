# TimeNeuronTimeLearnerBranch

Минимальный пример `NNeuronTimeLearnerBranch`: **1 сома + 1 дендрит**, импульсы паттерна на разном расстоянии от сомы. Алгоритм: [ALGORITHM.md](ALGORITHM.md).

## Параметры

- `NumInputDendrite = 4` — четыре **импульса** (не четыре дендрита)
- `DendriteLength` cold: `1, 1, 1, 0` (позиции импульсов; якорь на Soma1)
- `InputPattern` ISI: `0.01 / 0.08 / 0.16 / 0.24` (исходный паттерн, без time-compress)
- `IterationGap = 1.5`, `Delay = 1.5`, `SyncTolerance = 0.02`
- `NormalizationMode = 1`, `NeuronClassName = NSPNeuronGen`
- Обучение: `IsNeedToTrain = 1`, `TrainingLTZThreshold = 100`

## Прогон

```bash
cmake --build build/linux-gcc-debug-local --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranch/Project.ini \
  -s -t 160 -x
```

Ожидание: якорь commit → импульсы 2→1→0; `DendriteLength[3]=0`; `L0>L1>L2≥1`; одна цепь `Dendrite1_*`; `phase -> Done`.

# TimeNeuronTimeLearner

Минимальный пример `NNeuronTimeLearner`: один компонент с `StructureBuildMode=1` собирает `Neuron` + `DatasetMatrix` и fan-out `Generator1` на все дендриты.

Полное описание алгоритма: [ALGORITHM.md](ALGORITHM.md).

## Параметры

- `NumInputDendrite = 4`
- `InputPattern` ISI: `0.01 / 0.03 / 0.06 / 0.07`
- `IterationGap = 0.5`, `Delay = 0.5`
- `SyncTolerance = 0.02`
- `NeuronClassName = NSPNeuronGen`
- `IsNeedToTrain = 1`, `EnableDebug = 1`

## Прогон

```bash
cmake --build build/linux-gcc-debug-local --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)
./NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearner/Project.ini \
  -s -t 30 -x
```

Ожидание Sync: batch-рост `len` у дендритов 1..N−1, ненулевой `amp` после роста, `phase -> Normalize` при `|dsyn| ≤ SyncTolerance`.

Для сброса к необученному состоянию: `DendriteLength = 1 1 1 1`, `ResetToUntrainedState = 1`.

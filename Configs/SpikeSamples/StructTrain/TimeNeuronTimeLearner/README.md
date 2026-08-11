# TimeNeuronTimeLearner

Минимальный пример `NNeuronTimeLearner`: один компонент с `StructureBuildMode=1` собирает `Neuron` + `DatasetMatrix` и fan-out `Generator1` на все дендриты.

Полное описание алгоритма: [ALGORITHM.md](ALGORITHM.md).

## Параметры

- `NumInputDendrite = 4`
- `InputPattern` ISI: `0.01 / 0.08 / 0.16 / 0.24` (кумулятивные времена ≈ `0.01, 0.09, 0.25, 0.49`)
- `IterationGap = 1.5`, `Delay = 1.5` (≥ span + settle)
- `SyncTolerance = 0.02`
- `NeuronClassName = NSPNeuronGen`
- `IsNeedToTrain = 1`, `EnableDebug = 1`

## Прогон

```bash
cmake --build build/linux-gcc-debug-local --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearner/Project.ini \
  -s -t 60 -x
```

Ожидание Sync: первая пачка — bootstrap `PrevPeakRel`; далее `active=k`, `ApplyPending changed=[k:…]`, разные `len` (ранние дендриты длиннее), `phase -> Normalize` при `|lastAbsDt| ≤ SyncTolerance`.

Для сброса к необученному состоянию: `DendriteLength = 1 1 1 1`, `ResetToUntrainedState = 1`.

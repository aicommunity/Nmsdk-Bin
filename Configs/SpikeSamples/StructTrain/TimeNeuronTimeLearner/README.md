# TimeNeuronTimeLearner

Минимальный пример `NNeuronTimeLearner`: `StructureBuildMode=1` собирает `Neuron` + `DatasetMatrix` и fan-out `Generator1` на все дендриты. Рядом — `UStatisticDoubleMatrix` для записи сом/суммы в `StatisticLog/`.

Полное описание: [ALGORITHM.md](ALGORITHM.md).

## Параметры

- `NumInputDendrite = 4`
- `InputPattern` ISI: `0.01 / 0.08 / 0.16 / 0.24`
- `IterationGap = 1.5`, `Delay = 1.5`, `SyncTolerance = 0.02`
- `NeuronClassName = NSPNeuronGen`
- Для обучения: `IsNeedToTrain = 1`; сброс: `DendriteLength = 1 1 1 1`, `NumSynapse = 1 1 1 1`, `ResetToUntrainedState = 1`

## Прогон

```bash
cmake --build build/linux-gcc-debug-local --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearner/Project.ini \
  -s -t 120 -x
```

Ожидание: `L0 > L1 > L2 > 1`, дифференцированный `NumSynapse`, amp ≈ Initial (или best-effort@64 / dead tip), один доминирующий пик на сумме сом, `phase -> Done`.

После Done: `-t 8` и разбор `StatisticLog/` — один доминирующий пик sum (вторичный ≪ или Δt≪0.08 с).

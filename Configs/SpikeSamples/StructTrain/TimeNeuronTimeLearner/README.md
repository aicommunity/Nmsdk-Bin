# TimeNeuronTimeLearner

Минимальный пример `NNeuronTimeLearner`: `StructureBuildMode=1` собирает `Neuron` + `DatasetMatrix` и fan-out `Generator1` на все дендриты. Рядом — `UStatisticDoubleMatrix` для записи сом/суммы в `StatisticLog/`.

Полное описание: [ALGORITHM.md](ALGORITHM.md).

## Параметры

- `NumInputDendrite = 4`
- `InputPattern` ISI: `0.01 / 0.08 / 0.16 / 0.24`
- `IterationGap = 1.5`, `Delay = 1.5`, `SyncTolerance = 0.02`
- `NeuronClassName = NSPNeuronGen`
- `NormalizationMode = 1` (parametric, по умолчанию); structural: `NormalizationMode = 0`
- `ResistanceAdjustGain = 0.4` (уменьшать до 0.2–0.3 при осцилляции R)
- Для обучения: `IsNeedToTrain = 1`; сброс: `DendriteLength = 1 1 1 1`, `NumSynapse = 1 1 1 1`, `ResetToUntrainedState = 1`

### Parametric (NormalizationMode=1)

После reset добавьте в `Parameters_00.xml` (секция `NeuronTimeLearner`):

```xml
<NormalizationMode Type="i" ...>1</NormalizationMode>
<SynapseResistanceBase Type="d" ...>86000000</SynapseResistanceBase>
<ResistanceMin Type="d" ...>1000000</ResistanceMin>
<ResistanceMax Type="d" ...>1e11</ResistanceMax>
<AttenuationGamma Type="d" ...>-1</AttenuationGamma>
<ResistanceAdjustGain Type="d" ...>0.4</ResistanceAdjustGain>
```

Ожидание: `NumSynapse=[1,1,1,1]`, `phase -> Done` быстрее structural; в debug-log — `DampedResistance`, `adjGain=[...]`, `noImpR=[...]`, `resStatus=[...]`.

## Прогон

```bash
cmake --build build/linux-gcc-debug-local --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearner/Project.ini \
  -s -t 120 -x
```

Ожидание: `L0 > L1 > L2 > 1`, дифференцированный `NumSynapse`, amp ≈ Initial (или best-effort@128 / dead tip), один доминирующий пик на сумме сом, `phase -> Done`.

После Done: `-t 8` и разбор `StatisticLog/` — один доминирующий пик sum (вторичный ≪ или Δt≪0.08 с).

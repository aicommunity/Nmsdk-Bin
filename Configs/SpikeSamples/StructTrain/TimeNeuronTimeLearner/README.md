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
- Для обучения: `IsNeedToTrain = 1`
- Сброс к cold: достаточно `ResetToUntrainedState = 1` + Reset компонента — даже если в `Parameters_00.xml` уже лежат обученные `DendriteLength`/`TipSynapseResistance`/`InitialSomaPotential` (как в этом семпле: `49 41 25 1`). Флаг сбрасывает структуру в `L=1`, tip R = `SynapseResistanceBase`, `Initial=0`. Ручная правка `DendriteLength = 1 1 1 1` не обязательна.

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
Ход amp/R: `StatisticLog/*/NeuronTimeLearner.AmpDtTrace.txt`, `TipSynapseResistanceTrace.txt`, `StimulusIterTrace.txt`.
`[49,41,25,1]` в sample — уже settled cable sync; Done ждёт нормализацию amp (не рост L).

## Прогон

```bash
cmake --build build/linux-gcc-debug-local --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearner/Project.ini \
  -s -t 120 -x
```

Ожидание: `L0 > L1 > L2 > 1`, дифференцированный `NumSynapse`, amp ≈ Initial (или best-effort@128 / dead tip), один доминирующий пик на сумме сом, `phase -> Done`.

После Done: `-t 8` и разбор `StatisticLog/` — один доминирующий пик sum (вторичный ≪ или Δt≪0.08 с).

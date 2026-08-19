# TimeNeuronTimeLearnerBranch

Минимальный пример `NNeuronTimeLearnerBranch`: **1 сома + 1 дендрит**, импульсы паттерна на разном расстоянии от сомы. Алгоритм: [ALGORITHM.md](ALGORITHM.md).

## Параметры

- `NumInputDendrite = 4` — четыре **импульса** (не четыре дендрита)
- `DendriteLength` cold: `1, 1, 1, 1` (все импульсы на `Dendrite1_1`; на `Soma1` входов нет)
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

Ожидание: якорь commit → импульсы 2→1→0; `DendriteLength[3]≥1`; `L0>L1>L2≥1`; одна цепь `Dendrite1_*`; `phase -> Done`.

## GUI (графики)

Открыть в NeuroModeler:

`Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranch/Project.ini`

Меню **Watch** (две вкладки, как в `TimeNeuronTimeLearner` / EXP00_baseline):

| Вкладка | Что смотреть |
|---------|----------------|
| **tab_1** | ISI-паттерн, `Generator1`, `Neuron.Output`; **Soma Amplitudes** — пики по импульсам |
| **tab_2** | `DendriteNeuronAmplitude`, суммы нейрона (`SomaSumPotential`, `DendriticSumPotential`, LTZone) |

Входной синапс: `Dendrite1_1.ExcSynapse1` (один на сегмент; активный импульс переключается mute).

Запуск расчёта: Start, время ≥ 20–30 s для двух burst’ов (или `-t 160` из консоли).

## Последний прогон (2026-08-19)

- Выполнен повторный cold-run с очисткой runtime-логов и сохранением проекта через `-S`.
- По итоговому `Model_00.xml` входные связи от `DatasetMatrix.Generator1` расположены на дендритных сегментах:
  `Dendrite1_9`, `Dendrite1_17`, `Dendrite1_25`, `Dendrite1_33`, `Dendrite1_41`, `Dendrite1_44`.
- Итоговые обученные параметры в `Parameters_00.xml`:
  - `DendriteLength = [1, 44, 26, 1]`
  - `TipSynapseResistance = [86000000, 100000000000, 100000000000, 86000000]`
- В `EventsLog` этого прогона строка `phase -> Done` не зафиксирована (обучение осталось в `phase=0`), поэтому состояние рассматривается как частично обученное.

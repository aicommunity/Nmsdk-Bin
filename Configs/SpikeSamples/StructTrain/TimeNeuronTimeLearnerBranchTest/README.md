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

## Последний ретест (2026-08-19)

- В `BranchTest` перенесены параметры из последнего train-run:
  - `DendriteLength = [1, 44, 26, 1]`
  - `TipSynapseResistance = [86000000, 100000000000, 100000000000, 86000000]`
- Выполнен повторный тест на 8 стимулах (`SelectivityLog/results.csv`).
- Наблюдение по результату: нейрон не выдаёт `neuron_fired=1` ни на одном из 8 стимулов, при этом совпадение класса `match=1` есть только для 7 отрицательных примеров.
- Точность текущего ретеста: `7/8 = 87.5%` (ложный пропуск на целевом классе, trial=0).

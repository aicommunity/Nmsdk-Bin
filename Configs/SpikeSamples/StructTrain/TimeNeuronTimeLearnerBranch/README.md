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

Ожидание: якорь commit → импульсы 2→1→0; `DendriteLength[3]≥1`; `L0>L1>L2≥1`; одна цепь `Dendrite1_*`; затем **`CalibrateLtz`** (`R×N×(Initial/I_ref)` amp-eq якоря + `FixedLTZ=peak×0.99`) → `phase -> Done`.

После успешного прогона (пример): `DendriteLength≈[69,42,25,1]`, tip-R уже с amp-eq×N (проксимальный tip ≫ Base×N), `FixedLTZ` по parallel peak; BranchTest — см. актуальный `SelectivityLog/results.csv`.

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

## Последний прогон (2026-08-20)

- Исправлена линковка `Generator1.Output → ExcSynapse1`: stale links больше не накапливаются при росте кабеля (шаг +8).
- Cold retrain с `DendriteLength = [1,1,1,1]` до **`phase -> Done`**.
- Итоговые параметры (`Parameters_00.xml`):
  - `DendriteLength = [85, 46, 25, 1]` — `L0 > L1 > L2`, якорь на `Dendrite1_1`
  - `TipSynapseResistance = [1e6, 2.56e7, 2.33e7, 8.6e7]`
- Итоговые связи в `Model_00.xml` (**ровно 4**):
  `Dendrite1_85`, `Dendrite1_46`, `Dendrite1_25`, `Dendrite1_1` (импульсы 0..3).

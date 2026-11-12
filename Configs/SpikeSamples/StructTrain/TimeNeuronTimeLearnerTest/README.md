# TimeNeuronTimeLearnerTest — selectivity (same window)

Прогон **обученного** `NNeuronTimeLearner` (`IsNeedToTrain=0`, `DendriteLength=49/41/25/1`) по **8 ISI-паттернам один раз** через `DatasetMatrix` (`LoopSamples=0`, `AdvanceSampleAfterBurst=1`). У всех сэмплов одно окно **first→last = 0.48 с** (onset `0.01`, last spike на `t=0.49`). Результаты — CSV в `SelectivityLog/results.csv` (`NPatternResponseAnalyzer`).

Обучение: см. [TimeNeuronTimeLearner](../TimeNeuronTimeLearner/README.md) и [ALGORITHM.md](ALGORITHM.md).

## Tip R vs r_model (не завышение цели)

Обученные tip R ≈ `[25.8e6, 27.2e6, 21.9e6, 86e6]` при `Rbase=8.6e7`, `L=[49,41,25,1]`. Feedforward `r_model = Rbase·exp(−γ·(L−1))` ≈ `[80e6, 81e6, 83e6, 86e6]`. Дендриты 0–2 ниже модели (~0.26–0.33·r_model), но далеко от `ResistanceMin=1e6`. Это штатная компенсация кабеля: damped-P опускает R, чтобы вернуть пик сомы к `InitialSomaPotential≈0.0158` (захват на L=1). Если amp перелетал Initial, R рос бы. Done требует `|Initial−MaxIterSomaAmp|≤1e-5`. Сумма `SomaNeuronAmplitude[0]` — coincidence соматических частей при синхронных пиках, не Amplitude датасет-генератора.

## Сэмплы

Инвариант: `isi0=0.01`, `isi1+isi2+isi3=0.48`. Stretch/compress исключены.

| # | ISI (с) | class | роль |
|--:|---------|------:|------|
| 0 | 0.01 / 0.08 / 0.16 / 0.24 | 1 | обученный |
| 1 | 0.01 / 0.24 / 0.16 / 0.08 | 0 | reverse internals |
| 2 | 0.01 / 0.16 / 0.08 / 0.24 | 0 | permute mid |
| 3 | 0.01 / 0.16 / 0.16 / 0.16 | 0 | uniform в окне |
| 4 | 0.01 / 0.02 / 0.22 / 0.24 | 0 | близкая пара в начале |
| 5 | 0.01 / 0.24 / 0.22 / 0.02 | 0 | близкая пара в конце |
| 6 | 0.01 / 0.04 / 0.04 / 0.40 | 0 | ранний кластер + хвост |
| 7 | 0.01 / 0.40 / 0.04 / 0.04 | 0 | пробел + поздний кластер |

Ожидание: class **1** → `neuron_fired=1`; class **0** → тишина. Метрика `match=1` — совпадение с ожиданием.

## Прогон

```bash
cmake --build build/linux-gcc-debug-local --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerTest/Project.ini \
  -s -t 20 -x
```

CSV: 8 строк данных + header. Порог LTZ ≈ `FixedLTZThreshold=0.0115`.

## Результаты прогона (same-window, 2026-08-13)

| trial | class | fired | match | тип |
|------:|------:|------:|------:|-----|
| 0 | 1 | 1 | 1 | trained |
| 1 | 0 | 0 | 1 | reverse internals |
| 2 | 0 | 1 | 0 | permute mid — FP |
| 3 | 0 | 0 | 1 | uniform |
| 4 | 0 | 1 | 0 | близкая пара в начале — FP |
| 5 | 0 | 1 | 0 | близкая пара в конце — FP |
| 6 | 0 | 1 | 0 | ранний кластер — FP |
| 7 | 0 | 0 | 1 | поздний кластер |

**Accuracy = 4/8 (50%).** Обученный паттерн срабатывает. При том же окне 0.48 с:

- **тишина:** reverse internals, uniform, поздний кластер
- **FP:** permute mid, близкие пары (начало/конец), ранний кластер

Избирательность по полному порядку слабая: часть перестановок и локальные сгущения в начале окна всё ещё вызывают спайк. Поздняя концентрация нагрузки и равномерная сетка отвергаются лучше.

## Wiring

- `DatasetMatrix.Generator1.Output` → `PatternResponseAnalyzer.StimulusInputs`
- `Neuron.LTZone.Output` → `PatternResponseAnalyzer.NeuronOutputs`
- `DatasetMatrix.CurrentClassMatrix` → `PatternResponseAnalyzer.TargetClassInput`

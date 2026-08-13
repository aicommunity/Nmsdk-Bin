# TimeNeuronTimeLearnerTest — selectivity

Прогон **обученного** `NNeuronTimeLearner` (`IsNeedToTrain=0`, `DendriteLength=49/41/25/1`) по **6 ISI-паттернам один раз** через `DatasetMatrix` (`LoopSamples=0`, `AdvanceSampleAfterBurst=1`). Результаты — CSV в `SelectivityLog/results.csv` (`NPatternResponseAnalyzer`).

Обучение: см. [TimeNeuronTimeLearner](../TimeNeuronTimeLearner/README.md) и [ALGORITHM.md](ALGORITHM.md).

## Сэмплы

| # | ISI (с) | class | роль |
|--:|---------|------:|------|
| 0 | 0.01 / 0.08 / 0.16 / 0.24 | 1 | обученный паттерн |
| 1 | reverse 0.24→0.01 | 0 | дистрактор |
| 2 | uniform 0.12×4 | 0 | дистрактор |
| 3 | stretch ×2 | 0 | дистрактор |
| 4 | compress ×0.5 | 0 | дистрактор |
| 5 | permute ISI | 0 | дистрактор |

Ожидание: class **1** → `neuron_fired=1`; class **0** → тишина. Метрика `match=1` — совпадение с ожиданием.

## Прогон

```bash
cmake --build build/linux-gcc-debug-local --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerTest/Project.ini \
  -s -t 15 -x
```

CSV: 6 строк данных + header. Порог LTZ ≈ `FixedLTZThreshold=0.0115`.

## Результаты прогона (2026-08-13)

| trial | class | fired | match | комментарий |
|------:|------:|------:|------:|-------------|
| 0 | 1 | 1 | 1 | обученный ISI — срабатывание |
| 1 | 0 | 1 | 0 | reverse — ложное срабатывание |
| 2 | 0 | 0 | 1 | uniform — тишина |
| 3 | 0 | 0 | 1 | stretch — тишина |
| 4 | 0 | 1 | 0 | compress — ложное срабатывание |
| 5 | 0 | 1 | 0 | permute — ложное срабатывание |

**Accuracy = 3/6 (50%).** Нейрон избирателен на uniform/stretch, но reverse/compress/permute дают FP. Обученный паттерн распознаётся (trial 0).

## Wiring

- `DatasetMatrix.Generator1.Output` → `PatternResponseAnalyzer.StimulusInputs`
- `Neuron.LTZone.Output` → `PatternResponseAnalyzer.NeuronOutputs`
- `DatasetMatrix.CurrentClassMatrix` → `PatternResponseAnalyzer.TargetClassInput`

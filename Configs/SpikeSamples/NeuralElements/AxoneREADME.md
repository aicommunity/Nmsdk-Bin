# Axone experiments (NeuralElements)

Smoke / compare configs for PulseLib axon models (`NAxone*`).

| Config | What it compares |
|--------|------------------|
| [AxoneTypesCompare](AxoneTypesCompare/) | Delay vs Chain vs ChainAndDelay |
| [AxoneDelaySweep](AxoneDelaySweep/) | DelayTime 1 / 5 / 10 ms |
| [AxoneChainLengthSweep](AxoneChainLengthSweep/) | NumSegments 1 / 3 / 5 |
| [AxoneLengthDelayStudy](AxoneLengthDelayStudy/) | delay vs length (15 cells, metrics + plots) |

Общий вход: `NPGenerator` 10 Hz, pulse 1 ms. `DefaultTimeStep=2000`.

**Регенеративный сегмент:** `Inertial` (`Bias=-1`) → ExcChannel; `PosGenerator`(+1) → InhChannel; `LTZone` ↔ `Soma` feedback (как минимальный нейрон). `LTZone.Threshold=0.03` (не дефолт класса `1e-5`; для минимального сегмента без синапсов значение StructTrain `0.0115` слишком низко — LTZ срабатывает на первом шаге импульса).

Раскладка на схеме: Inertial (2,6.5), PosGenerator (2,2), Soma (8,4.5), LTZone (14,4.5); в Chain сегменты с шагом 18 по X; в ChainAndDelay — зазоры 2 (0.5 блока) между Segment(~16) и Delay(~4), period=24.

Watch: `Interface.xml` schemaVersion=2 (эталон StructTrain PreInh250).

## Manual check

1. `NeuroModelerConsole --check-config <dir>/project.ini` — VALID.
2. NeuroModeler: Reset → Start → Watch: импульсы на выходах Delay и Chain.

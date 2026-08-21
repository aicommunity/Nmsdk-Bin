# Axone experiments (NeuralElements)

Smoke / compare configs for PulseLib axon models (`NAxone*`).

| Config | What it compares |
|--------|------------------|
| [AxoneTypesCompare](AxoneTypesCompare/) | Delay vs Chain vs ChainAndDelay |
| [AxoneDelaySweep](AxoneDelaySweep/) | DelayTime 1 / 5 / 10 ms |
| [AxoneChainLengthSweep](AxoneChainLengthSweep/) | NumSegments 1 / 3 / 5 |

Общий вход: `NPGenerator` 10 Hz, pulse 1 ms. `DefaultTimeStep=2000`.

**Регенеративный сегмент:** `Inertial` (`Bias=-1`) → ExcChannel; `PosGenerator`(+1) → InhChannel; `LTZone` ↔ `Soma` feedback (как минимальный нейрон).

Раскладка на схеме: Inertial (2,6.5), PosGenerator (2,2), Soma (8,4.5), LTZone (16,4.5); в Chain сегменты с шагом 20 по X; в ChainAndDelay — равные зазоры 2 между Segment(~18) и Delay(~4).

Watch: `Interface.xml` schemaVersion=2 (эталон StructTrain PreInh250).

## Manual check

1. `NeuroModelerConsole --check-config <dir>/project.ini` — VALID.
2. NeuroModeler: Reset → Start → Watch: импульсы на выходах Delay и Chain.

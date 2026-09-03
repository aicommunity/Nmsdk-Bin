# L Oscillation Audit

**EXP:** EXP_span25ms_packA_gen  
**Источник:** pilot v3 StatisticLog `2026.09.02 09-13-20` (аудит до cold reset v4)  
**Final L (v3):** `6 5 3 1`  
**Reference L (LtzCal Done):** `6 5 4 1`

## Вывод

Осцилляция L на соседних значениях вызвана **расхождением cable-model (`delay_len`) и измеренного пика** в `ChangeDendriteStatus`:

| Дендрит | needed | delay_len @ L_ref | dt @ L_ref | Интерпретация |
|---------|--------|-------------------|------------|---------------|
| d0 | 0.0250 | 0.0260 | −0.0010 | cable чуть длиннее → shrink |
| d1 | 0.0208 | 0.0208 | 0.0 | settled |
| d2 | 0.0125 | 0.0156 | −0.0031 | cable длиннее → shrink (L=4→3) |
| d3 | ref | — | — | — |

При L на одну сегмента короче (d2: L=3) `delay_len < needed` → grow обратно к L=4. Цикл повторяется в joint train (amp + ΔL в одной итерации).

**Драйвер:** `delay_len` (кабельная модель), не `DelayFromPulse`, когда `meas_agrees=false` в `DelayUseOf`.

## Системный fix (C++)

В `NNeuronTimeLearner.cpp`:

1. **peak_synced hold** — если `SomaPeakValid` и `|needed − delay_meas| ≤ SyncTolerance`, не менять L (универсально, без hardcode длины).
2. **ApplyPendingDendriteLengthChanges** — пропуск ΔL для дендритов с `peak_valid && DendLastAbsDt ≤ tol`.

Контрольные L (`6 5 4 1`) остаются в `l_reference.json` / скриптах эксперимента.

## Pilot v4

Cold reset + train с новым бинарником. Старт с L_ref floor `6 5 4 1` → amp-фаза проверяет удержание L при C++ fix.

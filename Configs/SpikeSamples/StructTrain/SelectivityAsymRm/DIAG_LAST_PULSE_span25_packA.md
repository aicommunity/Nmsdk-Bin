# DIAG: last-pulse / crown — EXP_span25ms_packA_gen

Дата: 2026-09-11.  
Объекты: [`SelectivityAsymRm/EXP_span25ms_packA_gen`](EXP_span25ms_packA_gen/), twin [`../SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen`](../SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/).  
Срез CSV: восстановлен из git HEAD (8 проб); `AutoCalibrate` на AsymRm Test Model = 0.

## Вердикт

**Dominant cause: mix — H-sync ~60% / H-tau ~40%.**  
H-amp: **нет** (InitialSoma d0–d2 ≈ 0.100331; якорь d3 в AsymRm Train аномален `~5.6e13`, не объясняет early-spike на цели).

Запускать **фазу 2 (C++ analyzer + short-span sync)** и **фазу 3 (ChannelRcSweep / более медленная C)**.

## Числа (AsymRm Test, trial 0)

| Величина | Значение |
|----------|----------|
| Neuron | `NSPNeuronGenAsymRmD001C25e12` |
| L actual | `6 5 4 1` |
| L formula / peak | `6 5 3 1` (d2 FORMULA_OFF, ΔL=+1) |
| EstDelayPerSeg | 0.005 с |
| τ_mem = Rm·C | **0.25 мс** (Rm=1e7, C=2.5e-11) |
| t_arrive model (мс) | 25.52, 24.69, **28.02**, 25.52 |
| σ_L (разброс) | **2.50 мс** (≥ 2·τ = 0.5 мс) |
| σ_L formula | 2.08 мс (всё ещё ≫ τ) |
| pattern_end | 0.025 с |
| neuron_t_rel | **0.00105** → **early** (&lt; 0.5·end) |
| FixedLTZ / ltz_max | 0.08694 / 0.08849 (margin ~0.00155) |
| soma_amp_0..3 | 0.056, **0.131**, 0.103, 0.099 (max = дендрит 1, не «последний импульс») |
| ltz_max / max(soma_amp) | 0.67 |
| fires (8 trials) | `10001100` (fa=2 на trials 4–5; trial5 `t_rel≈0.025`) |

LtzCal twin: те же L/σ/early (`t_rel=0.001`), fires `10001100`, τ=0.25 мс.

## Пороги плана

| Условие | Факт |
|---------|------|
| σ_L ≥ 2·τ или early fire | **да** → H-sync |
| τ &lt; 0.5 мс при ISI≈4 мс / seg=5 мс и formula σ_L ≳ τ | **да** → H-tau |
| InitialSoma d0–d2 вне ε | **нет** |

## Интерпретация

1. Отдельные мембранные bump’ы при multi-dendrite — ожидаемы при быстрой τ.
2. Last-pulse crown отсутствует: ответ на цели early; разброс прихода ~2.5 мс убивает superposition при τ=0.25 мс.
3. Формальный `ok_audit` засчитывал mid-pattern LTZone edge как target hit.

## Фаза 4 — retrain C25e11 (2026-09-11)

- Cold reset + `NSPNeuronGenAsymRmD001C25e11` (C=2.5e-10, Cap verified ×44).
- Train Done: L=`7 6 4 1`, FixedLTZ≈0.02995, NeedTrain=0.
- Peak sync: still `PEAK_PREFERS_L_ACTUAL` (formula `6 5 3 1`).
- **Test last-pulse gate: FAIL**
  - Target trial0: `neuron_fired=0` (fn); mid-pattern spike @ `t=0.01495` (после 3-го стимула, до last); analyzer корректно не считает early as fire.
  - `ltz_max` цели ≈0.030 ≈ thr — crown не выше одиночных EPSP.
  - thr=0.035 → полная тишина (ltz_max≈0.031 &lt; thr) — суммирования до crown нет.
- LtzCal twin: не поднимать в реестр; тот же класс/пайплайн до появления last-pulse на AsymRm.

### Следующие итерации (вне закрытия этого прогона)

- Калибровка порога / tip amp так, чтобы одиночный EPSP &lt; thr &lt; crown.
- Дальнейший sync (σ_L, EstDelay) и/или более сильная интеграция LTZone.
- Только после last-pulse PASS — фаза 5 (все сжатые span).

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

## Фаза tip/thr / force-L (2026-09-11) — FAIL

Конфиг после проб **возвращён** к post-C25e11 Train (L=`7 6 4 1`, TipR trained, FixedLTZ≈0.02995).

| Проба | Условие | Итог |
|-------|---------|------|
| TipR×2.5, thr=0.018, L=`6 5 3 1` | слабее tips | тишина: target `ltz≈0.009` ≪ thr; `ok_audit=0`, fn |
| TipR restore, thr=0.031, L=`6 5 3 1` | formula L | тишина: target `ltz≈0.020` &lt; thr; foil6/7 `ltz` **выше** цели |
| TipR restore, thr=0.019, avgLTZ=0, L=`6 5 3 1` | sum mode | mid-pattern spike цели @`0.01405` (не fire); foil7 fp @`0.029` last-pulse-like |
| L=`26 21 13 1`, thr=0.02 | «физическая» длина | mid-pattern цели @`0.01`; fp foil5/7 near end; crown нет |

**Вывод:** масштабирование TipR не создаёт crown (линейный режим: crown/single не растёт). Force formula-L и удлинение кабеля не убирают mid-pattern edge до last stim. `EstDelayPerSeg` остаётся ~5 мс и **не** совпадает с фактическим временем до спайка (~1–2 мс после 3-го стимула). Нужен рычаг **реальной** задержки/интеграции (Ra/τ сегмента, калибровка EstDelay по observed peak, либо иной LTZone), а не tip/thr alone.

Фаза 5 по-прежнему **не стартовать**.

## Фаза τ/EstDelay — C1e9 + EstDelay seed (2026-09-11)

### Изменения (C++)
- `EstDelayPerSeg` → `UProperty` (XML); **не** сбрасывать в `ResizeSyncVectors`.
- Класс `NSPNeuronGenAsymRmD001C1e9` (AsymRm + C=`1e-9`, τ≈10 мс как PhaseA Bio).

### Retrain packA
- Cold reset; seed `EstDelayPerSeg=0.002`; neuron C1e9.
- **Done** T=80: L=`15 12 8 1`, Cap verified `1e-9`, FixedLTZ≈`0.0118`, `NeedTrain=0`, `sync_ok_all=True`.
- Peak report: `PEAK_PREFERS_L_ACTUAL` (formula still assumes 5 мс → `[6,5,3,1]`); feas `est≈0.00179`.

### Test last-pulse gate
| Условие | Итог |
|---------|------|
| AutoCal thr≈0.0118 | **first spike late** (`t_rel≈0.045` ≥ 0.8·end) на **всех** 8 пробах → timing last-pulse **есть**, но `fire_all` / `per_stim` (10–11 спайков), `ok_audit=0` |
| thr 0.0125 / 0.014 / 0.02 | ltz_max «догоняет» thr (~thr+ε); всё ещё fire_all (регенерация LTZ) |
| TipR×2.5, thr=0.015 | nspk↓ (7), `t_rel≈0.06` late; всё ещё fire_all, **нет** margin target vs foil |

**Вывод:** рычаг τ/EstDelay **сдвинул** mid-pattern → late burst (прогресс по времени), но на span25 при τ≈10 мс и переусиленных tip’ах (Rsyn d0–d2 ~1e6) нет одиночного селективного crown. Следующее: amp-norm / более высокий Rsyn floor, промежуточная C (5e-10), или иной LTZone / refractory — не фаза 5.

## Фаза Rsyn floor / TipR reset (2026-09-11) — PASS

Корневая причина fire_all: amp-norm упёрся в `ResistanceMin=1e6` → TipR d0–d2 ~1e6 (слишком сильные tips).

| Шаг | Действие | Итог |
|-----|----------|------|
| Floor | `ResistanceMin=2e7` (было 1e6) | нельзя снова уйти в 1e6 |
| TipR | reset → `8.6e7` ×4 (SynapseResistanceBase) | слабее EPSP |
| Keep | C1e9, EstDelay=0.002, L=`15 12 8 1` | late integration |
| thr probe | FixedLTZ `0.0118` | silent / fn (ltz≈0.0097) |
| thr | FixedLTZ **`0.0096`** (AutoCal=0) | **PASS** |

### Gate (Test, confirmed)

- `ok_audit=1`, `ok_strict`, `response_quality=ok_single`, `mode=selective`, **acc 8/8**
- Target: `neuron_fired=1`, `nspk=1`, `t_rel≈0.10` ≥ 0.8·`pattern_end` (0.025) → **last-pulse**
- Foils: silent; target `ltz_max` чуть выше foils (~0.0096 vs ~0.0094–0.0095)

Amp-continue с новым полом **не** потребовался для PASS: reset TipR на base + floor + thr-калибровка достаточны. Полный amp-norm с `ResistanceMin=2e7` — опциональное упрочнение позже.

Фаза 5: можно планировать после репликации на twin / соседних pack — **не** автостарт всей сетки.

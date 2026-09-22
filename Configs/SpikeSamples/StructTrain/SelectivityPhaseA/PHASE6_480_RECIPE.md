# PHASE6 — Recipe @480 ms (full pattern)

Журнал кампании: перенос **процедуры** PHASE5 (TipR@Rmin, Rmin floor, silent-probe mid-thr, clean Test hygiene, last-pulse gate) на эталонный паттерн ~480 мс.

**ISI:** `0.01 0.08 0.16 0.24` → `pattern_end ≈ 0.48 с`.  
**Эталон уже C=1e-9**, L≈`49 41 25 1` — **не** копировать EstDelay=0.002 / short-span L с PHASE5.

Gate (процедурная цель волны, критерии кода **не** меняем): `ok_audit` + last-pulse `t_rel ≥ 0.8·pattern_end` + `ok_single`; цель **8/8 selective**. Канон `ok_audit` по-прежнему допускает acc≥4 — см. [`../SUCCESSFUL_EXPERIMENTS.md`](../SUCCESSFUL_EXPERIMENTS.md) §«Слои ворот».

Reference: [`../SelectivityAsymRm/PHASE5_SPAN50_100.md`](../SelectivityAsymRm/PHASE5_SPAN50_100.md), [`../SelectivityAsymRm/THR_FRAGILITY_DIAG.md`](../SelectivityAsymRm/THR_FRAGILITY_DIAG.md).

## Принципы

- Исторические `EXP00`–`EXP06`, `TimeNeuronTimeLearner`, PSI EXP00–15 — **не** cold-reset / не перезаписывать.
- Все прогоны — клоны под [`Phase6/`](Phase6/).
- FAIL / partial конфиги **сохраняются** со ссылками ниже.
- Branch вне scope.

## Рецепт (перенос / не перенос)

| Переносим с PHASE5 | Не копируем слепо |
|--------------------|-------------------|
| TipR@Rmin `2e7 2e7 2e7 8.6e7` | EstDelay=0.002 |
| Rmin `2e7` (эталон `1e6`) | пересчёт L short-span |
| silent-probe mid FixedLTZ | cold-reset Done исторических |
| clean Test (MatrixClasses, 4 tip connectors) | dirty inject Train→Test |
| цель 8/8 + last-pulse | смена формулы `ok_audit` |

## Wave status

| Wave | EXP | Status | Acc | Notes |
|------|-----|--------|-----|-------|
| scaffold | [`Phase6/EXP_480_gen_baseline`](Phase6/EXP_480_gen_baseline/) | mirror | 4/8 | клон EXP00; thr=0.0115 |
| 0 | [`Phase6/EXP_480_gen_tiprmin`](Phase6/EXP_480_gen_tiprmin/) | **7/8** | selective | TipR@Rmin + Rmin=2e7 + mid-thr; не 8/8 |
| 0b | [`Phase6/EXP_480_gen_thr_only`](Phase6/EXP_480_gen_thr_only/) | **7/8** | selective | только mid-thr, TipR Done |
| 1 | [`Phase6/EXP_480_preinh250_tiprmin`](Phase6/EXP_480_preinh250_tiprmin/) | **7/8** | selective | clone PSI EXP04 + TipR@Rmin |
| 1 | [`Phase6/EXP_480_ltzcal_twin_gen`](Phase6/EXP_480_ltzcal_twin_gen/) | **7/8** | selective | twin: clean Test tiprmin |
| 2 | pack-proxy | **deferred** | — | нет AsymRm-подобных pack B/C на 480 |

## Wave 0 — gen TipR@Rmin (2026-09-13)

| Item | Value |
|------|-------|
| Source | clone [`EXP00_baseline`](EXP00_baseline/) |
| TipR | `2e7 2e7 2e7 8.6e7` (+ tip ExcSynapse R) |
| ResistanceMin | `2e7` |
| Silent probe thr | 0.05 → ltz tgt=`0.017333` foil_max=`0.018237` (**gap −9.0e-4**) |
| FixedLTZ gate | **0.016894** (mid tgt ↔ max foil **below** tgt) |
| Gate | `ok_audit=1`, `ok_single`, selective **7/8**, fires=`10000010`, last-pulse `t_rel≈0.490` |
| Hard foil | trial 6 (silent ltz > tgt) — окно thr не закрывает 8/8 |

[Train](Phase6/EXP_480_gen_tiprmin/Train) · [Test](Phase6/EXP_480_gen_tiprmin/Test) · [CSV](Phase6/EXP_480_gen_tiprmin/Test/SelectivityLog/results.csv) · [silent](Phase6/EXP_480_gen_tiprmin/Test/SelectivityLog/results_silent_thr05.csv)

## Wave 0b — thr-only control (2026-09-13)

| Item | Value |
|------|-------|
| TipR | Done EXP00 (`~25.8e6 27.2e6 21.9e6 86e6`) |
| Rmin | `1e6` |
| Silent | tgt=`0.014677` foil_max=`0.014735` (gap **−5.8e-5**) |
| FixedLTZ | **0.014386** |
| Gate | **7/8** selective same fires=`10000010`; last-pulse `t_rel≈0.491` |

**Вывод 0 vs 0b:** TipR@Rmin **не** улучшил acc относительно mid-thr на Done TipR (оба 7/8, тот же FP trial6). Gap silent при TipR@Rmin **хуже** (более отрицательный).

[Train](Phase6/EXP_480_gen_thr_only/Train) · [Test](Phase6/EXP_480_gen_thr_only/Test) · [CSV](Phase6/EXP_480_gen_thr_only/Test/SelectivityLog/results.csv)

## Wave 1 — preinh250 + LtzCal twin (2026-09-13)

### preinh250 tiprmin

| Item | Value |
|------|-------|
| Source | clone PSI [`EXP04_preinh_250`](../SelectivityPresynapticInhib/EXP04_preinh_250) |
| TipR / Rmin | @Rmin / `2e7` |
| Silent | tgt=`0.039342` foil_max=`0.041606` (gap **−2.3e-3**) |
| FixedLTZ | **0.038722** |
| Gate | **7/8** selective `10000010`; last-pulse `t_rel≈0.497` |

[Train](Phase6/EXP_480_preinh250_tiprmin/Train) · [Test](Phase6/EXP_480_preinh250_tiprmin/Test) · [CSV](Phase6/EXP_480_preinh250_tiprmin/Test/SelectivityLog/results.csv)

### ltzcal twin gen

| Item | Value |
|------|-------|
| Train shell | [`RegressionFull480/EXP_baseline_gen`](../SelectivityLtzCalibrate/RegressionFull480/EXP_baseline_gen) + Model/Parameters from tiprmin |
| Test | **clone clean Test** tiprmin (не dirty inject) |
| GTS | 2000 (совпадает с tiprmin) |
| Gate | **7/8** selective — воспроизводит tiprmin |

[Train](Phase6/EXP_480_ltzcal_twin_gen/Train) · [Test](Phase6/EXP_480_ltzcal_twin_gen/Test) · [CSV](Phase6/EXP_480_ltzcal_twin_gen/Test/SelectivityLog/results.csv)

## Wave 2 — deferred

На ~480 мс нет pack B/C с разным foil MatrixData при том же ISI (в отличие от AsymRm). `SelectivityFastResponse/EXPD*` — вариации D/C мембраны, не foil-pack. Полный перенос «pack B/C clone→рецепт» **отложен**; не выдумывать span.

## Робастность @480 мс

| Ось | Итог |
|-----|------|
| Перенос процедуры | silent-probe mid-thr + hygiene → стабильный **7/8** last-pulse / ok_audit |
| TipR@Rmin | **не** ключевой рычаг @480 (0 ≡ 0b по fires) |
| 8/8 selective | **не достигнуто**: hardest foil (trial6) выше tgt по silent ltz |
| thr gap | узкий / отрицательный к hardest foil; согласуется с [`THR_FRAGILITY_DIAG`](../SelectivityAsymRm/THR_FRAGILITY_DIAG.md) (~6e-6 на эталоне) |
| twin | clean Test clone воспроизводит gen |

## Антирегрессия

- Не трогать AsymRm span25/50/100 PASS cold-reset.
- Исторические PhaseA / TimeNeuron / PSI — сохранены; Phase6 только клоны.
- Критерии `ok_audit` / acc≥4 в коде **не** менялись.

## PHASE9 P4 note

Clone `Phase6/EXP_480_gen_tiprmin_phase9_foil6`: silent foil6 ltz/soma > target → 8/8 unreachable by mid alone. See `EXP_480_gen_tiprmin_phase9_foil6/PHASE9_FOIL6_NOTE.md`. Parent 7/8 retained.

## PHASE10 T1 TipR Done retry

Clone `Phase6/EXP_480_gen_tiprmin_phase10_done_tipr`: TipR from thr_only (`~25.8e6…86e6`) + silent 0.05 mid. Foil6 ltz still ≥ target → gate **7/8** (fires `10000010`). See `PHASE10_FOIL6_TIPR_NOTE.md`. No pack B/C @480.

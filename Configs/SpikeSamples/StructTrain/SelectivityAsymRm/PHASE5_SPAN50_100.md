# PHASE5 — Span 50 / 100 ms recalculate (C1e9 recipe)

Recipe base from span25: C1e9, EstDelayPerSeg=0.002, Rmin=2e7, per-exp thr, last-pulse gate.
Gate: `ok_audit` + last-pulse `t_rel ≥ 0.8·pattern_end` + `ok_single`; prefer 8/8.

**Отличие от TipR base @25 мс:** на 50/100 TipR base (`8.6e7×4`) даёт **отрицательный** tgt−foil gap. Рабочий TipR: **`2e7 2e7 2e7 8.6e7`** (d0–d2 @ Rmin).

## Wave 0 — packA_gen @50 — **PASS** (2026-09-12)

| Item | Value |
|------|-------|
| Neuron | `NSPNeuronGenAsymRmD001C1e9` |
| L | `25 23 15 1` |
| EstDelayPerSeg | 0.002 |
| ResistanceMin | 2e7 |
| TipR | **`2e7 2e7 2e7 8.6e7`** |
| FixedLTZ | **0.011759** (mid silent-probe gap) |
| Test hygiene | clean Train→Test Parameters; MatrixClasses `1,0×7`; 4 tip Dataset connectors only |
| Gate | ok_audit=1, ok_strict, ok_single, selective, **8/8**; target `t_rel≈0.232` last-pulse; foils silent |

Notes: polluted Test Parameters (preinh tree / stale MatrixClasses) hid TipR effect and broke labels. After clean sync, TipR@Rmin flips gap positive (~3.3e-4).

## Wave 0b — packA_gen @100 — **PASS** (2026-09-12)

| Item | Value |
|------|-------|
| Neuron | `NSPNeuronGenAsymRmD001C1e9` |
| L | `52 48 27 1` |
| TipR / Rmin / EstDelay | same as @50 |
| FixedLTZ | **0.006681** |
| Gate | **8/8** selective last-pulse; target `t_rel≈0.533` |

Length train дошёл до L-band; amp-Done не ждали — TipR@Rmin + silent-probe thr + Test.

## Wave 1 — preinh + LtzCal twin — **PASS** (2026-09-12)

| EXP | thr | Gate |
|-----|-----|------|
| `EXP_span50ms_packA_preinh` | 0.011759 | 8/8 |
| `AsymRmLtzCal/EXP_span50ms_packA_gen` | 0.011759 | 8/8 (clone Test Model+Parameters) |
| `EXP_span100ms_packA_preinh` | 0.006681 | 8/8 |
| `AsymRmLtzCal/EXP_span100ms_packA_gen` | 0.006681 | 8/8 |

### Ловушки twin@100
- Twin `Project.ini` имел **GTS=10000** vs AsymRm **20000** → чинить GTS.
- `inject_analyzer.py` копирует **Train→Test**: Train с промежуточными Dataset connectors → fire_all. Для twin: **клонировать чистый Test эталона** (уже с analyzer), не inject из Train.
- NumSamples=1 в Model после dirty inject → чинить / не тащить Train.

## Wave 2 — packB_gen / packC_gen — **PASS** (2026-09-12)

MatrixData/InputPattern у A/B/C на одном span **идентичны**; исторический pack RC игнорируется → neuron **C1e9**, clone структуры с packA_gen + TipR@Rmin + per-exp mid-thr.

| EXP | L | FixedLTZ | Gate |
|-----|---|----------|------|
| `EXP_span50ms_packB_gen` | `25 23 15 1` | 0.011759 | 8/8 |
| `EXP_span50ms_packC_gen` | `25 23 15 1` | 0.011759 | 8/8 |
| `EXP_span100ms_packB_gen` | `52 48 27 1` | 0.006681 | 8/8 |
| `EXP_span100ms_packC_gen` | `52 48 27 1` | 0.006681 | 8/8 |

`grid_cells.tsv`: packB/C gen @50/100 → `NSPNeuronGenAsymRmD001C1e9`, cap=1e-9. Preinh B/C вне scope (после gen PASS — отложено).

## Робастность (по итогам waves 0–2)

Различаем три оси: **перенос рецепта**, **last-pulse timing**, **запас FixedLTZ**.

| Span | Физический gap `tgt_ltz − foil_max` | gap/thr | TipR | Запас thr |
|------|-------------------------------------|---------|------|-----------|
| 25 мс (эталон, TipR base) | ~1.5e-4 … 2.3e-4; окно thr ≥1.3e-4 | ~1.6–2.4% | base `8.6e7×4` | **хрупкий** (как до плана) |
| 50 мс (TipR@Rmin) | ~1.7e-4 (twin CSV до ~3.6e-4) | ~1.4% | `2e7×3+8.6e7` | **такой же хрупкий** по порядку |
| 100 мс (TipR@Rmin) | **~5e-6** | **~0.08%** | `2e7×3+8.6e7` | **на порядок хрупче** |

Метрики с gate-CSV эталонов: 50A gap=`1.665e-4` (tgt `0.011761` / foil_max `0.011594`); 100A gap=`5.33e-6` (tgt `0.006681` / foil `0.006676`). Mid-thr сидит почти у потолка окна (hi-margin ~0…2e-6).

### Что робастно
- **Last-pulse / ok_single 8/8** воспроизводится на 25/50/100 при C1e9 + EstDelay=0.002 + hygiene Test.
- **Между моделями обучения** на одном span (gen / Preinh2.5 / LtzCal twin / pack B·C после clone→C1e9): gaps и thr **совпадают** с эталоном packA — различия pack RC на этом уровне не видны (MatrixData одинаковая).
- Preinh @50/100 не потребовал отдельного thr (в отличие от span25, где thr≈0.0047 vs 0.0096).

### Что не робастно
- **Амплитудный порог** нигде не «широкий»: селективность держится на узком ltz-gap, не на tip-imbalance.
- @50 gap не стал лучше, чем @25 — лишь смена TipR (base→Rmin), чтобы gap был **положительным**.
- @100 hardest foil (trial2) почти равен target → окно thr фактически «лезвие»; любой шум/GTS/грязь connectors ломает PASS (это и вскрыл twin до GTS/clone-fix).

### Почему различия
1. **Длина кабеля / интеграция:** L~25→52 при том же EstDelay=0.002; foil-паттерны успевают нагнать target по ltz_max сильнее на 100 мс.
2. **TipR@Rmin** выравнивает crown timing, но **не расширяет** относительный amp-margin; на 100 абсолютный gap схлопывается.
3. **Модели обучения** после clone структуры не меняют физику gap — хрупкость thr **общая для span**, не для gen vs preinh vs twin.

Итог: проги **робастны как процедура/рецепт** (перенос на span и twin/pack), но **не робастны как FixedLTZ-маржа**; @100 хуже @25/50. Дальнейший запас — не «ещё mid-thr», а механизм, расширяющий tgt−foil (другая LTZ/нормализация/структура), либо явный thr-sweep с допуском.

## Антирегрессия

- Span25 PASS-конфиги не cold-reset.
- В реестр только last-pulse selective 8/8 (не fire_all / early `t_rel` / n≠8).
- Полная 18-EXP сетка (все preinh B/C и старые RC) — **не** автостарт этим планом.

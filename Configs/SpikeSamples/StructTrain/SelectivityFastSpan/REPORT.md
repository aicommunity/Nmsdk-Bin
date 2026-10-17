# SelectivityFastSpan — REPORT

Сжатые span **100 / 50 / 25 мс** с парой **(DissociationTC=0.002, Capacity=2.5e-10)** на Train и Test.  
Каталог: `Bin/Configs/SpikeSamples/StructTrain/SelectivityFastSpan/`.  
Мета: `grid_cells.tsv`, сводка: `grid_summary.csv`, лог: `run_fastspan_rerun.log`.

## Invalidation

Все прогоны FastSpan **до 2026-08-23** невалидны: `patch_pattern_scale.py` масштабировал паттерн in-place с floor 1.5 мс, фактический learner span был ~4–6 мс при метках 25/50/100 мс. Таблицы Acc/mode из тех прогонов не использовать.

## Протокол цели

Цель: trial0 (trained) → fire; trials 1–7 (distractors: reverse / permute / clusters / uniform) → silence. Gate: target_hit ∧ Acc≥4 ∧ ¬fire_all. Acc=1/8 + fp=7 = fire_all (порог слишком низкий или нет gap).

## Протокол

| Параметр | Значение |
|----------|----------|
| Эталон | `[0.01, 0.08, 0.16, 0.24]` с → α = T/0.48, scale из канона (идемпотентно) |
| Floor ISI | **0.5 мс** (`FLOOR_SEC=0.0005`) |
| Cold TipR / L | `86e6×4` / `1 1 1 1` |
| `ResistanceAdjustGain` | 0.4 |
| `Delay` (learner) | 1.5 |
| Train / Test | `-t 160 -S` / `-t 20` |
| Gate | target_hit + Acc≥4 + не fire_all |
| Verify | `verify_pattern_span.py` (16/16 PASS), `verify_element_params.py` (D/C) |

Setup: fresh `copy_config` из `TimeNeuronTimeLearner` / `TimeNeuronTimeLearnerTest` → `setup_fastspan.sh`.

## InputPattern после fix (verify PASS)

Learner span = sum(rows 1..3). Test MatrixData: 8 образцов с тем же span на sample.

| span T | InputPattern (с) | SyncTol | PeakMeasureMargin |
|--------|------------------|---------|-------------------|
| 100 мс | `0.00208, 0.01667, 0.03333, 0.05` | 0.00417 | 0.00583 |
| 50 мс | `0.00104, 0.00833, 0.01667, 0.025` | 0.00208 | 0.00292 |
| 25 мс | `0.00052, 0.00417, 0.00833, 0.0125` | 0.00104 | 0.002 |

## Классы нейронов

### `NSPNeuronGenD002C25e11` (fast / fast_ts10k)

Dissoc=0.002 с, Cap=2.5e-10, `UseElementDefaults=true`, Bio membrane/synapse.

### `NSPNeuronGenPreinh2_5D002C25e11` (preinh / preinh_ts10k)

Preinh k=2.5, Dissoc=0.002 с, Cap=2.5e-10, `UseElementDefaults=true`.

## Результаты (rerun 2026-08-23, valid patterns)

| EXP | NeuronClass | span | GlobalTS | FixedLTZ | Acc | mode | gate | L после Train |
|-----|-------------|------|----------|----------|-----|------|------|---------------|
| `EXP_span100ms_fast` | `NSPNeuronGenD002C25e11` | 100 | 2000 | 0.0115 | 1/8 | fire_all | FAIL | 23 19 13 1 |
| `EXP_span100ms_fast_preinh` | `…Preinh2_5D002C25e11` | 100 | 2000 | 0.0115 | 1/8 | fire_all | FAIL | 23 20 13 1 |
| `EXP_span50ms_fast` | `NSPNeuronGenD002C25e11` | 50 | 2000 | 0.0115 | 1/8 | fire_all | FAIL | 12 10 7 1 |
| `EXP_span50ms_fast_preinh` | `…Preinh2_5D002C25e11` | 50 | 2000 | 0.0115 | 1/8 | fire_all | FAIL | 12 10 7 1 |
| `EXP_span25ms_fast` | `NSPNeuronGenD002C25e11` | 25 | 2000 | 0.0115 | 1/8 | fire_all | FAIL | 7 6 4 1 |
| `EXP_span25ms_fast_preinh` | `…Preinh2_5D002C25e11` | 25 | 2000 | 0.0115 | 1/8 | fire_all | FAIL | 6 5 4 1 |
| `EXP_span25ms_fast_ts10k` | `NSPNeuronGenD002C25e11` | 25 | **10000** | **0.04** | 7/8 | silent | FAIL | 6 6 4 1 |
| `EXP_span25ms_fast_preinh_ts10k` | `…Preinh2_5D002C25e11` | 25 | **10000** | **0.04** | 7/8 | silent | FAIL | 7 6 4 1 |

При TS=2000: target_hit=1, fp=7 (fire_all) — селективность не достигнута, но паттерн и margins согласованы.  
При TS=10000: target не срабатывает (silent, target_hit=0) — порог 0.04 / dt=0.1 мс требует отдельной калибровки.

Контрольная группа паттернов: `SelectivityFastResponse` — аудит 2026-08-23, 9/9 EXP, span 480 мс OK.

## Вывод

После исправления масштабирования паттернов quality-gate селективности на span ≤100 мс при TS=2000 по-прежнему не достигается (fire_all). Это уже не артеfact broken pattern (~5 мс). Узкий EPSP (D=0.002, C=2.5e-10) необходим, но недостаточен для текущего learner+tip протокола на сжатых span.

## Команды

```bash
./scripts/setup_fastspan.sh
python3 scripts/verify_pattern_span.py --meta grid_cells.tsv EXP_*/Train/Parameters_00.xml EXP_*/Test/Parameters_00.xml
MAX_JOBS=4 ./scripts/run_fastspan.sh
```

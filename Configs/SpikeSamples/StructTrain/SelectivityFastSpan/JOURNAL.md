# Журнал SelectivityFastSpan

## 2026-08-23 — Pattern scale fix + valid rerun

### Проблема

`patch_pattern_scale.py` масштабировал ISI in-place с floor 1.5 ms без reset из эталона `[0.01, 0.08, 0.16, 0.24]`. Во всех 8 EXP фактический learner span был ~4–6 мс вместо заявленных 25/50/100 мс; margins (SyncTol, Peak) были рассчитаны под целевой span. Все предыдущие прогоны FastSpan — невалидны.

### Исправления

- `patch_pattern_scale.py`: идемпотентный scale из канона (Train + Test MatrixData 32 val), `FLOOR_SEC=0.0005`
- `setup_fastspan.sh`: `copy_config` → cold_patch → scale → `verify_pattern_span.py`; re-patch Watch (16 Interface)
- `run_fastspan.sh`: verify span до Train и после sync

### Прогон

MAX_JOBS=4, Train t=160, Test t=20. Verify pattern 16/16 PASS, verify D/C PASS.

| EXP | span | Acc | mode | gate |
|-----|------|-----|------|------|
| span100ms_fast[_preinh] | 100 | 1/8 | fire_all | FAIL |
| span50ms_fast[_preinh] | 50 | 1/8 | fire_all | FAIL |
| span25ms_fast[_preinh] | 25 | 1/8 | fire_all | FAIL |
| span25ms_*_ts10k | 25 | 7/8 | silent | FAIL |

Полная таблица: [`REPORT.md`](REPORT.md).

### Вывод

С корректными паттернами при TS=2000 селективность не достигнута (fire_all). ts10k: silent (target_hit=0) — отдельная задача калибровки LTZ. Следующие направления: алгоритм различения, Preinh k, tip R, не повторный TC-sweep без новой гипотезы.

## 2026-09-08 — Cleanup invalid pre-2026-08-23 artifacts + valid Test rerun

### Удалено (битый scale / misleading)

- Top-level: `run_fastspan.log`, `run_escalate_*.log`, `setup.log`, `setup_rerun.log`, `run_fastspan_rerun.log`, `grid_cells.tsv.all`, `*.bak_full`, `*.superseded`
- Все `Parameters_00.xml.bak`; все `EventsLog/`
- `StatisticLog` с датой **&lt; 2026.08.23** (266 dirs)
- Stale `Test/SelectivityLog/results.csv` (часть с ISI `0.0015` от 22 авг)

### Не удалялось

- Каталоги `EXP_*`, валидные Models/Parameters после fix 23 авг
- `REPORT.md`, `grid_cells.tsv`, актуальный `patch_pattern_scale.py`

### Прогон

`SKIP_TRAIN=1` добавлен в `run_fastspan.sh`. Команда:

```bash
MAX_JOBS=4 TEST_T=20 SKIP_TRAIN=1 bash scripts/run_fastspan.sh
```

Лог: `run_fastspan_valid_test.log`. Verify pattern 16/16 PASS. Результат совпал с каноном 23 авг: TS=2000 → fire_all 1/8; ts10k → silent 7/8. CSV с валидными ISI (не 0.0015).

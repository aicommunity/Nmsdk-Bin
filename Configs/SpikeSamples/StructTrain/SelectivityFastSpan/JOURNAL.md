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

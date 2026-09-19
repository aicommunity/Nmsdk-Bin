# REPRO_COLD_RESULT

> **RU:** [`REPRO_COLD_RESULT.ru.md`](REPRO_COLD_RESULT.ru.md)

Generated: 2026-09-16T11:22:48Z

Cold Train harness (soft-cold default; TipR cold→@Rmin; Need=0; mid gate).

| family | role | L | TipR | thr | fires | acc | mode | ok_audit | last_pulse | Need |
|--------|------|---|------|-----|-------|-----|------|----------|------------|------|
| fastspan | gold | `6 5 4 1` | `20000000 20000000 20000000 86000000` | 0.0328372 | `10000000` | 8 | selective | 1 | 1 | 0 |
| fastspan | r1 | `7 5 4 1` | `20000000 20000000 20000000 86000000` | 0.1034165 | `11110101` | 3 | partial_FA | 0 | 1 | 1 |
| fastspan | r2 | `7 5 4 1` | `20000000 20000000 20000000 86000000` | 0.1034165 | `11110101` | 3 | partial_FA | 0 | 1 | 1 |
| branch | gold | `13 11 7 1` | `20000000 20000000 20000000 86000000` | 0.07179975 | `10000000` | 8 | selective | 1 | 1 | 0 |
| branch | r1 | `13 11 7 1` | `20000000 20000000 20000000 86000000` | 0.07179975 | `10000000` | 8 | selective | 1 | 1 | 0 |
| branch | r2 | `13 11 7 1` | `20000000 20000000 20000000 86000000` | 0.07179975 | `10000000` | 8 | selective | 1 | 1 | 0 |

## Verdicts

- **fastspan**: `REPRO_FAIL`
- **branch**: `REPRO_OK_EXACT`

## Criteria

- `REPRO_OK_QUALITY` — r1≡r2, ok_audit=1, acc≥8 (fires/L vs gold optional)
- `REPRO_OK_EXACT` — QUALITY + fires==gold + L==gold
- `REPRO_OK` / `REPRO_SOFT` — legacy exact/soft fires match
- `REPRO_FAIL` — ok_audit=0 or (legacy) fires≠gold without QUALITY
- `NONDET` — r1 vs r2 disagree on fires or L


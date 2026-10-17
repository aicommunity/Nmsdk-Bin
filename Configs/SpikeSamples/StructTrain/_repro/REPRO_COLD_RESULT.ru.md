# REPRO_COLD_RESULT — RU

**EN:** [`REPRO_COLD_RESULT.md`](REPRO_COLD_RESULT.md)

Сгенерировано: 2026-09-16T11:22:48Z

Harness Cold Train (soft-cold по умолчанию; TipR cold→@Rmin; Need=0; mid gate).

| family | role | L | TipR | thr | fires | acc | mode | ok_audit | last_pulse | Need |
|--------|------|---|------|-----|-------|-----|------|----------|------------|------|
| fastspan | gold | `6 5 4 1` | tiprmin | 0.0328372 | `10000000` | 8 | selective | 1 | 1 | 0 |
| fastspan | r1/r2 | `7 5 4 1` | tiprmin | 0.1034165 | `11110101` | 3 | partial_FA | 0 | 1 | 1 |
| branch | gold/r1/r2 | `13 11 7 1` | tiprmin | 0.07179975 | `10000000` | 8 | selective | 1 | 1 | 0 |

## Вердикты
- **fastspan:** `REPRO_FAIL` (Need≠0; L 7↔6 dend0)
- **branch:** `REPRO_OK_EXACT`

Дальнейший разбор: [`REPRO_COLD_INVESTIGATION.md`](REPRO_COLD_INVESTIGATION.md). PHASE12: Branch VALIDATED; FS → FAIL_ROOTCAUSE / proposals.

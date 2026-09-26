# GoldTest retest NOT_RETESTED — 2026-09-25

Console SHA-256: `4917a2bcbac318d160ca8b596452d3986ccc9978172d35a1b554d65b5a27c843`  
PulseLib: `8d429e7` · Bin: `1a664a2`

## Метод

- Манифест: [`NOT_RETESTED_manifest_20260925.txt`](NOT_RETESTED_manifest_20260925.txt)
- Runner: `scripts/gold_retest_batch.py` (span-aware `test_sim_t`, CSV≥8 SIGTERM)
- Сводка: [`GOLD_RETEST_MERGED_20260925.csv`](GOLD_RETEST_MERGED_20260925.csv)
- Gate CSV: `../AUDIT_GATE_RECOMPUTE.csv`

## Итог

| | N |
|--|--:|
| Прогнано (merged) | 102 |
| PASS | 101 |
| FAIL | 1 (`Phase6/EXP_480_ltzcal_twin_gen`) |
| OUT (не гоняли) | 4 |

GoldTest строк NOT_RETESTED в основных §1–7 и ok_audit — закрыты. SoftCold — отдельная волна C (`SOFTCOLD_C_*.log` / `SOFTCOLD_C_rcs.txt`).

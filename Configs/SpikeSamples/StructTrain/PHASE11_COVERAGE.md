# PHASE11 — re-audit coverage journal

Повторный аудит TimeLearner + Branch после PHASE10. Критерии кода **не** меняются (`ok_audit`).  
Предшественники: [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md), [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md). Рецепты: [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md).

## Волны

| ID | Содержание | Статус |
|----|------------|--------|
| RD | Pack StatisticLog ≥200M; Avail≥80G gate | **done** 3/3 |
| R0 | AUDIT_MATRIX + GATE archive + docs | **done** 168 EXP / 167 GATE / 77 ok_audit |
| R1 | n=8 hygiene + foil6 CSV | pending |
| R2.1 | Branch NextSeg pack B/C ×6 | pending |
| R2.2 | PSI short C1e9 cold Train ×3 | pending |
| R2.3 | FastSpan span50 gen fix | pending |
| R2.4 | br480 preinh retrain (optional) | pending |
| R3 | foil6/FR/stall closure docs | pending |
| R4 | defer catalog | pending |

## Disk (RD)

| wave | Avail_before | Avail_after | note |
|------|-------------:|------------:|------|
| RD start | 301G | — | StructTrain ~40G |
| RD pack `statisticlog_20260915T074209Z` | 301G | 302G | LtzCal twin Test StatisticLog ×3 ≥200M ok |

Script: [`scripts/pack_statistic_logs.py`](scripts/pack_statistic_logs.py).  
Archive: [`archives/statisticlog_20260915T074209Z/`](archives/statisticlog_20260915T074209Z/).  
S0 prior: [`archives/statisticlog_20260914T161650Z/`](archives/statisticlog_20260914T161650Z/).

**Gates:** Avail &lt; 80G → STOP Train; &lt; 50G → HARD STOP. Pack after each Train. One NM at a time.

## Анти-регрессия

Не cold-reset PASS parents (Branch tiprmin / packA–C C1e9, AsymRm, Phase6 7/8, AsymRmLtzCalBranch stall). Не менять `ok_audit`.

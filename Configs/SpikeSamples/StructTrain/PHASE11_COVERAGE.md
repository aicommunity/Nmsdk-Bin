# PHASE11 — re-audit coverage journal

Повторный аудит TimeLearner + Branch после PHASE10. Критерии кода **не** меняются (`ok_audit`).  
Предшественники: [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md), [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md). Рецепты: [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md).

## Волны

| ID | Содержание | Статус |
|----|------------|--------|
| RD | Pack StatisticLog ≥200M; Avail≥80G gate | **done** 3/3 |
| R0 | AUDIT_MATRIX + GATE archive + docs | **done** 168 EXP / 167 GATE / 77 ok_audit |
| R1 | n=8 hygiene + foil6 CSV | **done** 20 Test + foil6 CSV; GATE 168 / 97 ok_audit |
| R2.1 | Branch NextSeg pack B/C ×6 | **done** 6/6 8/8 selective last-pulse |
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
| R1 after gates | 302G | — | PSI/PhaseA/FR/foil6 Test reruns |
| R1 pack `statisticlog_20260915T082250Z` | 302G | 306G | 35× StatisticLog ≥100M ok; StructTrain ~35G |

Script: [`scripts/pack_statistic_logs.py`](scripts/pack_statistic_logs.py).  
Archives: [`archives/statisticlog_20260915T074209Z/`](archives/statisticlog_20260915T074209Z/) (RD), [`archives/statisticlog_20260915T082250Z/`](archives/statisticlog_20260915T082250Z/) (R1).  
S0 prior: [`archives/statisticlog_20260914T161650Z/`](archives/statisticlog_20260914T161650Z/).

### R1 notes

- PSI k-sweep EXP00/02–13 (+margprops/recheck): all n=8; still partial_FA/selective (not recipe PASS).
- PhaseA EXP04/05: n=8.
- FastResponse `EXPD002C1e9`: n=8 silent (ok_audit=0) — TipR-only FAIL kept for R3.
- foil6 clone: CSV present; 7/8 selective thr≈0.016894; foil6 unreachable — see [`PHASE9_FOIL6_NOTE.md`](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase9_foil6/PHASE9_FOIL6_NOTE.md).

**Gates:** Avail &lt; 80G → STOP Train; &lt; 50G → HARD STOP. Pack after each Train. One NM at a time.

## Анти-регрессия

Не cold-reset PASS parents (Branch tiprmin / packA–C C1e9, AsymRm, Phase6 7/8, AsymRmLtzCalBranch stall). Не менять `ok_audit`.

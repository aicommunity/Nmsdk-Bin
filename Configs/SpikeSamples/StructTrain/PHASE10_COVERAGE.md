# PHASE10 — coverage journal

Журнал после PHASE9 tails. Критерии кода **не** меняются (`ok_audit`).  
Предшественник: [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md). Рецепты: [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md).

## Волны

| ID | Содержание | Статус |
|----|------------|--------|
| S0 | Pack StatisticLog/EventsLog ≥200M → `archives/statisticlog_*` | **done** 111/111 |
| T0 | GATE metrics rebuild (+P1–P3 C1e9) | pending |
| T1 | P4b TipR Done/partial (br480 + Phase6 foil6) | pending |
| T2 | AsymRmLtzCal packA_preinh ×3 Test hygiene | pending |
| P10.1 | PSI short preinh250 → `*_C1e9` TipR@Rmin | pending |
| P10.2 | FastSpan short → `*_C1e9` / `*_preinh_C1e9` | pending |
| P10.3 | FastResponse D001/D002 C1e9 tiprmin copies | pending |
| P10.4 | PhaseA03–05 / LtzCal Fast — docs skip | pending |

## S0 disk prep

- Script: [`scripts/pack_statistic_logs.py`](scripts/pack_statistic_logs.py)
- Archive: [`archives/statisticlog_20260914T161650Z/`](archives/statisticlog_20260914T161650Z/) (MANIFEST 111 ok)
- Avail `/`: **142G → 308G**; StructTrain **201G → 35G**
- SelectivityLog / ltz_sweep **not** packed
- Pointer: [`archives/README.md`](archives/README.md)

## Анти-регрессия

Не cold-reset / overwrite PASS parents (Branch tiprmin / packA–C C1e9, AsymRm gen+preinh C1e9, Phase6 7/8, AsymRmLtzCalBranch stall).

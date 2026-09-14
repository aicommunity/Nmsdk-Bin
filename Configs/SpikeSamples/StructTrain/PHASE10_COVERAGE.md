# PHASE10 — coverage journal

Журнал после PHASE9 tails. Критерии кода **не** меняются (`ok_audit`).  
Предшественник: [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md). Рецепты: [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md).

## Волны

| ID | Содержание | Статус |
|----|------------|--------|
| S0 | Pack StatisticLog/EventsLog ≥200M → `archives/statisticlog_*` | **done** 111/111 |
| T0 | GATE metrics rebuild (+P1–P3 C1e9) | **done** 154/64 |
| T1 | P4b TipR Done/partial (br480 + Phase6 foil6) | **done** (both FAIL 8/8; parents 7/8 keep) |
| T2 | AsymRmLtzCal packA_preinh ×3 Test hygiene | **3/3 PASS** 8/8 |
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

## T1 TipR retries

| Clone | Mode | Result |
|-------|------|--------|
| `SelectivityBranch/EXP_br480_preinh250_tiprmin_phase10_tipr` | done → partial | `ok_audit=0` per_stim; parent 7/8 keep |
| `SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase10_done_tipr` | TipR thr_only | foil6≥tgt; gate 7/8; no 8/8 |

## T2 AsymRmLtzCal preinh twins

Test refreshed from AsymRm `packA_preinh` (Train stall untouched). TipR: @25 base×4; @50/100 TipR@Rmin.

| EXP | Status | thr |
|-----|--------|-----|
| `AsymRmLtzCal/EXP_span25ms_packA_preinh` | **PASS** 8/8 | 0.004686425 |
| `…/EXP_span50ms_packA_preinh` | **PASS** 8/8 | 0.011759 |
| `…/EXP_span100ms_packA_preinh` | **PASS** 8/8 | 0.006681015 |

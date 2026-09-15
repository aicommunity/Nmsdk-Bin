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
| R2.2 | PSI short C1e9 cold Train ×3 | **done** 25:acc5 · 50:acc4 · 100:acc6; none ≥7 SUCCESSFUL |
| R2.3 | FastSpan span50 gen fix | **done** thr+cold fail; restored P10 partial_FA; pack `statisticlog_20260915T103702Z` |
| R2.4 | br480 preinh retrain (optional) | **skipped** Avail ok but parent 7/8 keep; disk budget after PSI×3 |
| R3 | foil6/FR/stall closure docs | **done** `PHASE11_FOIL6_CLOSURE` + RECIPE |
| R4 | defer catalog | **done** RECIPE §PHASE11 defer |

## Disk (RD)

| wave | Avail_before | Avail_after | note |
|------|-------------:|------------:|------|
| RD start | 301G | — | StructTrain ~40G |
| RD pack `statisticlog_20260915T074209Z` | 301G | 302G | LtzCal twin Test StatisticLog ×3 ≥200M ok |
| R1 after gates | 302G | — | PSI/PhaseA/FR/foil6 Test reruns |
| R1 pack `statisticlog_20260915T082250Z` | 302G | 306G | 35× StatisticLog ≥100M ok; StructTrain ~35G |

Script: [`scripts/pack_statistic_logs.py`](scripts/pack_statistic_logs.py).  
Archives: [`archives/statisticlog_20260915T074209Z/`](archives/statisticlog_20260915T074209Z/) (RD), [`archives/statisticlog_20260915T082250Z/`](archives/statisticlog_20260915T082250Z/) (R1), [`archives/statisticlog_20260915T103702Z/`](archives/statisticlog_20260915T103702Z/) (R2.3).  
S0 prior: [`archives/statisticlog_20260914T161650Z/`](archives/statisticlog_20260914T161650Z/).

### R1 notes

- PSI k-sweep EXP00/02–13 (+margprops/recheck): all n=8; still partial_FA/selective (not recipe PASS).
- PhaseA EXP04/05: n=8.
- FastResponse `EXPD002C1e9`: n=8 silent (ok_audit=0) — TipR-only FAIL kept for R3.
- foil6 clone: CSV present; 7/8 selective thr≈0.016894; foil6 unreachable — see [`PHASE11_FOIL6_CLOSURE.md`](SelectivityPhaseA/Phase6/PHASE11_FOIL6_CLOSURE.md).

**Gates:** Avail &lt; 80G → STOP Train; &lt; 50G → HARD STOP. Pack after each Train. One NM at a time.

## Анти-регрессия

Не cold-reset PASS parents (Branch tiprmin / packA–C C1e9, AsymRm, Phase6 7/8, AsymRmLtzCalBranch stall). Не менять `ok_audit`.

### R2.3 FastSpan span50 gen

Thr re-mid: still acc5. Cold Train: amp inversion → acc2 `ok_audit=0`. Restored PHASE10 XML/CSV (acc5 `ok_audit=1`). Sibling preinh 8/8 kept. Disk: pack after Train Avail 300G→303G.

### R3 closure

- foil6: [`PHASE11_FOIL6_CLOSURE.md`](SelectivityPhaseA/Phase6/PHASE11_FOIL6_CLOSURE.md)
- FastResponse: TipR-only FAIL; AsymRm scaffold out of scope
- LtzCalBranch / FastSpanLtzCal: `wontfix` (superseded PHASE8/P10.2)
- Branch trio: demoted эталон — no cold-reset

### R4 defer

See [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md) §PHASE11 defer catalog.

### Follow-up: identical cold repro

Harness: [`_repro/README.md`](_repro/README.md) · result [`_repro/REPRO_COLD_RESULT.md`](_repro/REPRO_COLD_RESULT.md).

Clean tip-1 cold ×2 (FastSpan25 `-t`160, Branch25 `-t`320) → TipR@Rmin + mid. **r1≡r2** (deterministic); neither family matches gold fires → `REPRO_FAIL` (not `NONDET`). FS L=`7 5 4 1` vs gold `6 5 4 1`; Branch L matches gold, fires `10010000` vs gold `10000000`.

### R2.2 PSI short C1e9 cold

| span | L after | thr | acc | note |
|-----:|---------|-----|----:|------|
| 25 | 6 5 3 1 | ≈0.1246 | 5 | partial_FA |
| 50 | (cold) | ≈0.0296 | 4 | partial_FA |
| 100 | 21 18 12 1 | ≈0.0182 | 6 | selective |

Packs: `statisticlog_20260915T125643Z`, `…T141845Z`, `…T153249Z`. Avail finish ~301G. No SUCCESSFUL (need ≥7).

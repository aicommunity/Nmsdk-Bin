# PHASE11 — foil6 @480 closure

Clone: [`EXP_480_gen_tiprmin_phase9_foil6`](EXP_480_gen_tiprmin_phase9_foil6/).  
Parent PASS: [`EXP_480_gen_tiprmin`](EXP_480_gen_tiprmin/) — 7/8 selective, FP trial6, fires=`10000010`.

## Finding

Silent mid (`ltz_potential_max`, thr≈0.05 probe then mid≈0.016894):

| trial | role | ltz_potential_max |
|------:|------|------------------:|
| 0 | target | 0.0173325 |
| 6 | foil | **0.0182371** |

**foil6 > target** — amplitude inversion. Mid-thr alone cannot reach 8/8 without foil-matrix change.

## PHASE11 R1

Gate CSV complete (n=8): thr≈0.0168941, fires=`10000010`, acc=7/8, last-pulse ok. Audit gap closed (no missing CSV among live EXP).

## Closure

| Item | Status |
|------|--------|
| 8/8 @480 gen tiprmin | **unreachable** via thr-only (foil6) |
| Pack B/C @480 | **deferred** (no Matrix packs for Phase6) |
| Parent `EXP_480_gen_tiprmin` | **keep** PASS 7/8 |
| Clone foil6 | diagnostic only; RECIPE Partial |

See also: [`PHASE9_FOIL6_NOTE.md`](EXP_480_gen_tiprmin_phase9_foil6/PHASE9_FOIL6_NOTE.md), [`PHASE6_480_RECIPE.md`](../PHASE6_480_RECIPE.md).

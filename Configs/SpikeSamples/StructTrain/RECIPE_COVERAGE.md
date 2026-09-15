# Recipe coverage — TipR@Rmin + C1e9 + silent mid-thr

Рецепт = `TipSynapseResistance` TipR@Rmin `2e7 2e7 2e7 8.6e7` + `ResistanceMin=2e7` + silent mid-thr + clean Test.  
Для short-span дополнительно **C1e9** neuron + cold Train (Test-only tiprmin на Branch short-span — FAIL).

Критерии кода не меняются — [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md) §«Слои ворот».  
Журнал PHASE9: [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md). Журнал PHASE10: [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md). Журнал PHASE11: [`PHASE11_COVERAGE.md`](PHASE11_COVERAGE.md). GATE: 2026-09-15 · 168 Test · 97 `ok_audit=1` (PHASE11 R1). MATRIX: [`AUDIT_MATRIX_20260915.csv`](AUDIT_MATRIX_20260915.csv).

## Covered

| Семья | Конфиги | Журнал |
|-------|---------|--------|
| AsymRm A gen+preinh, B/C gen @25/50/100 | `SelectivityAsymRm/EXP_span{25,50,100}ms_pack{A,B,C}_gen` (+ A_preinh) | [`PHASE5_SPAN50_100.md`](SelectivityAsymRm/PHASE5_SPAN50_100.md) |
| AsymRm pack B/C preinh C1e9 @25/50/100 | `SelectivityAsymRm/EXP_span*_pack{B,C}_preinh_C1e9` (old FAIL kept) | [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) P2 **6/6 PASS** |
| AsymRmLtzCal twin gen @25/50/100 | `SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span*_packA_gen` | PHASE5 Wave1 |
| AsymRmLtzCal twin preinh @25/50/100 | `AsymRmLtzCal/EXP_span*_packA_preinh` | [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md) T2 **3/3 PASS** |
| Branch @480 tiprmin / nextseginh | `SelectivityBranch/EXP_br480_tiprmin`, `…_nextseginh_tiprmin` | [`PHASE7_BRANCH_QUALITY.md`](SelectivityBranch/PHASE7_BRANCH_QUALITY.md) |
| Branch short-span packA gen+preinh @25/50/100 | `SelectivityBranch/EXP_br_span{25,50,100}_packA_{gen,preinh}_C1e9` | [`PHASE8_SHORTSPAN.md`](SelectivityBranch/PHASE8_SHORTSPAN.md) (span100 gen: Done TipR fallback) |
| Branch short-span pack B/C gen+preinh @25/50/100 | `SelectivityBranch/EXP_br_span{25,50,100}_pack{B,C}_{gen,preinh}_C1e9` | [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) P1 **12/12 PASS** |
| Branch NextSegInh short packA @25/50/100 | `SelectivityBranch/EXP_br_span*_packA_nextseginh_C1e9` | [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) P3 **3/3 PASS** |
| Branch NextSegInh short pack B/C @25/50/100 | `SelectivityBranch/EXP_br_span*_pack{B,C}_nextseginh_C1e9` | [`PHASE11_COVERAGE.md`](PHASE11_COVERAGE.md) R2.1 **6/6 PASS** |
| FastSpan short C1e9 gen+preinh @25/50/100 | `SelectivityFastSpan/EXP_span*_fast_C1e9` (+ `_preinh_C1e9`) | [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md) P10.2 (4×8/8 + 7/8; span50 gen partial) |
| PSI short preinh250 C1e9 | `SelectivityPresynapticInhib/EXP_span*_preinh250_C1e9` | P10.1 `ok_audit` partial_FA |

## Partial

| Семья | Acc | Конфиг | Пробел |
|-------|-----|--------|--------|
| Phase6 TimeLearner @480 | 7/8 | `SelectivityPhaseA/Phase6/EXP_480_*` | foil trial6; pack B/C deferred — [`PHASE6_480_RECIPE.md`](SelectivityPhaseA/PHASE6_480_RECIPE.md) · PHASE9 P4 |
| Branch preinh250 tiprmin | 7/8 | `SelectivityBranch/EXP_br480_preinh250_tiprmin` | 1 FP (trial4) · PHASE9 P4 |
| FastSpan span50 gen C1e9 | 5/8 | `EXP_span50ms_fast_C1e9` | PHASE11 R2.3 thr+cold fail (amp inversion); restored P10 partial; sibling preinh PASS |
| PSI short C1e9 | 4–6/8 | `EXP_span*_preinh250_C1e9` | cold Train → PHASE11 R2.2 |

## Gap (PHASE11 execution)

| Тема | Путь | Статус |
|------|------|--------|
| Phase6 foil trial6 / br480 FP | quality clones | TipR Done/partial — still 7/8 |
| FastResponse tiprmin | `EXPD00{1,2}C1e9_phase10_tiprmin` | P10.3 silent / fire_all |

## Orphans PHASE10+ (catalog / residual)

| Семья | Пути | Почему | Действие |
|-------|------|--------|----------|
| AsymRmLtzCalBranch ×6 | `SelectivityLtzCalibrate/AsymRmLtzCalBranch/EXP_*` | NeedTrain=1, C25e12 stall | Не overwrite; PHASE8 packA = замена |
| Branch канон trio | `TimeNeuronTimeLearnerBranch*` | demoted эталон | Не cold-reset |
| PSI k-sweep / long span | `EXP00`–`15`, `EXP30`–`35`, autothr | вне P10.1 | catalog only |
| FastResponse D/C grid | non-C1e9 cells | вне P10.3 | catalog only |
| PhaseA EXP03–05 | sync/gain | no foil invent | P10.4 docs skip |

Тренер: `NNeuronTimeLearner`. Рецепт C1e9+TipR@Rmin **не** применялся на orphans ниже. Срез: [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv).

### PSI (~38 EXP roots)

| Группа | EXP | GATE (кратко) |
|--------|-----|----------------|
| k-sweep @~480 | `EXP00_baseline*` | n=7, ~3–4/8 |
| | `EXP01_preinh_050` | **ok_audit=1** 4/8 (реестр) |
| | `EXP01…_autothr` / `EXP02…_autothr` / `EXP03…_autothr` | fire_all |
| | `EXP02_preinh_100` … `EXP09_preinh_1000` | n=7, ~3–5/8 |
| | `EXP10…`–`EXP13…` mid-k | n=7, 4–5/8 |
| | `EXP14_preinh_260`, `EXP15_preinh_270` | **ok_audit=1** (реестр) |
| Span × baseline\|preinh250 | `EXP20`–`EXP27` (10–100 мс) | fire_all / partial |
| | `EXP21`, `EXP31`–`EXP35` | часть в реестре |
| | `EXP30`–`EXP35` (200–400 мс) | 3–5/8; часть ok_audit |

Нейроны: `NSPNeuronGen` / `NSPNeuronGenPreinh{k}` — **не** AsymRm C1e9.  
**PHASE10.1 done:** `EXP_span{25,50,100}ms_preinh250_C1e9` — TipR@Rmin+mid; `ok_audit=1` partial_FA (не 8/8). Cold Train deferred.

### FastSpan (parents + C1e9)

| EXP | GATE |
|-----|------|
| `EXP_span{25,50,100}ms_fast` (+ `_preinh`) parents | fire_all (kept) |
| `EXP_span*_fast_C1e9` / `*_preinh_C1e9` | **P10.2** TipR@Rmin — 4×8/8, 1×7/8, 1× partial_FA |
| `EXP_span25ms_fast_ts10k` (+ `_preinh_ts10k`) | silent acc7 (skip) |

### FastResponse

| EXP | GATE |
|-----|------|
| `EXP00CtrlExp04`, `EXPD00{1,2,5}C25e11`, `…C5e10` | fire_all |
| `EXPD001C1e9` / `EXPD002C1e9` parents | silent / incomplete |
| `EXPD00{1,2}C1e9_phase10_tiprmin` | **P10.3** silent / fire_all |

### PhaseA EXP03–05 (3)

| EXP | GATE |
|-----|------|
| `EXP03_sync_tolerance_015` | fail / n≠8 — P10.4 skip |
| `EXP04_sync_tolerance_010` | fail / n≠8 — P10.4 skip |
| `EXP05_resistance_gain_025` | fail / n≠8 — P10.4 skip |

### LtzCal Fast / BranchFastSpan

`SelectivityLtzCalibrate/FastSpanLtzCal`, `BranchFastSpan` — superseded PHASE8 / P10.2.

## Вне scope

- `UProperty EstDelayPerSeg` для Branch (отдельный PulseLib PR).
- Полный retrain orphans — только PHASE10+.

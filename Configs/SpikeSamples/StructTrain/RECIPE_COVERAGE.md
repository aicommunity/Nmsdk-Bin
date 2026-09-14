# Recipe coverage — TipR@Rmin + C1e9 + silent mid-thr

Рецепт = `TipSynapseResistance` TipR@Rmin `2e7 2e7 2e7 8.6e7` + `ResistanceMin=2e7` + silent mid-thr + clean Test.  
Для short-span дополнительно **C1e9** neuron + cold Train (Test-only tiprmin на Branch short-span — FAIL).

Критерии кода не меняются — [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md) §«Слои ворот».  
Журнал PHASE9: [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md). GATE D0: 2026-09-14 · 132 Test · 43 `ok_audit=1`.

## Covered

| Семья | Конфиги | Журнал |
|-------|---------|--------|
| AsymRm A gen+preinh, B/C gen @25/50/100 | `SelectivityAsymRm/EXP_span{25,50,100}ms_pack{A,B,C}_gen` (+ A_preinh) | [`PHASE5_SPAN50_100.md`](SelectivityAsymRm/PHASE5_SPAN50_100.md) |
| AsymRm pack B/C preinh C1e9 @25/50/100 | `SelectivityAsymRm/EXP_span*_pack{B,C}_preinh_C1e9` (old FAIL kept) | [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) P2 **6/6 PASS** |
| AsymRmLtzCal twin gen @25/50/100 | `SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span*_packA_gen` | PHASE5 Wave1 |
| Branch @480 tiprmin / nextseginh | `SelectivityBranch/EXP_br480_tiprmin`, `…_nextseginh_tiprmin` | [`PHASE7_BRANCH_QUALITY.md`](SelectivityBranch/PHASE7_BRANCH_QUALITY.md) |
| Branch short-span packA gen+preinh @25/50/100 | `SelectivityBranch/EXP_br_span{25,50,100}_packA_{gen,preinh}_C1e9` | [`PHASE8_SHORTSPAN.md`](SelectivityBranch/PHASE8_SHORTSPAN.md) (span100 gen: Done TipR fallback) |
| Branch short-span pack B/C gen+preinh @25/50/100 | `SelectivityBranch/EXP_br_span{25,50,100}_pack{B,C}_{gen,preinh}_C1e9` | [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) P1 **12/12 PASS** |
| Branch NextSegInh short packA @25/50/100 | `SelectivityBranch/EXP_br_span*_packA_nextseginh_C1e9` | [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) P3 **3/3 PASS** |

## Partial

| Семья | Acc | Конфиг | Пробел |
|-------|-----|--------|--------|
| Phase6 TimeLearner @480 | 7/8 | `SelectivityPhaseA/Phase6/EXP_480_*` | foil trial6; pack B/C deferred — [`PHASE6_480_RECIPE.md`](SelectivityPhaseA/PHASE6_480_RECIPE.md) · PHASE9 P4 |
| Branch preinh250 tiprmin | 7/8 | `SelectivityBranch/EXP_br480_preinh250_tiprmin` | 1 FP (trial4) · PHASE9 P4 |

## Gap (PHASE9 execution targets)

| Семья | Пути | Почему | Действие |
|-------|------|--------|----------|
| AsymRmLtzCalBranch ×6 | `SelectivityLtzCalibrate/AsymRmLtzCalBranch/EXP_*` | NeedTrain=1, C25e12 stall | Не overwrite; PHASE8 packA = замена |
| AsymRmLtzCal preinh twins | `AsymRmLtzCal/EXP_*_preinh` | silent / n≠8 | **explicit defer** PHASE9 P4 (no overwrite) |
| Branch канон trio | `TimeNeuronTimeLearnerBranch*` | demoted эталон | Не cold-reset |

## Orphans PHASE10+ (catalog only — no Train/gate in PHASE9)

Тренер: `NNeuronTimeLearner`. Рецепт C1e9+TipR@Rmin **не** применялся. Срез: [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv).

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
**PHASE10 start:** `preinh250` @25/50/100 → новые `*_C1e9` + TipR@Rmin + mid (не весь k-sweep).

### FastSpan (8)

| EXP | GATE |
|-----|------|
| `EXP_span{25,50,100}ms_fast` (+ `_preinh`) | fire_all |
| `EXP_span25ms_fast_ts10k` (+ `_preinh_ts10k`) | silent acc7 |

Neuron `D002C25e11` / Preinh2_5 same.

### FastResponse (9)

| EXP | GATE |
|-----|------|
| `EXP00CtrlExp04`, `EXPD00{1,2,5}C25e11`, `…C5e10` | fire_all |
| `EXPD001C1e9` | silent |
| `EXPD002C1e9` | silent n=7 |

### PhaseA EXP03–05 (3)

| EXP | GATE |
|-----|------|
| `EXP03_sync_tolerance_015` | fail / n≠8 |
| `EXP04_sync_tolerance_010` | fail / n≠8 |
| `EXP05_resistance_gain_025` | fail / n≠8 |

### LtzCal Fast / BranchFastSpan

`SelectivityLtzCalibrate/FastSpanLtzCal`, `BranchFastSpan` — templates / stall; Branch short superseded by PHASE8.

## Вне scope

- `UProperty EstDelayPerSeg` для Branch (отдельный PulseLib PR).
- Полный retrain orphans — только PHASE10+.

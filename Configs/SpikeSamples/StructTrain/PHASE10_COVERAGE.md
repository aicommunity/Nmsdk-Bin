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
| P10.1 | PSI short preinh250 → `*_C1e9` TipR@Rmin | **3/3 ok_audit** (partial_FA 4–6/8; no cold Train) |
| P10.2 | FastSpan short → `*_C1e9` / `*_preinh_C1e9` | **done** 6/6 `ok_audit` (4×8/8) |
| P10.3 | FastResponse D001/D002 C1e9 tiprmin copies | **done** 0/2 PASS (silent / fire_all) |
| P10.4 | PhaseA03–05 / LtzCal Fast — docs skip | **done** (docs) |

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

## P10.1 PSI short preinh250 C1e9

Neuron kept `NSPNeuronGenPreinh2_5`. TipR@Rmin + GTS=20000 + silent mid (no cold Train; gap>0).

| EXP | Status | thr | fires |
|-----|--------|-----|-------|
| `EXP_span25ms_preinh250_C1e9` | ok_audit=1 acc5 | 0.03457115 | `11110000` |
| `EXP_span50ms_preinh250_C1e9` | ok_audit=1 acc4 | 0.02956455 | `11110001` |
| `EXP_span100ms_preinh250_C1e9` | ok_audit=1 acc6 | 0.0181721 | `10100001` |

Not added to SUCCESSFUL (partial_FA / not ≥7 selective). Cold Train deferred (gap>0 trigger not met).

## P10.2 FastSpan short C1e9

Cold Train → TipR@Rmin + silent mid (`ltz`). Neuron: gen `NSPNeuronGenAsymRmD001C1e9` / preinh `NSPNeuronGenPreinh2_5AsymRmD001C1e9`. GTS=20000. Parents `*_fast` / `*_fast_preinh` not overwritten.

| EXP | Status | thr | fires |
|-----|--------|-----|-------|
| `EXP_span25ms_fast_C1e9` | **8/8** selective | 0.0328372 | `10000000` |
| `EXP_span25ms_fast_preinh_C1e9` | **8/8** selective | 0.01563085 | `10000000` |
| `EXP_span50ms_fast_C1e9` | ok_audit=1 acc5 partial_FA | 0.0236098 | `11110000` |
| `EXP_span50ms_fast_preinh_C1e9` | **8/8** selective | 0.0112976 | `10000000` |
| `EXP_span100ms_fast_C1e9` | **7/8** selective | 0.01568185 | `10100000` |
| `EXP_span100ms_fast_preinh_C1e9` | **8/8** selective | 0.00708053 | `10000000` |

SUCCESSFUL: 8/8 + 7/8 last-pulse rows; skip span50 gen partial_FA. ts10k: catalog skip (already silent).

## P10.3 FastResponse tiprmin probe

Copies `EXPD001C1e9_phase10_tiprmin` / `EXPD002C1e9_phase10_tiprmin` (TipR@Rmin + Rmin=2e7 + silent mid). GTS kept **2000** (parent FastResponse). Parents not overwritten.

| EXP | Status | thr | note |
|-----|--------|-----|------|
| `EXPD001C1e9_phase10_tiprmin` | `ok_audit=0` silent | 0.007819505 | gap≈5.6e-5; target FN |
| `EXPD002C1e9_phase10_tiprmin` | `ok_audit=0` fire_all | 0.00837223 | per_stim / FA |

Not added to SUCCESSFUL. D/C sweep outside scope.

## P10.4 Docs skip

- PhaseA `EXP03`–`EXP05`: hygiene optional; **no foil invent**.
- `SelectivityLtzCalibrate/FastSpanLtzCal`, `BranchFastSpan`: superseded by PHASE8 Branch short + P10.2 FastSpan C1e9.

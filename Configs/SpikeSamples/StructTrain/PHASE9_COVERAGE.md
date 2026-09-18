# PHASE9 — coverage journal

Журнал волн после PHASE8. Критерии кода **не** меняются (`ok_audit` в [`scripts/selectivity_metrics.py`](scripts/selectivity_metrics.py)).  
Карта семей: [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md). Реестр PASS: [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md).

**GATE D0:** 2026-09-14 · [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv) (исторически 132/43) · архив [`archive/AUDIT_GATE_RECOMPUTE_20260914T064705Z_phase9_d0.csv`](archive/AUDIT_GATE_RECOMPUTE_20260914T064705Z_phase9_d0.csv).

**GATE T0:** 2026-09-14 · live CSV **154 Test / 64 `ok_audit=1`** (+P1–P3) · [`archive/AUDIT_GATE_RECOMPUTE_20260914T171405Z_phase9_tail.csv`](archive/AUDIT_GATE_RECOMPUTE_20260914T171405Z_phase9_tail.csv).

**Disk prep → PHASE10 S0:** pack StatisticLog/EventsLog — см. [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md) §S0.

## Анти-регрессия

Не cold-reset / overwrite:

- `TimeNeuronTimeLearnerBranch*` (+ NextSegInh / PreInh250)
- `SelectivityBranch/EXP_br480_{tiprmin,nextseginh_tiprmin,preinh250_tiprmin}`
- `SelectivityBranch/EXP_br_span*_packA_*_C1e9` (PHASE8 PASS)
- `SelectivityAsymRm/EXP_span*_pack{A,B,C}_gen` + `*_packA_preinh`
- `SelectivityLtzCalibrate/AsymRmLtzCalBranch/**` (stall)
- Удаление любых `EXP_*` FAIL

## Волны

| ID | Содержание | Статус |
|----|------------|--------|
| D0 | GATE recompute + RECIPE + orphan catalog + этот журнал | **done** |
| T0 | GATE sync +P1–P3 C1e9 (154/64) | **done** |
| P1 | Branch short pack B/C ×12 clone packA + silent mid gate | **12/12 PASS** |
| P2 | AsymRm `*_pack{B,C}_preinh_C1e9` ×6 (старые FAIL keep) | **6/6 PASS** |
| P3 | Branch NextSegInh short packA C1e9 ×3 cold Train + gate | **3/3 PASS** |
| P4 | Phase6 foil trial6 + br480 preinh250 FP; twin preinh defer | **done** (docs; mid FAIL) |
| Orphans | PSI / FastSpan / FastResponse / PhaseA03–05 — **catalog only** → PHASE10+ | cataloged |

## P1 matrix (status)

MatrixData sha256 A≡B≡C на каждом span (25/`9d50a7ab1d2a`, 50/`4757f0a41370`, 100/`ac8bf5ff2ecf`). Helper: `--pack` / `--matrix-only` в [`phase8_tiprmin_gate.py`](SelectivityBranch/scripts/phase8_tiprmin_gate.py).

| EXP | Status | thr |
|-----|--------|-----|
| `EXP_br_span25_pack{B,C}_gen_C1e9` | **PASS** | 0.07179975 |
| `EXP_br_span25_pack{B,C}_preinh_C1e9` | **PASS** | 0.05171075 |
| `EXP_br_span50_pack{B,C}_gen_C1e9` | **PASS** | 0.06440315 |
| `EXP_br_span50_pack{B,C}_preinh_C1e9` | **PASS** | 0.03008405 |
| `EXP_br_span100_pack{B,C}_gen_C1e9` | **PASS** (Done TipR) | 0.007181835 |
| `EXP_br_span100_pack{B,C}_preinh_C1e9` | **PASS** | 0.0203054 |

## P2 matrix (status)

Helper: [`SelectivityAsymRm/scripts/phase9_preinh_bc_gate.py`](SelectivityAsymRm/scripts/phase9_preinh_bc_gate.py). Old `*_preinh` FAIL kept.

| EXP | Status | thr |
|-----|--------|-----|
| `EXP_span25ms_pack{B,C}_preinh_C1e9` | **PASS** | 0.004686425 |
| `EXP_span50ms_pack{B,C}_preinh_C1e9` | **PASS** | 0.011759 |
| `EXP_span100ms_pack{B,C}_preinh_C1e9` | **PASS** | 0.006681015 |

## P3 matrix (status)

Cold Train C1e9 + NextSeg=1; Test shell from packA gen + neuron overlay (full `prepare_test` sync broke Matrix → n=25).

**PHASE12:** packA NextSeg Wave1 = 25/50 VALIDATED, **100 FAIL** (soft-cold L stuck); pack B/C = Wave 2. See `PHASE12_VALIDATION.md`.

| EXP | Status | L | thr |
|-----|--------|---|-----|
| `EXP_br_span25_packA_nextseginh_C1e9` | **PASS** | `13 11 7 1` | 0.07179975 |
| `EXP_br_span50_packA_nextseginh_C1e9` | **PASS** | `14 9 6 1` | ≈0.04564 |
| `EXP_br_span100_packA_nextseginh_C1e9` | **PASS** | `21 17 11 1` | ≈0.01443 |

## Orphans → PHASE10+ (no Train/gate in PHASE9)

Полная таблица: [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md) §«Orphans PHASE10+».

| Семья | ~N | PHASE10 start (предложение) |
|-------|----|------------------------------|
| PSI | ~38 EXP | `preinh250` @25/50/100 → `*_C1e9` + TipR@Rmin |
| FastSpan | 8 | fire_all / silent — recipe after Branch short |
| FastResponse | 9 | D/C sweep FAIL |
| PhaseA EXP03–05 | 3 | syncTol / Rgain fail |
| FastSpanLtzCal / BranchFastSpan | templates | stall / superseded |

## Ссылки

- Helper Branch: [`SelectivityBranch/scripts/phase8_tiprmin_gate.py`](SelectivityBranch/scripts/phase8_tiprmin_gate.py)
- AsymRm clone: [`SelectivityAsymRm/scripts/clone_asymrm_exp.sh`](SelectivityAsymRm/scripts/clone_asymrm_exp.sh)
- PHASE8 эталон: [`SelectivityBranch/PHASE8_SHORTSPAN.md`](SelectivityBranch/PHASE8_SHORTSPAN.md)

## P4 quality notes

### Phase6 foil trial6
Clone `SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase9_foil6` — silent foil6 ltz/soma **>** target → 8/8 unreachable by mid alone. See `PHASE9_FOIL6_NOTE.md`. Parent 7/8 retained.

### Branch br480 preinh250 FP trial4
Clone `SelectivityBranch/EXP_br480_preinh250_tiprmin_phase9_mid` — silent soma gap **negative** (trial4 > target). Mid-only FAIL. See `PHASE9_MID_NOTE.md`. Parent 7/8 retained.

### AsymRmLtzCal preinh twins
`SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span*_packA_preinh`: GATE n=2 silent — **explicit defer** (no overwrite stall Train). PHASE10+ if revisited.

**PHASE12 Wave 2a:** Branch B/C + NextSeg B/C @25/50 matrix-only reaffirm — statuses in [`PHASE12_VALIDATION.md`](PHASE12_VALIDATION.md).

**PHASE12 W2 GATE:** 2026-09-17 · 174 Test / 103 `ok_audit=1` — [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv).

## PHASE12 Wave3 pointer

See [`PHASE12_VALIDATION.md`](PHASE12_VALIDATION.md) Wave 3 run log (2026-09-18).

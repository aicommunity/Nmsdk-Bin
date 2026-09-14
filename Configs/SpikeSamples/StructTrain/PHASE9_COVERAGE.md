# PHASE9 — coverage journal

Журнал волн после PHASE8. Критерии кода **не** меняются (`ok_audit` в [`scripts/selectivity_metrics.py`](scripts/selectivity_metrics.py)).  
Карта семей: [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md). Реестр PASS: [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md).

**GATE D0:** 2026-09-14 · [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv) (132 Test, 43 `ok_audit=1`, в т.ч. PHASE8 packA C1e9 ×6) · архив [`archive/AUDIT_GATE_RECOMPUTE_20260914T064705Z_phase9_d0.csv`](archive/AUDIT_GATE_RECOMPUTE_20260914T064705Z_phase9_d0.csv).

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
| P1 | Branch short pack B/C ×12 clone packA + silent mid gate | **12/12 PASS** |
| P2 | AsymRm `*_pack{B,C}_preinh_C1e9` ×6 (старые FAIL keep) | pending |
| P3 | Branch NextSegInh short packA C1e9 ×3 cold Train + gate | scaffolded |
| P4 | Phase6 foil trial6 + br480 preinh250 FP; twin preinh defer | pending |
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

| EXP | Status | Seed |
|-----|--------|------|
| `EXP_span{25,50,100}ms_pack{B,C}_preinh_C1e9` | pending | `packA_preinh` via `clone_asymrm_exp.sh` |

## P3 matrix (status)

| EXP | Status |
|-----|--------|
| `EXP_br_span{25,50,100}_packA_nextseginh_C1e9` | pending |

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

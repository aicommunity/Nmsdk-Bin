# PHASE12 — validation manifest (source of truth)

Живой реестр статусов cold-replay / clone / artifact. Канон и tooling: [`scripts/phase12_validate.py`](scripts/phase12_validate.py), soft-cold harness [`_repro/README.md`](_repro/README.md).

**Срез:** 2026-09-16 · PulseLib pin `780ffc7` · Wave 1 = Branch short packA roots.

## Канон

| Параметр | Значение |
|----------|----------|
| Cold | soft-cold: L=`1 1 1 1`, TipR cold=`86e6×4`, links→tip-1, fat Model |
| Inject | `ResetToUntrainedState=1` |
| Stop Train | `IsNeedToTrain=0` |
| Post TipR | TipR@Rmin + tip Exc (кроме `done_tipr`) |
| Mid Branch | `soma_amp_sum` |
| Gate Branch | `phase8_tiprmin_gate.py` full prepare (no `--skip-prepare`) |
| Disk | Avail ≥80G; pack ≥200M; 1 NM |
| Promote | bak + r1≡r2 + ok_audit + acc≥7 + Need=0 + last_pulse |

Статусы: `VALIDATED` | `VALIDATED_CLONE` | `ARTIFACT` | `BLOCKED_FS` | `DEFERRED` | `OUT` | `FAIL`.

## Wave map

| Wave | Scope | Status |
|------|-------|--------|
| **1** | Branch packA ×9 cold | **in progress** |
| 2 | Branch B/C + NextSeg B/C clones; br480 tiprmin | DEFERRED |
| 3 | FS fix → FastSpan + AsymRm packA → B/C + LtzCal | DEFERRED / BLOCKED_FS |
| 4 | Phase6 480 tiprmin 7/8 | DEFERRED |
| ∞ | ARTIFACT / OUT | marked below |

---

## Catalog

Path base: `Bin/Configs/SpikeSamples/StructTrain/`.

### A. Phase A — ARTIFACT

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP00_baseline | SelectivityPhaseA/EXP00_baseline | ∞ | ARTIFACT | ARTIFACT | historical partial_FA | |
| EXP01_ltz_threshold_sweep | SelectivityPhaseA/EXP01_ltz_threshold_sweep | ∞ | ARTIFACT | ARTIFACT | | |
| EXP02_ltzone_average_mode | SelectivityPhaseA/EXP02_ltzone_average_mode | ∞ | ARTIFACT | ARTIFACT | | |
| EXP06_ltzone_integration | SelectivityPhaseA/EXP06_ltzone_integration | ∞ | ARTIFACT | ARTIFACT | | |

### B. PSI — ARTIFACT

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP01_preinh_050 | SelectivityPresynapticInhib/EXP01_preinh_050 | ∞ | ARTIFACT | ARTIFACT | | |
| EXP14_preinh_260 | SelectivityPresynapticInhib/EXP14_preinh_260 | ∞ | ARTIFACT | ARTIFACT | | |
| EXP15_preinh_270 | SelectivityPresynapticInhib/EXP15_preinh_270 | ∞ | ARTIFACT | ARTIFACT | | |
| EXP21_span100ms_preinh250 | SelectivityPresynapticInhib/EXP21_span100ms_preinh250 | ∞ | ARTIFACT | ARTIFACT | | |
| EXP31_span200ms_preinh250 | SelectivityPresynapticInhib/EXP31_span200ms_preinh250 | ∞ | ARTIFACT | ARTIFACT | | |
| EXP32_span300ms_baseline | SelectivityPresynapticInhib/EXP32_span300ms_baseline | ∞ | ARTIFACT | ARTIFACT | | |
| EXP33_span300ms_preinh250 | SelectivityPresynapticInhib/EXP33_span300ms_preinh250 | ∞ | ARTIFACT | ARTIFACT | | |
| EXP34_span400ms_baseline | SelectivityPresynapticInhib/EXP34_span400ms_baseline | ∞ | ARTIFACT | ARTIFACT | | |
| EXP35_span400ms_preinh250 | SelectivityPresynapticInhib/EXP35_span400ms_preinh250 | ∞ | ARTIFACT | ARTIFACT | | |

### C. TimeNeuron — ARTIFACT

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| TimeNeuronTimeLearner | TimeNeuronTimeLearner | ∞ | ARTIFACT | ARTIFACT | | |

### D. AsymRm short — Wave 3 DEFERRED

| exp_id | path | wave | kind | status | gold_L | gold_TipR_recipe | gold_thr | notes | last_commit |
|--------|------|------|------|--------|--------|------------------|----------|-------|-------------|
| EXP_span25ms_packA_gen | SelectivityAsymRm/EXP_span25ms_packA_gen | 3 | cold | DEFERRED | | tiprmin/base | | after FS unblock | |
| EXP_span25ms_packA_preinh | SelectivityAsymRm/EXP_span25ms_packA_preinh | 3 | cold | DEFERRED | | | | | |
| EXP_span50ms_packA_gen | SelectivityAsymRm/EXP_span50ms_packA_gen | 3 | cold | DEFERRED | `25 23 15 1` | tiprmin | 0.011759 | | |
| EXP_span50ms_packA_preinh | SelectivityAsymRm/EXP_span50ms_packA_preinh | 3 | cold | DEFERRED | | tiprmin | 0.011759 | | |
| EXP_span100ms_packA_gen | SelectivityAsymRm/EXP_span100ms_packA_gen | 3 | cold | DEFERRED | `52 48 27 1` | tiprmin | 0.006681 | | |
| EXP_span100ms_packA_preinh | SelectivityAsymRm/EXP_span100ms_packA_preinh | 3 | cold | DEFERRED | | tiprmin | 0.006681 | | |
| EXP_span25ms_packB_gen | SelectivityAsymRm/EXP_span25ms_packB_gen | 3 | clone | DEFERRED | | | | after packA | |
| EXP_span25ms_packC_gen | SelectivityAsymRm/EXP_span25ms_packC_gen | 3 | clone | DEFERRED | | | | | |
| EXP_span25ms_packB_preinh_C1e9 | SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9 | 3 | clone | DEFERRED | | | | | |
| EXP_span25ms_packC_preinh_C1e9 | SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9 | 3 | clone | DEFERRED | | | | | |
| EXP_span50ms_packB_gen | SelectivityAsymRm/EXP_span50ms_packB_gen | 3 | clone | DEFERRED | | | | | |
| EXP_span50ms_packC_gen | SelectivityAsymRm/EXP_span50ms_packC_gen | 3 | clone | DEFERRED | | | | | |
| EXP_span50ms_packB_preinh_C1e9 | SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9 | 3 | clone | DEFERRED | | | | | |
| EXP_span50ms_packC_preinh_C1e9 | SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9 | 3 | clone | DEFERRED | | | | | |
| EXP_span100ms_packB_gen | SelectivityAsymRm/EXP_span100ms_packB_gen | 3 | clone | DEFERRED | | | | | |
| EXP_span100ms_packC_gen | SelectivityAsymRm/EXP_span100ms_packC_gen | 3 | clone | DEFERRED | | | | | |
| EXP_span100ms_packB_preinh_C1e9 | SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9 | 3 | clone | DEFERRED | | | | | |
| EXP_span100ms_packC_preinh_C1e9 | SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9 | 3 | clone | DEFERRED | | | | | |

### E. AsymRmLtzCal twin — Wave 3c DEFERRED

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP_span25ms_packA_gen | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen | 3c | sync | DEFERRED | sync from AsymRm | |
| EXP_span50ms_packA_gen | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen | 3c | sync | DEFERRED | | |
| EXP_span100ms_packA_gen | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen | 3c | sync | DEFERRED | | |
| EXP_span25ms_packA_preinh | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh | 3c | sync | DEFERRED | | |
| EXP_span50ms_packA_preinh | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh | 3c | sync | DEFERRED | | |
| EXP_span100ms_packA_preinh | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh | 3c | sync | DEFERRED | | |

### F. Phase6 @480 tiprmin — Wave 4 DEFERRED

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP_480_gen_tiprmin | SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin | 4 | cold | DEFERRED | 7/8 | |
| EXP_480_gen_thr_only | SelectivityPhaseA/Phase6/EXP_480_gen_thr_only | 4 | cold | DEFERRED | 7/8 | |
| EXP_480_preinh250_tiprmin | SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin | 4 | cold | DEFERRED | 7/8 | |
| EXP_480_ltzcal_twin_gen | SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen | 4 | sync | DEFERRED | 7/8 | |

### G. Branch @480 — Wave 2 DEFERRED

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP_br480_tiprmin | SelectivityBranch/EXP_br480_tiprmin | 2 | cold | DEFERRED | 8/8 | |
| EXP_br480_nextseginh_tiprmin | SelectivityBranch/EXP_br480_nextseginh_tiprmin | 2 | cold | DEFERRED | 8/8 | |
| EXP_br480_preinh250_tiprmin | SelectivityBranch/EXP_br480_preinh250_tiprmin | 2 | cold | DEFERRED | 7/8 | |

### H. Branch short packA — Wave 1

| exp_id | path | wave | kind | status | gold_L | gold_TipR_recipe | gold_thr | notes | last_commit |
|--------|------|------|------|--------|--------|------------------|----------|-------|-------------|
| EXP_br_span25_packA_gen_C1e9 | SelectivityBranch/EXP_br_span25_packA_gen_C1e9 | 1 | cold | VALIDATED | `13 11 7 1` | tiprmin | 0.07179975 | stamp-from-repro preferred (`REPRO_OK_EXACT`) | |
| EXP_br_span50_packA_gen_C1e9 | SelectivityBranch/EXP_br_span50_packA_gen_C1e9 | 1 | cold | VALIDATED | `13 11 6 1` | tiprmin | 0.06440315 | | |
| EXP_br_span100_packA_gen_C1e9 | SelectivityBranch/EXP_br_span100_packA_gen_C1e9 | 1 | cold | DEFERRED | `25 21 11 1` | done_tipr | 0.007181835 | Done TipR + `--allow-done-tipr-fallback` | |
| EXP_br_span25_packA_preinh_C1e9 | SelectivityBranch/EXP_br_span25_packA_preinh_C1e9 | 1 | cold | VALIDATED | `7 6 4 1` | tiprmin | 0.05171075 | | |
| EXP_br_span50_packA_preinh_C1e9 | SelectivityBranch/EXP_br_span50_packA_preinh_C1e9 | 1 | cold | DEFERRED | `13 11 6 1` | tiprmin | 0.03008405 | | |
| EXP_br_span100_packA_preinh_C1e9 | SelectivityBranch/EXP_br_span100_packA_preinh_C1e9 | 1 | cold | DEFERRED | `22 18 11 1` | tiprmin | 0.0203054 | | |
| EXP_br_span25_packA_nextseginh_C1e9 | SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9 | 1 | cold | DEFERRED | `13 11 7 1` | tiprmin | 0.07179975 | NextSeg=1 | |
| EXP_br_span50_packA_nextseginh_C1e9 | SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9 | 1 | cold | DEFERRED | `14 9 6 1` | tiprmin | 0.0456422 | NextSeg=1 | |
| EXP_br_span100_packA_nextseginh_C1e9 | SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9 | 1 | cold | DEFERRED | `21 17 11 1` | tiprmin | 0.014432775 | NextSeg=1 | |

### I. Branch pack B/C + NextSeg B/C — Wave 2 DEFERRED

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP_br_span25_packB_gen_C1e9 | SelectivityBranch/EXP_br_span25_packB_gen_C1e9 | 2 | clone | DEFERRED | matrix-only after packA | |
| EXP_br_span25_packC_gen_C1e9 | SelectivityBranch/EXP_br_span25_packC_gen_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span25_packB_preinh_C1e9 | SelectivityBranch/EXP_br_span25_packB_preinh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span25_packC_preinh_C1e9 | SelectivityBranch/EXP_br_span25_packC_preinh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span50_packB_gen_C1e9 | SelectivityBranch/EXP_br_span50_packB_gen_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span50_packC_gen_C1e9 | SelectivityBranch/EXP_br_span50_packC_gen_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span50_packB_preinh_C1e9 | SelectivityBranch/EXP_br_span50_packB_preinh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span50_packC_preinh_C1e9 | SelectivityBranch/EXP_br_span50_packC_preinh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span100_packB_gen_C1e9 | SelectivityBranch/EXP_br_span100_packB_gen_C1e9 | 2 | clone | DEFERRED | Done TipR parent | |
| EXP_br_span100_packC_gen_C1e9 | SelectivityBranch/EXP_br_span100_packC_gen_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span100_packB_preinh_C1e9 | SelectivityBranch/EXP_br_span100_packB_preinh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span100_packC_preinh_C1e9 | SelectivityBranch/EXP_br_span100_packC_preinh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span25_packB_nextseginh_C1e9 | SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span25_packC_nextseginh_C1e9 | SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span50_packB_nextseginh_C1e9 | SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span50_packC_nextseginh_C1e9 | SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span100_packB_nextseginh_C1e9 | SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9 | 2 | clone | DEFERRED | | |
| EXP_br_span100_packC_nextseginh_C1e9 | SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9 | 2 | clone | DEFERRED | | |

### J. FastSpan C1e9 — Wave 3 BLOCKED_FS / OUT

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP_span25ms_fast_C1e9 | SelectivityFastSpan/EXP_span25ms_fast_C1e9 | 3 | cold | BLOCKED_FS | soft-cold REPRO_FAIL Need=1 L=`7 5 4 1` | |
| EXP_span25ms_fast_preinh_C1e9 | SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9 | 3 | cold | BLOCKED_FS | | |
| EXP_span50ms_fast_preinh_C1e9 | SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9 | 3 | cold | BLOCKED_FS | | |
| EXP_span100ms_fast_C1e9 | SelectivityFastSpan/EXP_span100ms_fast_C1e9 | 3 | cold | BLOCKED_FS | 7/8 registry | |
| EXP_span100ms_fast_preinh_C1e9 | SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9 | 3 | cold | BLOCKED_FS | | |
| EXP_span50ms_fast_C1e9 | SelectivityFastSpan/EXP_span50ms_fast_C1e9 | ∞ | OUT | OUT | acc5 not in SUCCESSFUL | |

### K. OUT / demoted

| exp_id | status | notes |
|--------|--------|-------|
| TimeNeuronTimeLearnerBranch* (no tiprmin) | OUT | late_fp + per_stim demoted |
| EXP_br_span25_tiprmin / BranchFastSpan | OUT | fire_all / FAIL superseded PHASE8 |
| FastResponse tiprmin P10.3 | OUT | silent / fire_all |
| AsymRmLtzCalBranch stall ×6 | OUT | replaced by PHASE8 |
| PSI short C1e9 cold | OUT | PHASE11 R2.2 fail ≥7 |
| PhaseA EXP03–05 / FastSpanLtzCal | OUT | docs skip |
| PHASE6 foil6 mid | OUT | FAIL amp inversion |
| EXP_480_gen_baseline | OUT | EXP00 duplicate |

---

## Wave 1 run log

| UTC | exp_id | verdict | L | thr | fires | notes |
|-----|--------|---------|---|-----|-------|-------|
| 2026-09-16T21:32Z | EXP_br_span25_packA_preinh_C1e9 | VALIDATED | | | | verdict=REPRO_OK_EXACT L=`7 6 4 1` thr=0.05171075 fires=`10000000` |
| 2026-09-16T18:22Z | EXP_br_span25_packA_preinh_C1e9 | FAIL | | | | train exited_need1 r1 |
| 2026-09-16T15:35Z | EXP_br_span50_packA_gen_C1e9 | VALIDATED | | | | verdict=REPRO_OK_EXACT L=`13 11 6 1` thr=0.06440315 fires=`10000000` |
| 2026-09-16T13:51Z | EXP_br_span25_packA_gen_C1e9 | VALIDATED | | | | stamp-from-repro REPRO_OK_EXACT L=`13 11 7 1` thr=0.07179975 |

## Links

- [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md)
- [`SelectivityBranch/PHASE8_SHORTSPAN.md`](SelectivityBranch/PHASE8_SHORTSPAN.md)
- [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) · [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md) · [`PHASE11_COVERAGE.md`](PHASE11_COVERAGE.md)
- [`_repro/REPRO_COLD_RESULT.md`](_repro/REPRO_COLD_RESULT.md) · [`_repro/REPRO_COLD_INVESTIGATION.md`](_repro/REPRO_COLD_INVESTIGATION.md)

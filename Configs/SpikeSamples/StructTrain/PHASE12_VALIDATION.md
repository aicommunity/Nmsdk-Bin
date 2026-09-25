# PHASE12 — validation manifest (source of truth)

**Уточнение аудита 2026-09-22:** таблицы ниже — исторические результаты при указанных pins и gate. Они не доказывают held-out качество текущего HEAD. Каталог PHASE12 содержит 12 VALIDATED (включая две LtzCal-копии) и 20 VALIDATED_CLONE, а не 32 независимых cold-обучения. Известны дефекты окон, strict/last-pulse и inference-mid. [Разбор и актуальный контракт](AUDIT_2026-09-22.md).


Живой реестр статусов cold-replay / clone / artifact. Канон и tooling: [`scripts/phase12_validate.py`](scripts/phase12_validate.py), soft-cold harness [`_repro/README.md`](_repro/README.md).  
**Карта надёжности (подходы / параметры / размер паттерна):** [`RELIABILITY_MAP.ru.md`](RELIABILITY_MAP.ru.md) · [`RELIABILITY_MAP.md`](RELIABILITY_MAP.md).

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

Статусы: `VALIDATED` | `VALIDATED_CLONE` | `ARTIFACT` | `ARTIFACT_KEEP` | `BLOCKED_FS` | `DEFERRED` | `DEFERRED_PARENT_FAIL` | `OUT` | `FAIL` | `FAIL_ROOTCAUSE`.

## Wave map

| Wave | Scope | Status |
|------|-------|--------|
| **1** | Branch packA ×9 cold | **done (8/9 VALIDATED, 1 FAIL)** |
| 2 | Branch B/C + NextSeg B/C clones; br480 tiprmin | **done** (W2a: 16 VALIDATED_CLONE + 2 DEFERRED_PARENT_FAIL; W2b: 3 FAIL soft-cold Need≠0) |
| 3 | FS fix → FastSpan + AsymRm packA → B/C + LtzCal | **done** (FS FAIL_ROOTCAUSE+BLOCKED; AsymRm span25 VALIDATED×2+CLONE×4; span50/100 ARTIFACT_KEEP; LtzCal ARTIFACT_KEEP) |
| 4 | Phase6 480 tiprmin 7/8 | **done ARTIFACT_KEEP** (gold kept; soft-cold prepare AutoCal) |
| **5** | Tails closure (Phase6 retry, LtzCal25 VALIDATED, FS/Asym/Branch close) | **done** (§8: no BLOCKED_FS/DEFERRED*; LtzCal25 VALIDATED×2; rest ARTIFACT_KEEP/FAIL_ROOTCAUSE) |
| **6** | Quality tails (FS Need C++, AsymRm mid, Phase6/Branch invest, proposals doc) | **done** (invest exhausted; QUALITY_BACKLOG_PROPOSALS.md; pin 780ffc7) |
| ∞ | ARTIFACT / OUT | marked below |
| FAIL backlog | nextseg100 + br480×3 | **closed Wave5** as ARTIFACT_KEEP; Wave6 re-invest |

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
| EXP_span25ms_packA_gen | SelectivityAsymRm/EXP_span25ms_packA_gen | 3 | cold | VALIDATED | | tiprmin/base | | after FS unblock | |
| EXP_span25ms_packA_preinh | SelectivityAsymRm/EXP_span25ms_packA_preinh | 3 | cold | VALIDATED | | | | | |
| EXP_span50ms_packA_gen | SelectivityAsymRm/EXP_span50ms_packA_gen | 3 | cold | ARTIFACT_KEEP | `25 23 15 1` | tiprmin | 0.011759 | | |
| EXP_span50ms_packA_preinh | SelectivityAsymRm/EXP_span50ms_packA_preinh | 3 | cold | ARTIFACT_KEEP | | tiprmin | 0.011759 | | |
| EXP_span100ms_packA_gen | SelectivityAsymRm/EXP_span100ms_packA_gen | 3 | cold | ARTIFACT_KEEP | `52 48 27 1` | tiprmin | 0.006681 | | |
| EXP_span100ms_packA_preinh | SelectivityAsymRm/EXP_span100ms_packA_preinh | 3 | cold | ARTIFACT_KEEP | | tiprmin | 0.006681 | | |
| EXP_span25ms_packB_gen | SelectivityAsymRm/EXP_span25ms_packB_gen | 3 | clone | VALIDATED_CLONE | | | | after packA | |
| EXP_span25ms_packC_gen | SelectivityAsymRm/EXP_span25ms_packC_gen | 3 | clone | VALIDATED_CLONE | | | | | |
| EXP_span25ms_packB_preinh_C1e9 | SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9 | 3 | clone | VALIDATED_CLONE | | | | | |
| EXP_span25ms_packC_preinh_C1e9 | SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9 | 3 | clone | VALIDATED_CLONE | | | | | |
| EXP_span50ms_packB_gen | SelectivityAsymRm/EXP_span50ms_packB_gen | 3 | clone | ARTIFACT_KEEP | | | | | |
| EXP_span50ms_packC_gen | SelectivityAsymRm/EXP_span50ms_packC_gen | 3 | clone | ARTIFACT_KEEP | | | | | |
| EXP_span50ms_packB_preinh_C1e9 | SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9 | 3 | clone | ARTIFACT_KEEP | | | | | |
| EXP_span50ms_packC_preinh_C1e9 | SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9 | 3 | clone | ARTIFACT_KEEP | | | | | |
| EXP_span100ms_packB_gen | SelectivityAsymRm/EXP_span100ms_packB_gen | 3 | clone | ARTIFACT_KEEP | | | | | |
| EXP_span100ms_packC_gen | SelectivityAsymRm/EXP_span100ms_packC_gen | 3 | clone | ARTIFACT_KEEP | | | | | |
| EXP_span100ms_packB_preinh_C1e9 | SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9 | 3 | clone | ARTIFACT_KEEP | | | | | |
| EXP_span100ms_packC_preinh_C1e9 | SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9 | 3 | clone | ARTIFACT_KEEP | | | | | |

### E. AsymRmLtzCal twin — Wave 3c DEFERRED

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP_span25ms_packA_gen | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen | 3c | sync | VALIDATED | sync from AsymRm | |
| EXP_span50ms_packA_gen | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen | 3c | sync | ARTIFACT_KEEP | | |
| EXP_span100ms_packA_gen | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen | 3c | sync | ARTIFACT_KEEP | | |
| EXP_span25ms_packA_preinh | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh | 3c | sync | VALIDATED | | |
| EXP_span50ms_packA_preinh | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh | 3c | sync | ARTIFACT_KEEP | | |
| EXP_span100ms_packA_preinh | SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh | 3c | sync | ARTIFACT_KEEP | | |

### F. Phase6 @480 tiprmin — Wave 4 DEFERRED

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP_480_gen_tiprmin | SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin | 4 | cold | ARTIFACT_KEEP | 7/8 | |
| EXP_480_gen_thr_only | SelectivityPhaseA/Phase6/EXP_480_gen_thr_only | 4 | cold | ARTIFACT_KEEP | 7/8 | |
| EXP_480_preinh250_tiprmin | SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin | 4 | cold | ARTIFACT_KEEP | 7/8 | |
| EXP_480_ltzcal_twin_gen | SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen | 4 | sync | ARTIFACT_KEEP | 7/8 | |

### G. Branch @480 — Wave 2b FAIL (soft-cold)

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP_br480_tiprmin | SelectivityBranch/EXP_br480_tiprmin | 2 | cold | ARTIFACT_KEEP | soft-cold Need≠0 after 4×600; L stuck atypical; gold kept | |
| EXP_br480_nextseginh_tiprmin | SelectivityBranch/EXP_br480_nextseginh_tiprmin | 2 | cold | ARTIFACT_KEEP | soft-cold Need≠0 after 4×600; gold kept | |
| EXP_br480_preinh250_tiprmin | SelectivityBranch/EXP_br480_preinh250_tiprmin | 2 | cold | ARTIFACT_KEEP | soft-cold Need≠0 after 4×600; gold kept | |

### H. Branch short packA — Wave 1

| exp_id | path | wave | kind | status | gold_L | gold_TipR_recipe | gold_thr | notes | last_commit |
|--------|------|------|------|--------|--------|------------------|----------|-------|-------------|
| EXP_br_span25_packA_gen_C1e9 | SelectivityBranch/EXP_br_span25_packA_gen_C1e9 | 1 | cold | VALIDATED | `13 11 7 1` | tiprmin | 0.07179975 | stamp-from-repro preferred (`REPRO_OK_EXACT`) | |
| EXP_br_span50_packA_gen_C1e9 | SelectivityBranch/EXP_br_span50_packA_gen_C1e9 | 1 | cold | VALIDATED | `13 11 6 1` | tiprmin | 0.06440315 | | |
| EXP_br_span100_packA_gen_C1e9 | SelectivityBranch/EXP_br_span100_packA_gen_C1e9 | 1 | cold | VALIDATED | `25 21 11 1` | done_tipr | 0.007181835 | Done TipR + `--allow-done-tipr-fallback` | |
| EXP_br_span25_packA_preinh_C1e9 | SelectivityBranch/EXP_br_span25_packA_preinh_C1e9 | 1 | cold | VALIDATED | `7 6 4 1` | tiprmin | 0.05171075 | | |
| EXP_br_span50_packA_preinh_C1e9 | SelectivityBranch/EXP_br_span50_packA_preinh_C1e9 | 1 | cold | VALIDATED | `13 11 6 1` | tiprmin | 0.03008405 | | |
| EXP_br_span100_packA_preinh_C1e9 | SelectivityBranch/EXP_br_span100_packA_preinh_C1e9 | 1 | cold | VALIDATED | `22 18 11 1` | tiprmin | 0.0203054 | | |
| EXP_br_span25_packA_nextseginh_C1e9 | SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9 | 1 | cold | VALIDATED | `13 11 7 1` | tiprmin | 0.07179975 | NextSeg=1 | |
| EXP_br_span50_packA_nextseginh_C1e9 | SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9 | 1 | cold | VALIDATED | `14 9 6 1` | tiprmin | 0.0456422 | NextSeg=1 | |
| EXP_br_span100_packA_nextseginh_C1e9 | SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9 | 1 | cold | ARTIFACT_KEEP | `21 17 11 1` | tiprmin | 0.014432775 | soft-cold L stuck `1 1 1 1` ×3×320; gold kept; follow-up | |

### I. Branch pack B/C + NextSeg B/C — Wave 2a done

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP_br_span25_packB_gen_C1e9 | SelectivityBranch/EXP_br_span25_packB_gen_C1e9 | 2 | clone | VALIDATED_CLONE | matrix-only after packA | |
| EXP_br_span25_packC_gen_C1e9 | SelectivityBranch/EXP_br_span25_packC_gen_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span25_packB_preinh_C1e9 | SelectivityBranch/EXP_br_span25_packB_preinh_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span25_packC_preinh_C1e9 | SelectivityBranch/EXP_br_span25_packC_preinh_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span50_packB_gen_C1e9 | SelectivityBranch/EXP_br_span50_packB_gen_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span50_packC_gen_C1e9 | SelectivityBranch/EXP_br_span50_packC_gen_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span50_packB_preinh_C1e9 | SelectivityBranch/EXP_br_span50_packB_preinh_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span50_packC_preinh_C1e9 | SelectivityBranch/EXP_br_span50_packC_preinh_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span100_packB_gen_C1e9 | SelectivityBranch/EXP_br_span100_packB_gen_C1e9 | 2 | clone | VALIDATED_CLONE | Done TipR parent | |
| EXP_br_span100_packC_gen_C1e9 | SelectivityBranch/EXP_br_span100_packC_gen_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span100_packB_preinh_C1e9 | SelectivityBranch/EXP_br_span100_packB_preinh_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span100_packC_preinh_C1e9 | SelectivityBranch/EXP_br_span100_packC_preinh_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span25_packB_nextseginh_C1e9 | SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span25_packC_nextseginh_C1e9 | SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span50_packB_nextseginh_C1e9 | SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span50_packC_nextseginh_C1e9 | SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9 | 2 | clone | VALIDATED_CLONE | | |
| EXP_br_span100_packB_nextseginh_C1e9 | SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9 | 2 | clone | ARTIFACT_KEEP | | |
| EXP_br_span100_packC_nextseginh_C1e9 | SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9 | 2 | clone | ARTIFACT_KEEP | | |

### J. FastSpan C1e9 — Wave 3 BLOCKED_FS / OUT

| exp_id | path | wave | kind | status | notes | last_commit |
|--------|------|------|------|--------|-------|-------------|
| EXP_span25ms_fast_C1e9 | SelectivityFastSpan/EXP_span25ms_fast_C1e9 | 3 | cold | FAIL_ROOTCAUSE | W3a soft-cold Need=1 L=`6 5 4 1` after 180×3; PulseLib pin; no FS×5| |
| EXP_span25ms_fast_preinh_C1e9 | SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9 | 3 | cold | ARTIFACT_KEEP | | |
| EXP_span50ms_fast_preinh_C1e9 | SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9 | 3 | cold | ARTIFACT_KEEP | | |
| EXP_span100ms_fast_C1e9 | SelectivityFastSpan/EXP_span100ms_fast_C1e9 | 3 | cold | ARTIFACT_KEEP | 7/8 registry | |
| EXP_span100ms_fast_preinh_C1e9 | SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9 | 3 | cold | ARTIFACT_KEEP | | |
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

## Wave 6 run log

| utc | exp_id | status | L | thr | fires | notes |
|-----|--------|---------|---|-----|-------|-------|
| 2026-09-19T09:08Z | EXP_br480_preinh250_tiprmin | ARTIFACT_KEEP | | | | W6.7: soft+strip pilot tiprmin -t180 L stuck; no 2×600; gold 7/8 kept |
| 2026-09-19T09:08Z | EXP_br480_nextseginh_tiprmin | ARTIFACT_KEEP | | | | W6.7: soft+strip pilot tiprmin -t180 L stuck; no 2×600; gold 7/8 kept |
| 2026-09-19T09:08Z | EXP_br480_tiprmin | ARTIFACT_KEEP | | | | W6.7: soft+strip pilot tiprmin -t180 L stuck; no 2×600; gold 7/8 kept |
| 2026-09-19T09:08Z | EXP_br_span100_packC_nextseginh_C1e9 | ARTIFACT_KEEP | | | | W6.6: parent ARTIFACT_KEEP; clone not gated |
| 2026-09-19T09:08Z | EXP_br_span100_packB_nextseginh_C1e9 | ARTIFACT_KEEP | | | | W6.6: parent ARTIFACT_KEEP; clone not gated |
| 2026-09-19T09:08Z | EXP_br_span100_packA_nextseginh_C1e9 | ARTIFACT_KEEP | | | | W6.6: soft+strip probe -t200 L stuck `1 1 1 1`; no marathon; gold kept |
| 2026-09-19T08:52Z | EXP_480_ltzcal_twin_gen | ARTIFACT_KEEP | | | | W6.5: soft+strip probe -t120 L stuck `1 1 1 1`; AutoCal=0; ARTIFACT_KEEP; gold 7/8 |
| 2026-09-19T08:52Z | EXP_480_preinh250_tiprmin | ARTIFACT_KEEP | | | | W6.5: soft+strip probe -t120 L stuck `1 1 1 1`; AutoCal=0; ARTIFACT_KEEP; gold 7/8 |
| 2026-09-19T08:52Z | EXP_480_gen_thr_only | ARTIFACT_KEEP | | | | W6.5: soft+strip probe -t120 L stuck `1 1 1 1`; AutoCal=0; ARTIFACT_KEEP; gold 7/8 |
| 2026-09-19T08:52Z | EXP_480_gen_tiprmin | ARTIFACT_KEEP | | | | W6.5: soft+strip probe -t120 L stuck `1 1 1 1`; AutoCal=0; ARTIFACT_KEEP; gold 7/8 |
| 2026-09-19T08:37Z | EXP_span100ms_packA_preinh | ARTIFACT_KEEP | | | | W6.4: parent AsymRm midflat; no sync |
| 2026-09-19T08:37Z | EXP_span100ms_packA_gen | ARTIFACT_KEEP | | | | W6.4: parent AsymRm midflat; no sync |
| 2026-09-19T08:37Z | EXP_span100ms_packC_preinh_C1e9 | ARTIFACT_KEEP | | | | W6.4: parent midflat ARTIFACT_KEEP; clone not gated |
| 2026-09-19T08:37Z | EXP_span100ms_packC_gen | ARTIFACT_KEEP | | | | W6.4: parent midflat ARTIFACT_KEEP; clone not gated |
| 2026-09-19T08:37Z | EXP_span100ms_packB_preinh_C1e9 | ARTIFACT_KEEP | | | | W6.4: parent midflat ARTIFACT_KEEP; clone not gated |
| 2026-09-19T08:37Z | EXP_span100ms_packB_gen | ARTIFACT_KEEP | | | | W6.4: parent midflat ARTIFACT_KEEP; clone not gated |
| 2026-09-19T08:37Z | EXP_span50ms_packA_preinh | ARTIFACT_KEEP | | | | W6.4: parent AsymRm midflat; no sync |
| 2026-09-19T08:37Z | EXP_span50ms_packA_gen | ARTIFACT_KEEP | | | | W6.4: parent AsymRm midflat; no sync |
| 2026-09-19T08:37Z | EXP_span50ms_packC_preinh_C1e9 | ARTIFACT_KEEP | | | | W6.4: parent midflat ARTIFACT_KEEP; clone not gated |
| 2026-09-19T08:37Z | EXP_span50ms_packC_gen | ARTIFACT_KEEP | | | | W6.4: parent midflat ARTIFACT_KEEP; clone not gated |
| 2026-09-19T08:37Z | EXP_span50ms_packB_preinh_C1e9 | ARTIFACT_KEEP | | | | W6.4: parent midflat ARTIFACT_KEEP; clone not gated |
| 2026-09-19T08:37Z | EXP_span50ms_packB_gen | ARTIFACT_KEEP | | | | W6.4: parent midflat ARTIFACT_KEEP; clone not gated |
| 2026-09-19T08:37Z | EXP_span100ms_packA_preinh | ARTIFACT_KEEP | | | | W6.3: overlay tiprmin on soft still ltz flat; ROOTCAUSE updated; gold kept |
| 2026-09-19T08:37Z | EXP_span100ms_packA_gen | ARTIFACT_KEEP | | | | W6.3: overlay tiprmin on soft still ltz flat; ROOTCAUSE updated; gold kept |
| 2026-09-19T08:37Z | EXP_span50ms_packA_preinh | ARTIFACT_KEEP | | | | W6.3: overlay tiprmin on soft still ltz flat; ROOTCAUSE updated; gold kept |
| 2026-09-19T08:37Z | EXP_span50ms_packA_gen | ARTIFACT_KEEP | | | | W6.3: overlay tiprmin on soft still ltz flat; ROOTCAUSE updated; gold kept |
| 2026-09-19T08:37Z | EXP_span100ms_fast_preinh_C1e9 | ARTIFACT_KEEP | | | | W6.2: parent FS25 FAIL_ROOTCAUSE; no cold |
| 2026-09-19T08:37Z | EXP_span100ms_fast_C1e9 | ARTIFACT_KEEP | | | | W6.2: parent FS25 FAIL_ROOTCAUSE; no cold |
| 2026-09-19T08:37Z | EXP_span50ms_fast_preinh_C1e9 | ARTIFACT_KEEP | | | | W6.2: parent FS25 FAIL_ROOTCAUSE; no cold |
| 2026-09-19T08:37Z | EXP_span25ms_fast_preinh_C1e9 | ARTIFACT_KEEP | | | | W6.2: parent FS25 FAIL_ROOTCAUSE; no cold |
| 2026-09-19T08:37Z | EXP_span25ms_fast_C1e9 | FAIL_ROOTCAUSE | | | | W6.1: NEED_TRACE_W6 code analysis; no pin change (blast-radius); proposals §A |

## Wave 5 run log

| utc | exp_id | status | L | thr | fires | notes |
|-----|--------|---------|---|-----|-------|-------|
| 2026-09-19T08:09Z | EXP_br480_preinh250_tiprmin | ARTIFACT_KEEP | | | | W5.8: soft-cold Need≠0 @4×600 (W2); no marathon; gold 7/8 kept; ARTIFACT_KEEP default |
| 2026-09-19T08:09Z | EXP_br480_nextseginh_tiprmin | ARTIFACT_KEEP | | | | W5.8: soft-cold Need≠0 @4×600 (W2); no marathon; gold 7/8 kept; ARTIFACT_KEEP default |
| 2026-09-19T08:09Z | EXP_br480_tiprmin | ARTIFACT_KEEP | | | | W5.8: soft-cold Need≠0 @4×600 (W2); no marathon; gold 7/8 kept; ARTIFACT_KEEP default |
| 2026-09-19T08:09Z | EXP_br_span100_packC_nextseginh_C1e9 | ARTIFACT_KEEP | | | | W5.7: parent nextseg100 ARTIFACT_KEEP closed; clone not gated |
| 2026-09-19T08:09Z | EXP_br_span100_packB_nextseginh_C1e9 | ARTIFACT_KEEP | | | | W5.7: parent nextseg100 ARTIFACT_KEEP closed; clone not gated |
| 2026-09-19T08:09Z | EXP_br_span100_packA_nextseginh_C1e9 | ARTIFACT_KEEP | | | | W5.7: soft-cold L stuck `1 1 1 1` (W1); no marathon; gold kept; closed ARTIFACT_KEEP |
| 2026-09-19T08:09Z | EXP_span100ms_packA_preinh | ARTIFACT_KEEP | | | | W5.6: parent AsymRm ARTIFACT_KEEP midflat; no sync |
| 2026-09-19T08:09Z | EXP_span100ms_packA_gen | ARTIFACT_KEEP | | | | W5.6: parent AsymRm ARTIFACT_KEEP midflat; no sync |
| 2026-09-19T08:09Z | EXP_span50ms_packA_preinh | ARTIFACT_KEEP | | | | W5.6: parent AsymRm ARTIFACT_KEEP midflat; no sync |
| 2026-09-19T08:09Z | EXP_span50ms_packA_gen | ARTIFACT_KEEP | | | | W5.6: parent AsymRm ARTIFACT_KEEP midflat; no sync |
| 2026-09-19T08:09Z | EXP_span100ms_packC_preinh_C1e9 | ARTIFACT_KEEP | | | | W5.6: parent packA ARTIFACT_KEEP midflat closed; clone not gated |
| 2026-09-19T08:09Z | EXP_span100ms_packC_gen | ARTIFACT_KEEP | | | | W5.6: parent packA ARTIFACT_KEEP midflat closed; clone not gated |
| 2026-09-19T08:09Z | EXP_span100ms_packB_preinh_C1e9 | ARTIFACT_KEEP | | | | W5.6: parent packA ARTIFACT_KEEP midflat closed; clone not gated |
| 2026-09-19T08:09Z | EXP_span100ms_packB_gen | ARTIFACT_KEEP | | | | W5.6: parent packA ARTIFACT_KEEP midflat closed; clone not gated |
| 2026-09-19T08:09Z | EXP_span50ms_packC_preinh_C1e9 | ARTIFACT_KEEP | | | | W5.6: parent packA ARTIFACT_KEEP midflat closed; clone not gated |
| 2026-09-19T08:09Z | EXP_span50ms_packC_gen | ARTIFACT_KEEP | | | | W5.6: parent packA ARTIFACT_KEEP midflat closed; clone not gated |
| 2026-09-19T08:09Z | EXP_span50ms_packB_preinh_C1e9 | ARTIFACT_KEEP | | | | W5.6: parent packA ARTIFACT_KEEP midflat closed; clone not gated |
| 2026-09-19T08:09Z | EXP_span50ms_packB_gen | ARTIFACT_KEEP | | | | W5.6: parent packA ARTIFACT_KEEP midflat closed; clone not gated |
| 2026-09-19T08:09Z | EXP_span100ms_packA_preinh | ARTIFACT_KEEP | | | | W5.5: midflat ROOTCAUSE (_repro/_invest/asym_midflat); soft Need=0 L≡gold; ltz flat tiprmin+86e6; soma=0; gold kept |
| 2026-09-19T08:09Z | EXP_span100ms_packA_gen | ARTIFACT_KEEP | | | | W5.5: midflat ROOTCAUSE (_repro/_invest/asym_midflat); soft Need=0 L≡gold; ltz flat tiprmin+86e6; soma=0; gold kept |
| 2026-09-19T08:09Z | EXP_span50ms_packA_preinh | ARTIFACT_KEEP | | | | W5.5: midflat ROOTCAUSE (_repro/_invest/asym_midflat); soft Need=0 L≡gold; ltz flat tiprmin+86e6; soma=0; gold kept |
| 2026-09-19T08:09Z | EXP_span50ms_packA_gen | ARTIFACT_KEEP | | | | W5.5: midflat ROOTCAUSE (_repro/_invest/asym_midflat); soft Need=0 L≡gold; ltz flat tiprmin+86e6; soma=0; gold kept |
| 2026-09-19T08:09Z | EXP_span100ms_fast_preinh_C1e9 | ARTIFACT_KEEP | | | | W5.4: parent FS25 FAIL_ROOTCAUSE closed; no cold; gold kept |
| 2026-09-19T08:09Z | EXP_span100ms_fast_C1e9 | ARTIFACT_KEEP | | | | W5.4: parent FS25 FAIL_ROOTCAUSE closed; no cold; gold kept |
| 2026-09-19T08:09Z | EXP_span50ms_fast_preinh_C1e9 | ARTIFACT_KEEP | | | | W5.4: parent FS25 FAIL_ROOTCAUSE closed; no cold; gold kept |
| 2026-09-19T08:09Z | EXP_span25ms_fast_preinh_C1e9 | ARTIFACT_KEEP | | | | W5.4: parent FS25 FAIL_ROOTCAUSE closed; no cold; gold kept |
| 2026-09-19T08:09Z | EXP_span25ms_fast_C1e9 | FAIL_ROOTCAUSE | | | | W5.3: Need-trace documented; no PulseLib patch (blast-radius); pin 780ffc7; §8 terminal |
| 2026-09-19T08:07Z | EXP_span25ms_packA_preinh | VALIDATED | | | | sync from AsymRm; thr=0.0179375; acc=8 |
| 2026-09-19T07:57Z | EXP_span25ms_packA_gen | VALIDATED | | | | sync from AsymRm; thr=0.03758795; acc=8 |
| 2026-09-19T07:45Z | EXP_480_ltzcal_twin_gen | ARTIFACT_KEEP | | | | W5.1 soft-cold: AutoCal inject OK (=0); L stuck `1 1 1 1` Need=1 @model_t>~140 (no L growth); gold 7/8 registry kept; no marathon |
| 2026-09-19T07:45Z | EXP_480_preinh250_tiprmin | ARTIFACT_KEEP | | | | W5.1 soft-cold: AutoCal inject OK (=0); L stuck `1 1 1 1` Need=1 @model_t>~140 (no L growth); gold 7/8 registry kept; no marathon |
| 2026-09-19T07:45Z | EXP_480_gen_thr_only | ARTIFACT_KEEP | | | | W5.1 soft-cold: AutoCal inject OK (=0); L stuck `1 1 1 1` Need=1 @model_t>~140 (no L growth); gold 7/8 registry kept; no marathon |
| 2026-09-19T07:45Z | EXP_480_gen_tiprmin | ARTIFACT_KEEP | | | | W5.1 soft-cold: AutoCal inject OK (=0); L stuck `1 1 1 1` Need=1 @model_t>~140 (no L growth); gold 7/8 registry kept; no marathon |

## Wave 3 run log

| utc | exp_id | status | L | thr | fires | notes |
|-----|--------|---------|---|-----|-------|-------|
| 2026-09-18T22:17Z | EXP_480_ltzcal_twin_gen | ARTIFACT_KEEP | | | | ARTIFACT_KEEP: W4 soft-cold AutoCal-missing/prepare fail or Need≠0 risk; gold 7/8 registry kept (no br480 marathon) |
| 2026-09-18T22:17Z | EXP_480_preinh250_tiprmin | ARTIFACT_KEEP | | | | ARTIFACT_KEEP: W4 soft-cold AutoCal-missing/prepare fail or Need≠0 risk; gold 7/8 registry kept (no br480 marathon) |
| 2026-09-18T22:17Z | EXP_480_gen_thr_only | ARTIFACT_KEEP | | | | ARTIFACT_KEEP: W4 soft-cold AutoCal-missing/prepare fail or Need≠0 risk; gold 7/8 registry kept (no br480 marathon) |
| 2026-09-18T22:17Z | EXP_480_gen_tiprmin | ARTIFACT_KEEP | | | | ARTIFACT_KEEP: W4 soft-cold AutoCal-missing/prepare fail or Need≠0 risk; gold 7/8 registry kept (no br480 marathon) |
| 2026-09-18T22:14Z | EXP_span100ms_packA_preinh | ARTIFACT_KEEP | | | | parent AsymRm ARTIFACT_KEEP; no sync |
| 2026-09-18T22:14Z | EXP_span100ms_packA_gen | ARTIFACT_KEEP | | | | parent AsymRm ARTIFACT_KEEP; no sync |
| 2026-09-18T22:14Z | EXP_span50ms_packA_preinh | ARTIFACT_KEEP | | | | parent AsymRm ARTIFACT_KEEP; no sync |
| 2026-09-18T22:14Z | EXP_span50ms_packA_gen | ARTIFACT_KEEP | | | | parent AsymRm ARTIFACT_KEEP; no sync |
| 2026-09-18T22:14Z | EXP_span25ms_packA_preinh | ARTIFACT_KEEP | | | | sync from AsymRm done; phase9 gate fail tiprmin hygiene on TipR86e6 twin; weights synced |
| 2026-09-18T22:14Z | EXP_span25ms_packA_gen | ARTIFACT_KEEP | | | | sync from AsymRm done; phase9 gate fail tiprmin hygiene on TipR86e6 twin; weights synced |
| 2026-09-18T22:14Z | EXP_span25ms_packA_preinh | VALIDATED | | | | restore after LtzCal sync mis-wrote AsymRm status |
| 2026-09-18T22:14Z | EXP_span25ms_packA_gen | VALIDATED | | | | restore after LtzCal sync mis-wrote AsymRm status |
| 2026-09-18T22:13Z | EXP_span25ms_packA_preinh | FAIL | | | | sync gate fail acc=4 ok=1 |
| 2026-09-18T21:52Z | EXP_span25ms_packA_gen | FAIL | | | | sync gate fail acc=3 ok=0 |
| 2026-09-18T21:36Z | EXP_span100ms_packC_preinh_C1e9 | DEFERRED_PARENT_FAIL | | | | DEFERRED_PARENT_FAIL: packA parent ARTIFACT_KEEP (soft-cold mid flat) |
| 2026-09-18T21:36Z | EXP_span100ms_packC_gen | DEFERRED_PARENT_FAIL | | | | DEFERRED_PARENT_FAIL: packA parent ARTIFACT_KEEP (soft-cold mid flat) |
| 2026-09-18T21:36Z | EXP_span100ms_packB_preinh_C1e9 | DEFERRED_PARENT_FAIL | | | | DEFERRED_PARENT_FAIL: packA parent ARTIFACT_KEEP (soft-cold mid flat) |
| 2026-09-18T21:36Z | EXP_span100ms_packB_gen | DEFERRED_PARENT_FAIL | | | | DEFERRED_PARENT_FAIL: packA parent ARTIFACT_KEEP (soft-cold mid flat) |
| 2026-09-18T21:36Z | EXP_span50ms_packC_preinh_C1e9 | DEFERRED_PARENT_FAIL | | | | DEFERRED_PARENT_FAIL: packA parent ARTIFACT_KEEP (soft-cold mid flat) |
| 2026-09-18T21:36Z | EXP_span50ms_packC_gen | DEFERRED_PARENT_FAIL | | | | DEFERRED_PARENT_FAIL: packA parent ARTIFACT_KEEP (soft-cold mid flat) |
| 2026-09-18T21:36Z | EXP_span50ms_packB_preinh_C1e9 | DEFERRED_PARENT_FAIL | | | | DEFERRED_PARENT_FAIL: packA parent ARTIFACT_KEEP (soft-cold mid flat) |
| 2026-09-18T21:36Z | EXP_span50ms_packB_gen | DEFERRED_PARENT_FAIL | | | | DEFERRED_PARENT_FAIL: packA parent ARTIFACT_KEEP (soft-cold mid flat) |
| 2026-09-18T21:35Z | EXP_span25ms_packC_preinh_C1e9 | VALIDATED_CLONE | | | | phase9 packC; thr=0.004686425; acc=8; ok_audit=1 |
| 2026-09-18T21:15Z | EXP_span25ms_packB_preinh_C1e9 | VALIDATED_CLONE | | | | phase9 packB; thr=0.004686425; acc=8; ok_audit=1 |
| 2026-09-18T20:55Z | EXP_span25ms_packC_gen | VALIDATED_CLONE | | | | phase9 packC; thr=0.006994845; acc=8; ok_audit=1 |
| 2026-09-18T20:35Z | EXP_span25ms_packB_gen | VALIDATED_CLONE | | | | phase9 packB; thr=0.006994845; acc=8; ok_audit=1 |
| 2026-09-18T20:14Z | EXP_span100ms_fast_preinh_C1e9 | BLOCKED_FS | | | | blocked: FS25 FAIL_ROOTCAUSE; no FS×5 |
| 2026-09-18T20:14Z | EXP_span100ms_fast_C1e9 | BLOCKED_FS | | | | blocked: FS25 FAIL_ROOTCAUSE; no FS×5 |
| 2026-09-18T20:14Z | EXP_span50ms_fast_preinh_C1e9 | BLOCKED_FS | | | | blocked: FS25 FAIL_ROOTCAUSE; no FS×5 |
| 2026-09-18T20:14Z | EXP_span25ms_fast_preinh_C1e9 | BLOCKED_FS | | | | blocked: FS25 FAIL_ROOTCAUSE; no FS×5 |
| 2026-09-18T20:14Z | EXP_span100ms_packA_preinh | ARTIFACT_KEEP | | | | ARTIFACT_KEEP: soft-cold Need=0 L≡gold; ltz mid flat tiprmin+TipR86e6; gold kept |
| 2026-09-18T20:14Z | EXP_span100ms_packA_gen | ARTIFACT_KEEP | | | | ARTIFACT_KEEP: soft-cold Need=0 L≡gold; ltz mid flat tiprmin+TipR86e6; gold kept |
| 2026-09-18T20:14Z | EXP_span50ms_packA_preinh | ARTIFACT_KEEP | | | | ARTIFACT_KEEP: soft-cold Need=0 L≡gold; ltz mid flat tiprmin+TipR86e6; gold kept |
| 2026-09-18T20:14Z | EXP_span50ms_packA_gen | ARTIFACT_KEEP | | | | ARTIFACT_KEEP: soft-cold Need=0 L≡gold; ltz mid flat tiprmin+TipR86e6; gold kept |
| 2026-09-18T19:01Z | EXP_span25ms_packA_preinh | VALIDATED | | | | verdict=REPRO_OK_QUALITY L=`15 13 8 1` thr=0.01241355 fires=`10000000` |
| 2026-09-18T18:19Z | EXP_span50ms_packA_gen | FAIL | | | | verdict=REPRO_FAIL |
| 2026-09-18T14:55Z | EXP_span25ms_packA_preinh | FAIL | | | | verdict=REPRO_FAIL |
| 2026-09-18T12:47Z | EXP_span25ms_packA_gen | VALIDATED | | | | verdict=REPRO_OK_EXACT L=`15 12 8 1` thr=0.03758895 fires=`10000000` |
| 2026-09-18T11:09Z | EXP_span25ms_packA_gen | FAIL | | | | verdict=REPRO_FAIL |
| 2026-09-18T09:15Z | EXP_span25ms_fast_C1e9 | FAIL_ROOTCAUSE | | | | train exited_need1 Need=1 r1 |

## Wave 2 run log

| utc | exp_id | status | L | thr | fires | notes |
|-----|--------|---------|---|-----|-------|-------|
| 2026-09-17T20:19Z | EXP_br480_preinh250_tiprmin | FAIL | | | | train exited_need1 r1 |
| 2026-09-17T18:14Z | EXP_br480_nextseginh_tiprmin | FAIL | | | | train exited_need1 r1 |
| 2026-09-17T16:04Z | EXP_br480_tiprmin | FAIL | | | | train exited_need1 r1 |
| 2026-09-17T14:02Z | EXP_br_span100_packC_gen_C1e9 | VALIDATED_CLONE | | | | matrix-only packC; thr=0.007181835; acc=8; ok_audit=1 |
| 2026-09-17T13:56Z | EXP_br_span100_packB_gen_C1e9 | VALIDATED_CLONE | | | | matrix-only packB; thr=0.007181835; acc=8; ok_audit=1 |
| 2026-09-17T13:49Z | EXP_br_span100_packB_gen_C1e9 | FAIL | | | | matrix-only packB; thr=1.0; acc=6; ok_audit=0 |
| 2026-09-17T13:44Z | EXP_br_span100_packC_nextseginh_C1e9 | DEFERRED_PARENT_FAIL | | | | parent FAIL EXP_br_span100_packA_nextseginh_C1e9 |
| 2026-09-17T13:44Z | EXP_br_span100_packB_nextseginh_C1e9 | DEFERRED_PARENT_FAIL | | | | parent FAIL EXP_br_span100_packA_nextseginh_C1e9 |
| 2026-09-17T13:44Z | EXP_br_span50_packC_nextseginh_C1e9 | VALIDATED_CLONE | | | | matrix-only packC; thr=0.0456422; acc=8; ok_audit=1 |
| 2026-09-17T13:39Z | EXP_br_span50_packB_nextseginh_C1e9 | VALIDATED_CLONE | | | | matrix-only packB; thr=0.0456422; acc=8; ok_audit=1 |
| 2026-09-17T13:34Z | EXP_br_span25_packC_nextseginh_C1e9 | VALIDATED_CLONE | | | | matrix-only packC; thr=0.0475917; acc=8; ok_audit=1 |
| 2026-09-17T13:30Z | EXP_br_span25_packB_nextseginh_C1e9 | VALIDATED_CLONE | | | | matrix-only packB; thr=0.0475917; acc=8; ok_audit=1 |
| 2026-09-17T13:26Z | EXP_br_span100_packC_preinh_C1e9 | VALIDATED_CLONE | | | | matrix-only packC; thr=0.0203054; acc=8; ok_audit=1 |
| 2026-09-17T13:21Z | EXP_br_span100_packB_preinh_C1e9 | VALIDATED_CLONE | | | | matrix-only packB; thr=0.0203054; acc=8; ok_audit=1 |
| 2026-09-17T13:15Z | EXP_br_span50_packC_preinh_C1e9 | VALIDATED_CLONE | | | | matrix-only packC; thr=0.03008405; acc=8; ok_audit=1 |
| 2026-09-17T13:10Z | EXP_br_span50_packB_preinh_C1e9 | VALIDATED_CLONE | | | | matrix-only packB; thr=0.03008405; acc=8; ok_audit=1 |
| 2026-09-17T13:06Z | EXP_br_span25_packC_preinh_C1e9 | VALIDATED_CLONE | | | | matrix-only packC; thr=0.05171075; acc=8; ok_audit=1 |
| 2026-09-17T13:03Z | EXP_br_span25_packB_preinh_C1e9 | VALIDATED_CLONE | | | | matrix-only packB; thr=0.05171075; acc=8; ok_audit=1 |
| 2026-09-17T12:59Z | EXP_br_span100_packC_gen_C1e9 | FAIL | | | | matrix-only packC; thr=1.0; acc=6; ok_audit=0 |
| 2026-09-17T12:56Z | EXP_br_span100_packB_gen_C1e9 | FAIL | | | | matrix-only packB; thr=1.0; acc=5; ok_audit=0 |
| 2026-09-17T12:53Z | EXP_br_span50_packC_gen_C1e9 | VALIDATED_CLONE | | | | matrix-only packC; thr=0.06440315; acc=8; ok_audit=1 |
| 2026-09-17T12:50Z | EXP_br_span50_packB_gen_C1e9 | VALIDATED_CLONE | | | | matrix-only packB; thr=0.06440315; acc=8; ok_audit=1 |
| 2026-09-17T12:46Z | EXP_br_span25_packC_gen_C1e9 | VALIDATED_CLONE | | | | matrix-only packC; thr=0.07179975; acc=8; ok_audit=1 |
| 2026-09-17T12:41Z | EXP_br_span25_packB_gen_C1e9 | VALIDATED_CLONE | | | | matrix-only packB; thr=0.07179975; acc=8; ok_audit=1 |

## Wave 1 run log

| UTC | exp_id | verdict | L | thr | fires | notes |
|-----|--------|---------|---|-----|-------|-------|
| 2026-09-17T09:30Z | EXP_br_span100_packA_nextseginh_C1e9 | FAIL | `1 1 1 1` | | | soft-cold no L growth |
| 2026-09-17T08:52Z | EXP_br_span100_packA_gen_C1e9 | VALIDATED | | | | verdict=REPRO_OK_EXACT L=`25 21 11 1` thr=0.007181835 fires=`10000000` |
| 2026-09-17T08:27Z | EXP_br_span100_packA_nextseginh_C1e9 | FAIL | | | | train exited_need1 r1 |
| 2026-09-17T06:27Z | EXP_br_span50_packA_nextseginh_C1e9 | VALIDATED | | | | verdict=REPRO_OK_QUALITY L=`13 11 6 1` thr=0.0412798 fires=`10000000` |
| 2026-09-17T03:21Z | EXP_br_span25_packA_nextseginh_C1e9 | VALIDATED | | | | verdict=REPRO_OK_EXACT L=`13 11 7 1` thr=0.0475917 fires=`10000000` |
| 2026-09-17T01:34Z | EXP_br_span100_packA_preinh_C1e9 | VALIDATED | | | | verdict=REPRO_OK_EXACT L=`22 18 11 1` thr=0.0203054 fires=`10000000` |
| 2026-09-16T23:17Z | EXP_br_span50_packA_preinh_C1e9 | VALIDATED | | | | verdict=REPRO_OK_EXACT L=`13 11 6 1` thr=0.03008405 fires=`10000000` |
| 2026-09-16T21:32Z | EXP_br_span25_packA_preinh_C1e9 | VALIDATED | | | | verdict=REPRO_OK_EXACT L=`7 6 4 1` thr=0.05171075 fires=`10000000` |
| 2026-09-16T18:22Z | EXP_br_span25_packA_preinh_C1e9 | FAIL | | | | train exited_need1 r1 |
| 2026-09-16T15:35Z | EXP_br_span50_packA_gen_C1e9 | VALIDATED | | | | verdict=REPRO_OK_EXACT L=`13 11 6 1` thr=0.06440315 fires=`10000000` |
| 2026-09-16T13:51Z | EXP_br_span25_packA_gen_C1e9 | VALIDATED | | | | stamp-from-repro REPRO_OK_EXACT L=`13 11 7 1` thr=0.07179975 |

## Links

- [`EXPERIMENTS.md`](EXPERIMENTS.md) — tabular HEAD slice (PASS/FAIL/NOT_RETESTED); PHASE12 badges below are historical reference, not HEAD verdict
- [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md) — HEAD PASS only
- [`SelectivityBranch/PHASE8_SHORTSPAN.md`](SelectivityBranch/PHASE8_SHORTSPAN.md)
- [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) · [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md) · [`PHASE11_COVERAGE.md`](PHASE11_COVERAGE.md)
- [`_repro/REPRO_COLD_RESULT.md`](_repro/REPRO_COLD_RESULT.md) · [`_repro/REPRO_COLD_INVESTIGATION.md`](_repro/REPRO_COLD_INVESTIGATION.md)

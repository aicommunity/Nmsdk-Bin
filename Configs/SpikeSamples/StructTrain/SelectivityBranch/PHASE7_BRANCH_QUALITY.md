# PHASE7 — Branch trainer quality

Исследование качества `NNeuronTimeLearnerBranch`: late_fp / per_stim demote на каноне @480 мс; short-span после починки Test wiring.

Критерии кода **не** меняем — см. [`../SUCCESSFUL_EXPERIMENTS.md`](../SUCCESSFUL_EXPERIMENTS.md) §«Слои ворот».  
Процедурная цель: `ok_audit` + last-pulse + `ok_single` (без late_fp/per_stim); ideally ≥7/8, цель 8/8.

Reference: [`../CAMPAIGN_REPORT_2026-08_09.md`](../CAMPAIGN_REPORT_2026-08_09.md) §3, [`../AUDIT_REPORT.md`](../AUDIT_REPORT.md), PHASE5/6 hygiene.

## Принципы

- Пересчёт устаревших CSV / сломанных Class — **в тех же корнях**.
- Подбор параметров — **новые клоны** под `SelectivityBranch/EXP_*` (исторический Branch не cold-reset).
- Конфиги не удаляем; FAIL сохраняем со ссылками.
- Branch: **один** дендрит, tip = `Dendrite1_{L[i]}`; silent gap по **`soma_amp_sum`** (`ltz_potential_max` в CSV часто 0). Silent thr для Branch ≈ **1.0** (пики ~0.05–0.11), не 0.05 как у PhaseA.

## Wave 0 — hygiene + recalculate (2026-09-13)

| EXP | Action | ok_audit | acc_L/S | late_fp | response_quality | fires | last-pulse |
|-----|--------|----------|---------|---------|------------------|-------|------------|
| [`TimeNeuronTimeLearnerBranch`](../TimeNeuronTimeLearnerBranch/) | Test re-run | 0 | 6/4 | 2 | per_stim | `10100010` | yes `t_rel≈0.861` |
| [`…_NextSegInh`](../TimeNeuronTimeLearnerBranch_NextSegInh/) | Test re-run | 0 | 7/3 | 4 | per_stim | `10000010` | yes `≈0.898` |
| [`…_PreInh250`](../TimeNeuronTimeLearnerBranch_PreInh250/) | Test re-run | 0 | 7/4 | 3 | per_stim | `10000010` | yes `≈0.974` |
| [`BranchFastSpan/…25`](../SelectivityLtzCalibrate/BranchFastSpan/EXP_branch_span25_gen/) | fix BranchBranch + re-run | 0 | 1/1 | 0 | per_stim | fire_all | `t_rel≈0.153` / end `0.025` |
| [`BranchFastSpan/…100`](../SelectivityLtzCalibrate/BranchFastSpan/EXP_branch_span100_gen/) | fix + re-run | 0 | 1/1 | 0 | per_stim | fire_all | `≈0.159` / end `0.10` |

Delta vs audit 2026-09-10: **канон trio без изменений** (demote confirmed). FastSpan после починки Class: честный **fire_all/per_stim**. CSV: `results_pre_recalc_20260913.csv` / `results_pre_fix.csv`.

`rg BranchBranch` → **0**. Скрипт [`../SelectivityLtzCalibrate/scripts/patch_test_model_branch.py`](../SelectivityLtzCalibrate/scripts/patch_test_model_branch.py) — idempotent + repair.

## Wave 1 — диагноз @480 (клоны)

| EXP | Результат |
|-----|-----------|
| [`EXP_br480_diag_silent`](EXP_br480_diag_silent/) | thr=1.0 silent; soma tgt=`0.0730`, foil_max=`0.107` (t6/t7) → **gap −0.034** |
| [`EXP_br480_diag_midthr`](EXP_br480_diag_midthr/) | mid без TipR ≈ baseline demote |

**Вердикт:** доминирует **amp/TipR skew** (Done TipR `~4e6 … 4e8`), не late-window и не mid-pattern analyzer. Peak×0.99 thr сидит в зоне, где foils 6/7 выше цели → per_stim/late_fp. Чистый mid-thr **не** достаточен.

## Wave 2 — param clones @480

| EXP | TipR / Rmin / thr | Gate |
|-----|-------------------|------|
| [`EXP_br480_base_recalc`](EXP_br480_base_recalc/) | Done | 6/8 demote (как канон) |
| [`EXP_br480_midthr`](EXP_br480_midthr/) / [`thr_only`](EXP_br480_thr_only/) | Done + mid `0.07258` | demote, per_stim |
| [`EXP_br480_tiprmin`](EXP_br480_tiprmin/) | TipR@Rmin `2e7×3+8.6e7`, Rmin=`2e7`, mid **`0.05149`** | **`ok_audit=1`, 8/8 selective, ok_single, last-pulse `t_rel≈0.491`**, fires=`10000000` |

Silent tiprmin: gap **+1.3e-3** (tgt soma `0.0522` > foil_max `0.0508`).  
**ltz_frac retrain:** не потребовался — TipR@Rmin + mid-thr на Done Test достаточно.

## Wave 3 — NextSegInh / PreInh на рецепте tiprmin

| EXP | Gate |
|-----|------|
| [`EXP_br480_nextseginh_tiprmin`](EXP_br480_nextseginh_tiprmin/) | **8/8** ok_audit, last-pulse `t_rel≈0.487`, thr mid=`0.036298` |
| [`EXP_br480_preinh250_tiprmin`](EXP_br480_preinh250_tiprmin/) | **7/8** ok_audit, ok_single, last-pulse `t_rel≈0.498`, fires=`10001000` (1 FP) |

NextSeg/PreInh **не** нужны для 8/8 gen; tiprmin переносится на NextSegInh. Preinh250 — partial (negative silent gap остаётся на t4).

## Wave 4 — short-span

| EXP | Status |
|-----|--------|
| BranchFastSpan 25/100 (корни) | Wave0: fire_all после fix Class |
| [`EXP_br_span25_tiprmin`](EXP_br_span25_tiprmin/) | Test-only TipR@Rmin: silent gap **−8.6e-3**; gate **FAIL** partial_FA/`mixed` fires=`11110101` |
| span50/100 C1e9 retrain / AsymRmLtzCalBranch stall×6 | **deferred** — нужен Train с C1e9/hygiene, не cold-reset stall |

TipR@Rmin **не** переносится на short-span Done без retrain (в отличие от @480).

## PHASE10 T1 — preinh250 TipR Done/partial

Clone [`EXP_br480_preinh250_tiprmin_phase10_tipr`](EXP_br480_preinh250_tiprmin_phase10_tipr/): Done TipR (PreInh250 skew) и partial → оба `ok_audit=0` (per_stim). Parent **7/8** retained. See `PHASE10_MID_TIPR_NOTE.md`. Helper: [`scripts/phase10_br480_tipr_retry.py`](scripts/phase10_br480_tipr_retry.py).

## Рецепт PASS (Branch @480)

1. TipR@Rmin `2e7 2e7 2e7 8.6e7` + tip ExcSynapse R на `Dendrite1_{L}`  
2. `ResistanceMin=2e7`  
3. Silent thr=`1.0` → mid thr по **soma_amp_sum** (tgt ↔ max foil below tgt)  
4. `UseFixedLTZThreshold=1`, clean Test  
5. Gate: ok_audit + last-pulse + ok_single; цель 8/8

## Антирегрессия

- Не cold-reset Done канона Branch / AsymRm PHASE5 PASS.
- Канон trio остаётся demoted (без tiprmin) — эталон «до рецепта».
- AsymRmLtzCalBranch stall ×6 — не перезаписывать.

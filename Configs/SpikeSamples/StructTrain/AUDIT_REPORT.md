# StructTrain audit report

Первичный срез: **2026-09-10**. Пересчёт GATE (metrics-from-CSV): **2026-09-13** после PHASE5–7; **2026-09-14** PHASE9 D0 (incl. PHASE8 C1e9); **2026-09-14 T0** (+P1–P3 C1e9).  
Scope: `Selectivity*` + `TimeNeuronTimeLearner*` under [`StructTrain/`](.).  
Excluded: `XOR/`, `SpikeAnsTrainer/`, `SpikeTrainer/`, `RTlibs/`.

Термины (RU): см. глоссарий в [`CAMPAIGN_REPORT_2026-08_09.md`](CAMPAIGN_REPORT_2026-08_09.md). Кратко: **ответ/спайк** на выходе нейрона (не «стрельба»); **алгоритм обучения** `NNeuronTimeLearner` / Branch = **обучение на одном дендрите** (сегменты импульсов); `fire_all` = ответ на все 8 проб.

Canonical metrics: [`scripts/selectivity_metrics.py`](scripts/selectivity_metrics.py)  
- `ok_legacy` — historical gate (`match` / in-window only); late на чужом **не** FA; PASS при acc≥4  
- `ok_strict` — late_fp/late_fn counted as errors; nontarget ok только при тишине in-window **и** late; PASS при acc_strict≥4  
- `ok_audit` — `ok_strict` ∧ `response_quality=ok_single` ∧ `n=8` (**не** требует 8/8; partial_FA 4–6/8 может пройти)  
- **Last-pulse (реестр)** — target `t_rel ≥ 0.8·pattern_end`; поверх audit, см. [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md)  
Analyzer: mid-pattern spike не ставит `neuron_fired` (`kMinStimForInWindowFire` в `NPatternResponseAnalyzer`).  
Artifacts: [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv) (live), [`archive/AUDIT_GATE_RECOMPUTE_20260914T171405Z_phase9_tail.csv`](archive/AUDIT_GATE_RECOMPUTE_20260914T171405Z_phase9_tail.csv), [`AUDIT_GATE_RECOMPUTE_2026-09-13.csv`](AUDIT_GATE_RECOMPUTE_2026-09-13.csv), [`AUDIT_GATE_RECOMPUTE_2026-09-10.csv`](AUDIT_GATE_RECOMPUTE_2026-09-10.csv), [`AUDIT_STRUCTURE_2026-09-10.csv`](AUDIT_STRUCTURE_2026-09-10.csv), [`LAYOUT.md`](LAYOUT.md), [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md), [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md), [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md).  
Полная таблица слоёв / ошибок на чужом — в SUCCESSFUL_EXPERIMENTS §«Слои ворот». Пороги `ok_audit` **не** ужесточались.

## Layout

All experiment roots now use `<root>/{Train,Test}` (+ optional `Test_<tag>/`).  
Merged sibling `*Test` TimeNeuron folders into Train/Test pairs. PhaseA EXP01/02/06 gained `Train/` from EXP00 (`TRAIN_SOURCE.txt`).

## Gate recompute (2026-09-14 PHASE9 T0, 154 Test)

| Metric | Count |
|--------|------:|
| `ok_audit=1` | 64 |
| rows | 154 |

Δ vs PHASE9 D0 (132 / 43): **+21** P1–P3 C1e9 (Branch B/C ×12 + AsymRm preinh B/C ×6 + NextSeg ×3) → 64 `ok_audit`. Архив T0: [`archive/AUDIT_GATE_RECOMPUTE_20260914T171405Z_phase9_tail.csv`](archive/AUDIT_GATE_RECOMPUTE_20260914T171405Z_phase9_tail.csv). D0: [`archive/AUDIT_GATE_RECOMPUTE_20260914T064705Z_phase9_d0.csv`](archive/AUDIT_GATE_RECOMPUTE_20260914T064705Z_phase9_d0.csv).

### `ok_audit` PASS

Полный реестр с рычагами и ссылками Train/Test/CSV: [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md)  
(**last-pulse** обязателен для живого реестра: target `t_rel ≥ 0.8·pattern_end`).

| Experiment | acc_legacy | Примечание |
|------------|------------|------------|
| PhaseA EXP00 / EXP01 / EXP02 / EXP06 | 4–6 | `t_rel≈pattern_end` (~0.48 с) |
| PSI EXP01, EXP14–15, EXP21, EXP31–35 | 4–6 | |
| `TimeNeuronTimeLearner/Test` | 4 | |
| PHASE5 AsymRm packA gen+preinh, B/C gen @25/50/100 | **8** | C1e9 + TipR@Rmin — [`PHASE5_SPAN50_100.md`](SelectivityAsymRm/PHASE5_SPAN50_100.md) |
| AsymRmLtzCal twin packA gen @25/50/100 | **8** | в реестре (после PHASE5 Wave1) |
| PHASE6 `Phase6/EXP_480_*` (tiprmin / thr_only / preinh / twin) | **7** | 2026-09-13; last-pulse; не 8/8 — см. [`PHASE6_480_RECIPE.md`](SelectivityPhaseA/PHASE6_480_RECIPE.md) |
| PHASE7 `SelectivityBranch/EXP_br480_tiprmin` (+ nextseginh) | **8** | TipR@Rmin + mid soma; last-pulse — [`PHASE7_BRANCH_QUALITY.md`](SelectivityBranch/PHASE7_BRANCH_QUALITY.md) |
| PHASE7 `EXP_br480_preinh250_tiprmin` | **7** | ok_audit; 1 FP |
| PHASE8 `SelectivityBranch/EXP_br_span*_packA_*_C1e9` ×6 | **8** | TipR@Rmin (span100 gen: Done TipR); last-pulse — [`PHASE8_SHORTSPAN.md`](SelectivityBranch/PHASE8_SHORTSPAN.md) |
| PHASE9 P1 Branch pack B/C C1e9 ×12 | **8** | [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) |
| PHASE9 P2 AsymRm pack B/C preinh C1e9 ×6 | **8** | |
| PHASE9 P3 Branch NextSeg short C1e9 ×3 | **8** | |

**Demote (2026-09-11):** ранний `packA_gen` / LtzCal twin с `t_rel≈0.001` (нет last-pulse) — снят с реестра. **Restore (2026-09-11 вечер):** `SelectivityAsymRm/EXP_span25ms_packA_gen` после C1e9+EstDelay+Rsyn floor — `ok_audit=1`, 8/8 selective, last-pulse. **Twins packA gen @25/50/100 — в реестре.** См. [`DIAG_LAST_PULSE_span25_packA.md`](SelectivityAsymRm/DIAG_LAST_PULSE_span25_packA.md).

### False successes (legacy PASS, audit FAIL)

| Experiment | legacy | strict | late_fp | response_quality | max_spikes |
|------------|--------|--------|---------|------------------|------------|
| `TimeNeuronTimeLearnerBranch/Test` | 6/8 | 1 | 2 | **per_stim** | 6 |
| `…Branch_NextSegInh/Test` | 7/8 | 0 | 4 | **per_stim** | 6 |
| `…Branch_PreInh250/Test` | 7/8 | 1 | 3 | **per_stim** | 6 |

Legacy 7/8 на Branch (обучение на одном дендрите): late-ответ на отвлекающих считался «тишиной» (`match=1`) плюс multi-spike / per-stim. **Demoted.** Снято tiprmin-клонами PHASE7 (`EXP_br480_*_tiprmin`); **канон trio всё ещё demoted** как эталон «до рецепта».

## Span 25 ms (исторический срез 2026-09-10 vs live)

| EXP (AsymRm) | Исторический GATE 2026-09-10 | Live (после PHASE5) |
|--------------|------------------------------|---------------------|
| `EXP_span25ms_packA_gen` | ok_audit=1 (early затем restore) | **8/8** selective, last-pulse |
| `EXP_span25ms_packA_preinh` | fire_all | **8/8** (C1e9 recipe) — SUCCESSFUL / PHASE5 |
| `EXP_span25ms_packB_*` / `packC_*` | fire_all | **gen 8/8**; preinh B/C — deferred (RECIPE_COVERAGE) |
| FastSpan 25 ms (non-ts10k) | per_stim / silent | без tiprmin-кампании (orphan) |

**Verdict (исторический):** membrane/dendrite timing fit alone не обобщался. **Superseded by PHASE5:** C1e9 + TipR@Rmin + silent mid-thr даёт 8/8 на gen A/B/C и A preinh @25/50/100.

## Burst / per-stim morphology

- **per_stim** (ответ на большинство стимулов паттерна): ~48 EXP with ≥1 such trial — dominant pathology; likely tip R / synaptic drive / short L.  
- **burst** (ISI≤5 мс packs): 8 EXP — often co-occurs with per_stim (`mixed`).  
- Both force `ok_audit=0` even if class labels look selective.

Analyzer now keeps the trial open to the end of Post/Late windows and logs `neuron_spike_count`, `neuron_spike_times`, `response_class` (see PulseLib docs).

## Structural FAIL notes

See [`AUDIT_FINDINGS.md`](AUDIT_FINDINGS.md). Remaining FAILs are mostly incomplete CSV (`n≠8`) or missing SelectivityLog on LtzCalibrate stalls — not missing neurons in live Train models after layout migration.

## Scripts

| Path | Role |
|------|------|
| `scripts/selectivity_metrics.py` | dual-gate + morphology |
| `scripts/audit_structtrain.py` | Train/Test / wiring inventory |
| `scripts/rerun_all_tests.sh` | Test-only batch (`PARALLEL`, `PRIORITY_ONLY`) |
| campaign `evaluate_selectivity_csv.py` | thin wrappers → metrics module |

## Follow-ups (out of this audit)

- Re-run remaining `n≠8` with longer wall time (AsymRm 50/100 мс often timeout at 150 s).  
- Retrain only after fixing per-stim / amp pathologies (not done here).  
- Consider tightening audit threshold above soft `acc≥4`.

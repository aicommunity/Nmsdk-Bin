# StructTrain audit report (2026-09-10)

Scope: `Selectivity*` + `TimeNeuronTimeLearner*` under [`StructTrain/`](.).  
Excluded: `XOR/`, `SpikeAnsTrainer/`, `SpikeTrainer/`, `RTlibs/`.  
No retrain — Test-only re-runs + offline metrics.

Canonical metrics: [`scripts/selectivity_metrics.py`](scripts/selectivity_metrics.py)  
- `ok_legacy` — historical gate (`match` / in-window only)  
- `ok_strict` — late_fp/late_fn counted as errors  
- `ok_audit` — `ok_strict` ∧ `response_quality=ok_single` ∧ `n=8`  
Artifacts: [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv), [`AUDIT_STRUCTURE_2026-09-10.csv`](AUDIT_STRUCTURE_2026-09-10.csv), [`LAYOUT.md`](LAYOUT.md).

## Layout

All experiment roots now use `<root>/{Train,Test}` (+ optional `Test_<tag>/`).  
Merged sibling `*Test` TimeNeuron folders into Train/Test pairs. PhaseA EXP01/02/06 gained `Train/` from EXP00 (`TRAIN_SOURCE.txt`).

## Gate recompute (112 Test)

| Metric | Count |
|--------|------:|
| `ok_legacy=1` | 19 |
| `ok_strict=1` | 18 |
| `ok_audit=1` | 16 |
| `response_quality=per_stim` | 40 EXP |
| `response_quality=mixed` (burst∪per_stim) | 8 EXP |
| `n≠8` (incomplete / timeout) | 41 |

### `ok_audit` PASS

| Experiment | acc_legacy |
|------------|------------|
| `SelectivityAsymRm/EXP_span25ms_packA_gen` | 6 |
| `SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen` | 6 |
| PhaseA EXP00 / EXP01 / EXP02 / EXP06 | 4–6 |
| PSI EXP01, EXP14–15, EXP21, EXP31–35 | 4–6 |
| `TimeNeuronTimeLearner/Test` | 4 |

### False successes (legacy PASS, audit FAIL)

| Experiment | legacy | strict | late_fp | response_quality | max_spikes |
|------------|--------|--------|---------|------------------|------------|
| `TimeNeuronTimeLearnerBranch/Test` | 6/8 | 1 | 2 | **per_stim** | 6 |
| `…Branch_NextSegInh/Test` | 7/8 | 0 | 4 | **per_stim** | 6 |
| `…Branch_PreInh250/Test` | 7/8 | 1 | 3 | **per_stim** | 6 |

Legacy 7/8 on Branch was driven by late nontarget spikes counted as correct silence (`match=1`) plus multi-spike / per-stim morphology. **Demoted.**

## Span 25 ms + timing-parameter fit

| EXP (AsymRm) | n | ok_audit | mode / notes |
|--------------|---|----------|--------------|
| `EXP_span25ms_packA_gen` | 8 | **1** | selective 6/8, single-spike |
| `EXP_span25ms_packA_preinh` | 8 | 0 | fire_all + per_stim |
| `EXP_span25ms_packB_*` | 8 | 0 | fire_all; B_gen also burst |
| `EXP_span25ms_packC_*` | 8 | 0 | fire_all + per_stim |
| FastSpan 25 ms (non-ts10k) | 8 | 0 | per_stim / silent-ts10k |

**Verdict:** membrane/dendrite timing fit did **not** generalize across 25 мс packs. The one audit PASS (`packA_gen`) is real under strict+single, but siblings are fire_all / per-stim — not evidence that temporal-parameter search systematically produces selectivity.

## Burst / per-stim morphology

- **per_stim** (answer to most pattern spikes): ~48 EXP with ≥1 such trial — dominant pathology; likely tip R / synaptic drive / short L.  
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

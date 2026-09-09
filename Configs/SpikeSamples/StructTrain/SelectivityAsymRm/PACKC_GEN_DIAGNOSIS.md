# Pack C gen diagnosis (2026-09-08)

Learner: **`NNeuronTimeLearner`** (not Branch). Done requires `AllDendritesSynced() ∧ AllSynapsesNormalized()` then CalibrateLtz (`NNeuronTimeLearner.cpp` `EndOfLearning`).

Sources: `analyze_train_stall.py --json` → `packc_stall_diag.json`; Train `Parameters_00.xml`; Done siblings Pack C preinh (read-only).

## Snapshot

| EXP | Need | FixedLTZ | L | EnableDebug | Overall blocker |
|-----|------|----------|---|-------------|-----------------|
| `EXP_span50ms_packC_gen` | 1 | 0.0115 cold | `11 9 7 1` (= L_ref) | 1 | `AMP_OSCILLATION` / feas `AMP_PENDING` |
| `EXP_span100ms_packC_gen` | 1 | 0.0115 cold | `20 17 10 1` (= L_ref) | 1 | `AMP_OSCILLATION` / feas `AMP_PENDING` |

`all_non_ref_sync_ok=true` for both (Python stall view). Cold FixedLTZ → CalibrateLtz never ran.

## Per-dendrite (span50 gen)

| d | L | sync_ok | tip_R | amp_dt | no_improve | stall blocker |
|---|---|---------|-------|--------|------------|---------------|
| 0 | 11 | yes | ~9.82e7 | ~4.8e-6 | 0 | DONE |
| 1 | 9 | yes | ~1.07e8 | ~1.8e-4 | **44** | **AMP_OSCILLATION** |
| 2 | 7 | yes | **1e11 (=ResistanceMax)** | **-35.4** | 39 | **AMP_PENDING** (pathological) |
| 3 (ref) | 1 | n/a | 8.6e7 | ~0.045 | 0 | DONE |

## Per-dendrite (span100 gen)

| d | L | sync_ok | tip_R | amp_dt | no_improve | stall blocker |
|---|---|---------|-------|--------|------------|---------------|
| 0 | 20 | yes | ~2.23e6 | **-0.0075** | 1 | AMP_PENDING |
| 1 | 17 | yes | ~1.78e7 | ~0.0018 | **99** | **AMP_OSCILLATION** |
| 2 | 10 | yes | ~5.43e7 | ~6.5e-6 | 0 | DONE |
| 3 (ref) | 1 | n/a | 8.6e7 | ~0.045 | 0 | DONE |

## Why EndOfLearning never fires

`AllSynapsesNormalized` fails while amp on non-ref dendrites is not settled (`|InitialSoma − MaxIterSomaAmp|` / SynapseStatus / tip not at dead_tip escape). Pathological **amp_dt≈−35** on span50 d2 with TipR pinned at **ResistanceMax** prevents stable normalize; span100 d1 hard OSC (`no_improve=99`) same class of amp stall.

Hypothesis ranking:

1. **H1 (confirmed primary):** pathological tip/amp_dt on ≥1 non-ref dendrite blocks synapse normalize → no CalibrateLtz.
2. **H2 (unlikely):** length sync false positive — L matches `l_reference`, non-ref sync_ok.
3. **H3 (not indicated yet):** C++ eps bug — no evidence without EnableDebug peak dumps after tip reset.
4. Preinh siblings are Done with calibrated FixedLTZ; gen TipR/Initial were previously seeded from preinh and then drifted under amp (span50 tip2 → Rmax).

## Chosen lever (single)

**Reset pathological TipR only** on whitelist Pack C gen (TipR ≥ 0.99×ResistanceMax and/or `|amp_dt| > 1`), set that dend TipR to median of healthy non-ref tips (same EXP), **do not** full TipR/Initial transplant from preinh. Then short amp `80 160` + `AMP_ABORT_HARD_OSC=1`.

Scripts: `scripts/reset_pathological_tip.py`, `scripts/finish_packC_gen_tip_reset_amp.sh`.

## Lever result (2026-09-08 evening) — FAIL

Applied TipR reset (span50 d1+d2; span100 d1) then `AMP_TRAIN_STEPS=80 160` + `AMP_ABORT_HARD_OSC=1`.

- Amp re-drove **span50 d2 TipR → ResistanceMax** with `amp_dt ≈ -5.9e4` (worse than −35).
- Both EXP still Need=1 / FixedLTZ cold 0.0115.
- Run aborted (wall time on T=160); **16 Done fingerprint unchanged**.
- Stall snapshot: `finish_packC_gen_tip_reset_amp_stall.json`.

**Defer:** tip reset alone does not stop pathological amp measurement on Pack C gen. Next requires C++/peak measurement audit or different algorithm — **not** another TipR transplant / short amp campaign.

## AmpDtAudit (копии `_ampaudit`, 2026-09-08)

Оригиналы `EXP_span{50,100}ms_packC_gen` **не** трогались. Клоны:

| EXP | Источник | Примечание |
|-----|----------|------------|
| `EXP_span50ms_packC_gen_ampaudit` | stuck Pack C gen 50 | EnableDebug=1; Project.ini EventsLogMode/DebugMode=1 |
| `EXP_span100ms_packC_gen_ampaudit` | stuck Pack C gen 100 | то же; NM hung после `phase -> Done` (убит после ~42 мин) |

C++ (`NNeuronTimeLearner.cpp`, только при EnableDebug + logger):

- `UpdateNormTraces` — `|amp_dt|>5`
- `ChangeSynapseResistanceStatus` — `|dt|>5`
- `MeasureMaxPotentialAndTime` — `currentsomaamp>10` или `>50×Initial`

Короткий train: `ADAPTIVE_TRAIN=0 TRAIN_T=80 AMP_TRAIN_STEPS=80` на копиях only. Fingerprint 16 Done: **OK**.

### События `AmpDtAudit` (span50 copy)

≥66 строк в `Train/run_console.log`. Пример (dend **2**, L=7):

```text
AmpDtAudit MeasureMaxPotentialAndTime: i=2 L=7 ... currentsomaamp=59278.5 MaxIterSomaAmp=59278.5 InitialSomaPotential=0.0423094
AmpDtAudit ChangeSynapseResistanceStatus: num=2 dt=-59278.5 ... r_old=2.42e6 → затем TipR=1e11 length_settled=1 ready_for_r_tune=1
AmpDtAudit UpdateNormTraces: i=2 amp_dt=-59278.5 TipR=1e11 PeakSeen=1 PeakLocked=1
```

**Вывод:** пик в окне PeakMeasure даёт чудовищный `MaxIterSomaAmp` при маленьком `Initial`; damped TipR при `|dt|≫1` гонит R к **ResistanceMax** — это и есть механизм H1 / tip-reset FAIL.

span100 copy: за T=80 до Done **0** строк `AmpDtAudit` (`|amp_dt|` в FinishTrainingIteration ~1e−2…0.045); `CalibrateFixedLTZ max=1.37e6` намекает на выбросы **вне** peak-окна / вне MaxIterSomaAmp.

### Fix (always-safe)

В `ChangeSynapseResistanceStatus`: если `|dt|>5` — **не** вызывать damped TipR update; `ResistanceStatus` не трогать; лог `AmpDtAudit skip TipR update`. Rebuild NeuroModelerConsole. Без TipR transplant.

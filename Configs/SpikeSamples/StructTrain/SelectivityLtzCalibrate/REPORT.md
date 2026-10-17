# SelectivityLtzCalibrate — отчёт

Кампания глубокого анализа структурного обучения на коротких ISI. Полный план: [ANALYSIS_structural_learning.md](ANALYSIS_structural_learning.md).

## Статус (2026-08-23, sprint close)

| Этап | Статус |
|------|--------|
| Sync pipeline (merge_train_model + inject in-place) | ✅ |
| Warm/smoke gate | ✅ — [REGRESSION.md](REGRESSION.md) |
| `verify_train_done.py` + fresh Model protocol | ✅ |
| Cold Bio baseline retrain | ➖ не gate |
| FastSpanLtzCal classic grid | 🟡 P1-soft — 6/6 fire_all (train not Done) |
| BranchFastSpan grid | 🟡 span25 **4/8** partial; span100 1/8 fire_all |
| Tier 0b classic C++ | ⏸ skipped (classic train stall) |
| A1 LTZ sweep + separability | ✅ |

## Regression (sync fix)

- Warm gate: golden → sync → test **5/8 + 6/8** (`verify_regression.py --mode warm`).
- Cold Bio retrain optional; не блокирует grid.

## Tier 0 classic (TimeLearner + D002)

Pilot span100: TRAIN_T 160/320/480 — train **не Done**, FixedLTZ=0.0115.

Grid (6 EXP, `-t 160`): все **fire_all**, FixedLTZ cold. Root cause: classic learner не завершает structural sync на D002 в batch.

Separability: offline ISI template **8/8**; LTZ sweep span25 preinh до **6/8** при ручном thr.

## Branch (TimeNeuronTimeLearnerBranch + D002)

Train **Done** + AutoCalibrate на обоих EXP. Test: span25 gen **4/8** (partial), span100 gen 1/8 fire_all.

## AsymRmLtzCal (2026-08-27 — repair 2026-08-28)

Repair protocol (parity setup + cold reset + TRAIN_T 80→160→320): **1/6 Done+calibrated** — `span25 gen` FixedLTZ=**0.0885**, test **6/8 gate PASS**. Остальные 5/6 stall (amp-sync). §4 fallback — без эффекта. См. [`AsymRmLtzCal/REPORT.md`](AsymRmLtzCal/REPORT.md).

## Backlog

- Classic train stall на D002 (GUI vs batch, EndOfLearning conditions).
- B1 offline dual-thr / FP diagnostics vs distractors (`MatchMode=1` = ISI oracle — **не** neuron gate).
- Branch span100 readout; amp-eq / NextSegInh из Branch REPORT.
- B3, C1–C4, Tier D — см. JOURNAL.

## Data hygiene

Runtime артефакты не коммитятся — см. [.gitignore](.gitignore). Источник весов: **Train/Parameters_00.xml**.

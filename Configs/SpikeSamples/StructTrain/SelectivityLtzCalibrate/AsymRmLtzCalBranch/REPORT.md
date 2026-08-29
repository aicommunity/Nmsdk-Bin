# AsymRmLtzCalBranch — REPORT

**Branch learner** (`TimeNeuronTimeLearnerBranch`) + **Pack A AsymRm** × span 100/50/25 × gen/preinh + AutoCalibrate LTZ.

## Протокол

| Параметр | Значение |
|----------|----------|
| Learner | `NeuronTimeLearnerBranch` |
| Neuron | AsymRm Pack A gen/preinh |
| GTS | 2000 (после stall @ 10000) |
| TRAIN_T | 160 (также пробовали 480 @ GTS=10000) |

## Результат

**6/6 train_not_Done** @ TRAIN_T=160, GTS=2000:

| EXP | L | FixedLTZ | NeedTrain |
|-----|---|----------|-----------|
| span100 gen | 1 1 18 1 | 0.0115 | 1 |
| span100 preinh | 1 1 11 1 | 0.0115 | 1 |
| span50 gen/preinh | 1 1 6 1 | 0.0115 | 1 |
| span25 gen | 1 1 4 1 | 0.0115 | 1 |
| span25 preinh | 1 1 5 1 | 0.0115 | 1 |

Branch на AsymRm Pack A **не достигает** CalibrateLtz (в отличие от `BranchFastSpan` + D002).

## Контроль (2026-08-27)

`BranchFastSpan/EXP_branch_span25_gen` retrain TRAIN_T=160 @ GTS=2000:

- `verify_train_done.py` **PASS**
- L=`13 11 5 1`, FixedLTZ≈**0.029**, NeedTrain=0

→ stall специфичен для **AsymRm element timing** (C=2.5e-11, D=0.001), не для Branch pipeline.

## Запуск

```bash
bash scripts/setup_asymrm_ltzcal_branch.sh
SKIP_REGRESSION_GATE=1 MAX_JOBS=3 TRAIN_T=160 bash scripts/run_asymrm_ltzcal_branch.sh
```

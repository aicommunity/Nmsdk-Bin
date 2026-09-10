# StructTrain layout canon

Every experiment unit has:

```text
<ExperimentRoot>/
  Train/          # training Project.ini, Model, Parameters, weights
  Test/           # default evaluation (analyzer + SelectivityLog)
  Test_<tag>/     # optional extra eval variants (do not replace Test/)
```

## Rules

- One experiment = one root folder (no sibling `*Test` roots).
- Gate / `rerun_all_tests` / report links use `<root>/Test` by default.
- Extra sweeps live as `Test_<tag>/` beside `Test/`.
- New EXP clones must create both `Train/` and `Test/` immediately.

## Templates

| Role | Path |
|------|------|
| Classic TimeLearner | `TimeNeuronTimeLearner/Train`, `…/Test` |
| Branch TimeLearner | `TimeNeuronTimeLearnerBranch/Train`, `…/Test` |
| Branch NextSegInh | `TimeNeuronTimeLearnerBranch_NextSegInh/{Train,Test}` |
| Branch PreInh250 | `TimeNeuronTimeLearnerBranch_PreInh250/{Train,Test}` |

Campaign EXP under `Selectivity*` already follow `EXP_*/{Train,Test}`.

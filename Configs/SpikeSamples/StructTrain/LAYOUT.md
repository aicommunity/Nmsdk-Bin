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

## Related docs

| Doc | Role |
|-----|------|
| [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md) | Реестр audit-PASS (`ok_audit=1`) + слои ворот + ссылки |
| [`AUDIT_REPORT.md`](AUDIT_REPORT.md) | Ворота, demote, морфология ответа |
| [`CAMPAIGN_REPORT_2026-08_09.md`](CAMPAIGN_REPORT_2026-08_09.md) | Хроника кампаний |
| [`SelectivityPhaseA/PHASE6_480_RECIPE.md`](SelectivityPhaseA/PHASE6_480_RECIPE.md) | PHASE6 рецепт @480 мс (клоны в `Phase6/`) |
| [`SelectivityBranch/PHASE7_BRANCH_QUALITY.md`](SelectivityBranch/PHASE7_BRANCH_QUALITY.md) | PHASE7 качество Branch (клоны TipR@Rmin) |
| [`SelectivityBranch/PHASE8_SHORTSPAN.md`](SelectivityBranch/PHASE8_SHORTSPAN.md) | PHASE8 Branch short-span C1e9 @25/50/100 |
| [`SelectivityAsymRm/PHASE5_SPAN50_100.md`](SelectivityAsymRm/PHASE5_SPAN50_100.md) | PHASE5 short-span C1e9 |
| [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md) | Матрица покрытия tiprmin/C1e9 по семьям |
| [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) | PHASE9 журнал волн + orphan → PHASE10+ |

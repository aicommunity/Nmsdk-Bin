# Legacy StructTrain layouts and production runs

The directories and HEAD tables below describe historical Project.ini campaigns.
Their PASS criteria belong to their recorded snapshots; they do not certify the
new V2 pipeline or replace the August visual observations.

Each historical Project.ini experiment unit has:

```text
<ExperimentRoot>/
  Train/          # training Project.ini, Model, Parameters, weights
  Test/           # default evaluation (analyzer + SelectivityLog)
  Test_<tag>/     # optional extra eval variants (do not replace Test/)
```

## Historical directory rules

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
| [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md) | Реестр только HEAD **PASS** (алгоритм + параметры + протокол) |
| [`EXPERIMENTS.md`](EXPERIMENTS.md) | Полный HEAD-срез: PASS + FAIL + NOT_RETESTED |
| [`RELIABILITY_MAP.ru.md`](RELIABILITY_MAP.ru.md) · [`RELIABILITY_MAP.md`](RELIABILITY_MAP.md) | Карта надёжности: подходы, параметры нейрона, размер паттерна, уровни доверия (T1–T5; не подменяет колонку HEAD) |
| [`AUDIT_REPORT.md`](AUDIT_REPORT.md) | Ворота, demote, морфология ответа |
| [`CAMPAIGN_REPORT_2026-08_09.md`](CAMPAIGN_REPORT_2026-08_09.md) | Хроника кампаний |
| [`SelectivityPhaseA/PHASE6_480_RECIPE.md`](SelectivityPhaseA/PHASE6_480_RECIPE.md) | PHASE6 рецепт @480 мс (клоны в `Phase6/`) |
| [`SelectivityBranch/PHASE7_BRANCH_QUALITY.md`](SelectivityBranch/PHASE7_BRANCH_QUALITY.md) | PHASE7 качество Branch (клоны TipR@Rmin) |
| [`SelectivityBranch/PHASE8_SHORTSPAN.md`](SelectivityBranch/PHASE8_SHORTSPAN.md) | PHASE8 Branch short-span C1e9 @25/50/100 |
| [`SelectivityAsymRm/PHASE5_SPAN50_100.md`](SelectivityAsymRm/PHASE5_SPAN50_100.md) | PHASE5 short-span C1e9 |
| [`RECIPE_COVERAGE.md`](RECIPE_COVERAGE.md) | Матрица покрытия tiprmin/C1e9 по семьям |
| [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) | PHASE9 журнал волн + orphan → PHASE10+ |
| [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md) | PHASE10 S0 disk + tails T0–T2 + PSI/Fast |
| [`PHASE11_COVERAGE.md`](PHASE11_COVERAGE.md) | PHASE11 re-audit RD–R4 + MATRIX |
| [`AUDIT_MATRIX_20260915.csv`](AUDIT_MATRIX_20260915.csv) | trainer/recipe/gate/orphan matrix |

## Current production TimeLearner jobs

Новые инструменты находятся в корневом Scripts/StructTrain/TimeLearner.
Schema2 cold Train содержит finalization_plan и создаёт собственный portable
run directory с job/config/profile archives, native observations, source Solo,
finalization report и разрешённой итоговой recognition-моделью. Наличие каталога
Test или старого template не подтверждает перенос обученной модели.

Из корневого репозитория:

```text
python -m Scripts.StructTrain.TimeLearner train JOB.json --runtime-manifest RUNTIME.json --wall-seconds 1800 --output NEW_RUN
python -m Scripts.StructTrain.TimeLearner report RUN/run-manifest.json --format pipeline-run --output NEW_REPORT
```

Frozen evaluate вызывается отдельно с новым genuine source Solo и объявленным
дизайном. Partial/cancelled Train не выдаётся за успешно завершённое обучение;
SearchUnresolved и молчание target не означают PASS. Новая normal production
приёмка охватывает14 операций, ASan/visual gate ещё выполняется.
Полные изображения кэшируются на M40 Data, Git хранит compressed primary,
модели, метрики и selected images. Старые запускатели не становятся новым
production-путём; полная миграция и их удаление ещё остаются в плане.

[Текущий контракт, область проверок и ограничения](../../../../Docs/StructTrain/TimeLearner/NativeLiveFinalization.ru.md).

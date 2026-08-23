# SelectivityLtzCalibrate — отчёт

Кампания глубокого анализа структурного обучения на коротких ISI. Полный план: [ANALYSIS_structural_learning.md](ANALYSIS_structural_learning.md).

## Статус (2026-08-23)

| Этап | Статус |
|------|--------|
| Sync pipeline (merge_train_model + inject in-place) | ✅ |
| Sync gate (smoke + warm golden) | ✅ — [REGRESSION.md](REGRESSION.md) |
| RegressionFull480 cold retrain | ➖ **не gate** (новые syn/dend params могут не сходиться на Bio full480) |
| FastSpanLtzCal grid | ✅ прогнан — см. [grid_summary.csv](grid_summary.csv) |
| BranchFastSpan setup | ✅ конфиги готовы |
| C++ MatchMode / PatternRecognition | ✅ (rebuild NeuroModeler) |

## Regression PASS (sync fix)

- **Корневая причина fire_all:** `inject_analyzer.py` заменял test Model train Model (stale L=97).
- **Исправление:** `merge_train_model.py` мержит только weight-теги; inject in-place; не трогать `StructureBuildMode=1` в test Model.
- **Warm gate:** `run_regression_warm.sh` — golden Parameters → sync → test (5/8 gen, 6/8 preinh).
- Эталоны fires обновлены под текущий NeuroModeler: `10101010` / `10001010`.

## Data hygiene

- Источник весов: **Train/Parameters_00.xml** (не stale Train Model).
- Runtime: см. [.gitignore](.gitignore).

## Tier 0 / Branch

- Grid: [grid_summary.csv](grid_summary.csv) — 5/6 fire_all; span25 gen 7/8 silent.
- Separability: [separability_tier0.csv](separability_tier0.csv)
- BranchFastSpan: train+sync+test завершён (2 EXP)
- Append Tier 0: [ANALYSIS §Tier 0 results](ANALYSIS_structural_learning.md)

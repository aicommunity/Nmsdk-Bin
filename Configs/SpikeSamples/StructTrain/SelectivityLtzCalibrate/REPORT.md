# SelectivityLtzCalibrate — отчёт

Кампания глубокого анализа структурного обучения на коротких ISI. Полный план: [ANALYSIS_structural_learning.md](ANALYSIS_structural_learning.md).

## Статус (2026-08-23)

| Этап | Статус |
|------|--------|
| Документация + скрипты | ✅ |
| RegressionFull480 | ❌ **FAIL** — см. [REGRESSION.md](REGRESSION.md) |
| FastSpanLtzCal grid | ⏸ заблокирован gate (plan §14) |
| BranchFastSpan setup | ✅ конфиги готовы |
| C++ MatchMode / PatternRecognition | ✅ реализовано |

## Regression FAIL (кратко)

Cold train `-t 160` и `-t 300` не достигает `Done`: `L≈97 81 52 1`, `IsNeedToTrain=1`, `FixedLTZ=0.0115` (AutoCalibrate не срабатывает без Done). Test: **fire_all** `11111111`, acc **1/8**.

**Причина setup (исправлено частично):** шаблон `TimeNeuronTimeLearner` не содержал XML-тегов `AutoCalibrate*` / `PeakMeasureMargin`; `patch_ltz_calibrate.py` теперь **вставляет** теги. Источник regression переведён на golden `EXP00`/`EXP04` margprops.

**Открытый блокер:** cold retrain с `L=1` не сходится до golden `49 41 25 1` в текущем console batch (не связано с MatchMode/PatternRecognition — default behaviour).

## Tier 0 (ожидает regression PASS)

Конфиги `FastSpanLtzCal/` (6 EXP, span 25/50/100) подготовлены с `AutoCalibrate=1`.

## Tier B / C (код)

- **B1:** `NPatternResponseAnalyzer.MatchMode=1` — ISI template vs `TrainingPattern`
- **C1:** `PatternRecognition()` — order_match + LTZ peak tracking (debug log)
- **B2:** `BranchFastSpan/` — `TimeNeuronTimeLearnerBranch` + `NSPNeuronGenD002C25e11`

## Следующий шаг

1. Диагностика cold train stall (сравнение с GUI/warm EXP00, `ResetToUntrainedState`, gap_fraction vs peak_fraction).
2. После regression **PASS** → `MAX_JOBS=4 ./scripts/run_ltz_grid.sh`
3. `./scripts/run_separability.sh FastSpanLtzCal` + sweep

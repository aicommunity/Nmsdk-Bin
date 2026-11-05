# SelectivityPhaseA — индекс экспериментов

Фаза A: конфигурационные эксперименты избирательности `NNeuronTimeLearner` без изменения алгоритма обучения.

Итоговый отчёт: **[REPORT.md](REPORT.md)**

Baseline reference: [`TimeNeuronTimeLearner/Test`](../TimeNeuronTimeLearner/Test/) — 4/8.

| EXP | Train | Test | Изменение | Retrain? | Accuracy |
|-----|-------|------|-----------|:--------:|:--------:|
| EXP00_baseline | `Train/` | `Test/` | контроль | нет | **4/8** |
| EXP01_ltz_threshold_sweep | веса EXP00 | `Test/` (+ `Test_thr*`) | `FixedLTZThreshold` | нет | **6/8** (0.0135) |
| EXP02_ltzone_average_mode | веса EXP00 | `Test/` (+ `Test_avg*`) | `UseAverageLTZonePotential` | нет | 4/8 |
| EXP03_sync_tolerance_015 | `Train/` (`-S`) | `Test/` | `SyncTolerance=0.015` | да | **3/8** |
| EXP04_sync_tolerance_010 | `Train/` (`-S`) | `Test/` | `SyncTolerance=0.010` | да | 4/8 |
| EXP05_resistance_gain_025 | `Train/` (`-S`) | `Test/` | `ResistanceAdjustGain=0.25` | да | 4/8 |
| EXP06_ltzone_integration | веса EXP00 | `Test/` (+ `Test_tc*` / `Test_npltzone_*`) | тип компонента LTZone (`NPLTZone`) / τ / порог | нет | **6/8** (= EXP01) |

Лучший конфиг: [`EXP01_ltz_threshold_sweep/Test`](EXP01_ltz_threshold_sweep/Test/) (канон = бывший `Test_thr00135`).

## PHASE6 @480 мс

Клоны рецепта (не перезаписывают EXP00–06): [`Phase6/`](Phase6/) · журнал [`PHASE6_480_RECIPE.md`](PHASE6_480_RECIPE.md). Best **7/8** selective last-pulse.

## Текущий статус инструментов

Восемь исторических Phase A scripts удалены из поддерживаемого дерева; wrappers не оставлены. Они доступны в Git commit `99f58da9296a794374cef679bbb878cb62af979a` по прежним путям `Configs/SpikeSamples/StructTrain/SelectivityPhaseA/scripts/`. Полный реестр retrieval SHA/blob/hash и причины — `Docs/StructTrain/TimeLearner/script_migration.json` корневого репозитория; пояснение — `Docs/StructTrain/TimeLearner/PhaseAToolRetirement.ru.md`.

Новые запуски и анализ выполняются корневым пакетом `Scripts/StructTrain/TimeLearner`; `python -m Scripts.StructTrain.TimeLearner --help` запускается из корня. Наличие этого CLI не означает завершение научного replay всей Phase A или всех режимов. Старые команды и assumptions сохраняются в Git history.

Все таблицы выше, модели, конфиги, CSV и исходный REPORT сохранены. Визуально подтверждённые августовские4/8,5/8,6/8 относятся к исходному порядку/ITI; удаление инструментов не отменяет эти наблюдения. Offline sweep не заменяет реальный прогон с выбранным порогом.

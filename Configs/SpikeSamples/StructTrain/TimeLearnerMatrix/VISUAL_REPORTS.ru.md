# Визуальные отчёты по опытам TimeLearner

`scripts/generate_timelearner_visual_report.py` формирует один Word-документ для одного запуска или серии run bundles. Генератор читает готовые артефакты и не запускает Console, не изменяет конфиги и не влияет на обучение.

## Что попадёт в документ

- Тренер (Classic `NNeuronTimeLearner` или Branch `NNeuronTimeLearnerBranch`), режим нормализации, настройки пресинаптического торможения и длительность паттерна, если они записаны в provenance.
- ID опыта, время начала обучения, время Test-прогона и окончания, пути и SHA-256 использованных Train/Test XML, Console SHA и git SHAs.
- Фактические аргументы запуска Train и тестовых gate-скриптов, их имена и SHA-256, коды завершения и сохранённые логи скриптов.
- C++-сходимость отдельно от качества классификации: legacy и strict accuracy, обнаружение целевого паттерна, `fires`/`matches`, ложные срабатывания, late FP, форма ответа и результат `ok_audit`.
- Для каждого тестового примера: входные стимулы, выходные импульсы, потенциал `SomaNeuronAmplitude` и потенциал LTZone. C++-оценщик пишет компактную read-only трассу `Test/test_trace.csv`; скрипты её только переносят в run bundle и строят рисунок.

Перед запуском новых тестов используйте Linux Release Console, собранную из PulseLib с поддержкой `TraceLogEnabled`/`TraceLogFileName`. Gate-скрипты включают эти параметры только в Test-конфиге. Локальная Windows-сборка для этого процесса не требуется.

Для старых запусков, в которых непрерывную трассу не сохраняли, по умолчанию генератор останавливается с ошибкой. `--allow-missing-trace` включает явно помеченный исторический отчёт: на графиках остаются отметки входных/выходных импульсов, а отсутствующая осциллограмма не подменяется восстановленной или синтетической кривой.

## Создание отчёта

Нужны Python 3, `python-docx` и Pillow. Передайте одну или несколько папок с `provenance.json` и `Test/results.csv`; для нового формата в каждой папке также лежит `Test/test_trace.csv`.

```powershell
python Bin/Configs/SpikeSamples/StructTrain/scripts/generate_timelearner_visual_report.py `
  --run-root E:/experiments/run-001 `
  --run-root E:/experiments/run-002 `
  --out E:/experiments/reports/series-2026-10-17.docx
```

Для старых логов без трассы:

```powershell
python Bin/Configs/SpikeSamples/StructTrain/scripts/generate_timelearner_visual_report.py `
  --run-root E:/experiments/old-run `
  --allow-missing-trace `
  --out E:/experiments/reports/old-run-events-only.docx
```

После серии передайте генератору все `attempt-XXXX` папки этой серии. Не объединяйте результаты только по имени случая: каждый run bundle остаётся отдельной записью с собственными конфигами, временем и provenance. Конфигурации и метрики, скопированные в отчёт, принадлежат именно этому запуску.

## Точность и скриптовые итоги

Точность gate-скрипта и пересчёт по сохранённому `Test/results.csv` показываются раздельно. Run bundle сохраняет фактическую строку метрик и словарь `quality_metrics`, сформированные gate-скриптом при запуске; в Word отдельно выводятся его legacy/strict accuracy, `fires`/`matches`, обнаружение цели, ложные срабатывания, `ok_audit` и версия метрик. Генератор повторно считает legacy и strict accuracy каноническим `selectivity_metrics.py`, чтобы их можно было сверить с записанным результатом gate. Сходимость берётся из статуса C++-обучения и не выводится из accuracy. Отсутствующая CSV, неполный provenance, неуспешный gate и отсутствующая трасса отмечаются отдельно.

Будущие run bundles сохраняют список runner-скриптов с SHA-256, фактические аргументы orchestration, команду Console для Train, команды gate-скриптов, возвратные коды и `run_*.log`. Запись непрерывной трассы включается только в Test-модели в двух существующих C++ gate-скриптах; параметры обучения и состояние тренера скриптами не меняются.

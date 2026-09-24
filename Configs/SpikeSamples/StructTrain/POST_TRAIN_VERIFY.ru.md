# Проверка C++ PostTune — контракт и состояние

Сверено с PulseLib d4149190 / Bin 9733281, 2026-09-24. [Повторный аудит](../../../../Docs/Audit/TimeLearner-2026-09-24-review/README.md) и [план исправлений/контролей](../../../../Docs/Audit/TimeLearner-2026-09-24-review/PLAN.ru.md).

Сводка разработчика сообщает 2/7 cold PASS: asym50 и br100_search. Пять FAIL: br25_on/off, asym25, br100_keep, phase6_480. [Результаты](_repro/POSTTUNE_VERIFY_RESULT.md) не сопровождаются доступным полным комплектом свежих run-артефактов. Повторный аудит не объявляет эти результаты ложными, но не принимает их как независимую проверку всего HEAD.

## Требования к новому run

1. Новый исполняемый каталог с явно заданными Model/Parameters/Matrix/ini. Старые flags/live/CSV не являются входами. soft_cold поверх fat Model отдельно обозначается и не приравнивается к полной новой инициализации.
2. Связанный build manifest: root/gitlinks/dirty diff, compiler/options, библиотеки, Console SHA. Зафиксировать входы, overrides и scripts до запуска.
3. Train до доказанного завершения с raw rc/termination reason, Need, Phase, Complete, Result и конечными weights. Salvage и контролируемый stop отмечаются отдельно; exited/incomplete сами по себе не успех.
4. Test-калибровка должна быть свежей для этих weights/Matrix. Cpp mid требует current-run inference flag, конечных полных метрик и пригодного landscape. Один inference=1 в старом файле недостаточен.
5. Gate проверяет полную Matrix и observation window, один target-spike после последнего стимула и отсутствие foil-spikes; invalid/censored измерения не считаются тишиной.
6. Search сравнивается с собственным snapshot: applied_best либо подтверждённый same_reverted. Keep проверяет собственные веса. Отличие от другого Keep-клона не является свидетельством работы Search.
7. В run-bundle сохраняются параметры до/после Train→Test, flags, traces, CSV, hashes, команды, raw exit codes и verdict reasons.

Калибровка и оценка по одной Matrix — принятый A07. Held-out не обязателен. A12 отложен при достаточно малом шаге.

## Текущие ограничения автоматизации

posttune_verify.py уже добавил gate rc/fresh CSV checks, численный TipR comparator, раздельные Train/Test metadata, часть SHA/ожиданий и machine verdict. TL получил выбранный-best reprobe. Называть эти исправления отсутствующими неверно.

Однако текущий run_dir архивирует результат после исполнения старого case-каталога. Старый Test flag может подставить mid (в частности tracked Asym50 .0116458); Need=1/incomplete и некоторые Search snapshot нарушения могут не блокировать PASS. Live salvage может принять старый файл после child crash. Probes 15/15 не покрывают эти пути. Поэтому этот скрипт пока не реализует весь контракт выше.

C++ free-run требует дополнительных visited/finite checks: timeout/NaN может дать mid; Result не сбрасывается на новом attempt; explicit LTZ/Soma пути ещё не согласованы. Analyzer может сократить окно на sample advance. Эти ошибки проверяются до интерпретации cold FAIL как дефекта морфогенеза.

## Запуск и артефакты

Текущий orchestrator: [scripts/posttune_verify.py](scripts/posttune_verify.py). CLI: python3 scripts/posttune_verify.py --case br25_on (или all). Для Search --skip-train не допускается. Исполнение меняет clone-каталоги; для новых подтверждающих исследований сначала реализовать изоляцию по плану.

Console/gates используют Linux-путь Bin/Platform/Linux/NeuroModelerConsole через repro_cold_lib.NM. Нужна пересборка именно используемого runtime и сохранение его manifest.

Исторические времена Train: Branch25 320, Asym25 160, Branch100Keep 640, Search 2400, Asym50 320, Phase6 900 модельных секунд. Увеличение времени допускается как отдельный зафиксированный override, а не скрытая смена протокола.

Логи: Train/run_posttune_verify.log и Test/run_gate.log. Runtime debug/live исключены .gitignore; необходимые доказательства сохраняются явно в run-bundle. Политика ограничений logs/deadline должна соответствовать используемым скриптам, а не старому универсальному порогу.

## Разные типы приёмки

- Gold/inherited weights — контроль уже существующего состояния.
- Cold calibration-quality — новое обучение и свежий same-Matrix mid/gate при полной provenance.
- Search reverted PASS — работоспособность fallback; улучшение поиска требует положительного сравнения с собственным snapshot.
- Phase6 CASES ожидает 10000010: это regression-pass с одним foil FP. Строгая избирательность 10000000 оценивается отдельно.

Gold thresholds и допуск ±5% — сравнительный исторический ориентир при сопоставимом протоколе, а не универсальный признак правильности новых весов. Branch25 ≈.0718 и Branch100 ≈.00718 не следует смешивать.

## Историческая матрица прежнего протокола

Таблица ниже сохранена из предыдущей версии документа как запись заявлений прежнего среза. Она не означает текущий PASS и не заменяет новые требования. Историческое условие V5b «TipR≠keep» заменено выше сравнением с собственным snapshot. PHASE12 содержит 12 VALIDATED (в том числе две LtzCal-копии) и 20 VALIDATED_CLONE, а не 32 независимых cold-обучения.

| # | Клон | TipR mode | Ожидание | Исторически заявленный результат |
|---|------|-----------|----------|--------|
| V1 | `SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune` | 1 CanonRmin | TipR `2e7×3+8.6e7`; mid≈gold Test `0.0718` (±5%); fires 8/8; Need→0 | **PASS** fires `10000000` mid≈0.07180 |
| V2 | `…/EXP_br_span25_packA_gen_C1e9_posttune_off` | OFF → CalibrateLtz | Need→0; путь ScaleTipR (TipR ≠ канон допустим); gate с Python tiprmin OK | **PASS** fires `10000000` mid≈0.0163 |
| V3 | `SelectivityAsymRm/EXP_span25ms_packA_gen_posttune` | 2 FlatLastR | TipR `8.6e7×4`; mid≈gold `0.03759`; 8/8 | **PASS** mid≈0.037589 fires `10000000` |
| V4 | `SelectivityAsymRm/EXP_span50ms_packA_gen_posttune` | 1 CanonRmin | TipR Canon; **cpp** mid ±5% к `0.011759`; fires `10000000` | **PASS** mid≈0.011646 `mid_source=cpp` |
| V5 | `…/EXP_br_span100_…_posttune_keep` | 3 KeepDone | TipR snapshot; cpp mid; fires `10000000` | **PASS** mid≈0.00718 |
| V5b | `…/EXP_br_span100_…_posttune_search` | 4 SearchSynthetic | **полный Train** mode=4, `SearchIters=12`, `AutoScaleIterationGap=1`; trial BestTips + free-run reject; TipR≠keep **или** `search_reverted=1`; cpp mid; fires **строго** `10000000` | **PASS** TipR search `search_reverted=1` (Train silent); mid≈0.00714; fires `10000000` |
| V6 | `SelectivityPhaseA/Phase6/EXP_480_gen_posttune` | 1 CanonRmin | TipR Canon; **cpp** mid ±5% к tiprmin `0.016894`; fires `10000010` | **PASS** mid≈0.016896 `mid_source=cpp` |

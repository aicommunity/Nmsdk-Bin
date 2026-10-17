# Подтверждённые успешные эксперименты TimeLearner

## Правило включения

Сюда попадают только опыты, где C++-тренер сошёлся, строгие метрики качества разделения прошли аудит (`ok_audit=1`/эквивалентный зафиксированный strict gate) и цель обнаружена. `Need=0`, успешный код выхода оценщика и исторический permissive `ok=1` сами по себе недостаточны.

Исторические PASS по старым конфигам и бинарникам остаются в [CAMPAIGN_REPORT_2026-08_09.md](CAMPAIGN_REPORT_2026-08_09.md), [исторической инвентаризации](../../../../Docs/Audit/TimeLearner-2026-09-26-review/HISTORICAL_CONFIG_COVERAGE_2026-10-10.ru.md) и истории Git. Их нельзя выдавать за PASS текущего кода.

## Подтверждённые случаи текущей матрицы

| Случай | Тренер | Длительность, мс | Режим | Пресинаптическое торможение | Детекция цели | Acc / FP | Воспроизводимые конфиги |
|---|---|---:|---|---|---|---|---|
| W10_HIST_br50_gen | NNeuronTimeLearnerBranch | 50 | 1 | выключено | detected | 8/8 strict; FP=0 | [Train](TimeLearnerMatrix/W10/inputs/W10_HIST_br50_gen/Train/Project.ini) / [Test](TimeLearnerMatrix/W10/inputs/W10_HIST_br50_gen/Test/Project.ini) |
| W10_HIST_br25_nextseg | NNeuronTimeLearnerBranch | 25 | 1 | выключено | detected | 8/8 strict; FP=0 | [Train](TimeLearnerMatrix/W10/inputs/W10_HIST_br25_nextseg/Train/Project.ini) / [Test](TimeLearnerMatrix/W10/inputs/W10_HIST_br25_nextseg/Test/Project.ini) |
| W34_BR50_N1_PSIoff_POST | NNeuronTimeLearnerBranch | 50 | 1 | выключено | detected | 8/8 strict; FP=0 | [Train](TimeLearnerMatrix/W34/inputs/W34_BR50_N1_PSIoff_POST/Train/Project.ini) / [Test](TimeLearnerMatrix/W34/inputs/W34_BR50_N1_PSIoff_POST/Test/Project.ini) |

В сохранённых W01–W04 есть четыре обучения с `Need=0`, но строгого PASS нет. Два Classic 50-мс случая не имеют валидных метрик из-за ошибки оценщика. Два Branch short-span случая имеют строгие метрики: 25 мс — цель обнаружена, но один false positive (7/8); 50 мс — цель не обнаружена (`fires=00000000`, 7/8). Полное разделение сходимости, качества и детекции приведено в [EXPERIMENTS.md](EXPERIMENTS.md).

Ручные Train/Test-конфиги каждой строки лежат в `TimeLearnerMatrix/<wave>/inputs/<case>/`. Полная матрица содержит отдельный Run case на обучение; внутренние восемь Test-проб не считаются восьмью отдельными обучениями.

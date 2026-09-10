# Сводный отчёт: эксперименты StructTrain (~13 августа – 8 сентября 2026)

Дата сводки: 2026-09-08 (аудит метрик/layout: **2026-09-10**, см. [`AUDIT_REPORT.md`](AUDIT_REPORT.md)).  
Период по журналам и коммитам: примерно четыре недели.  
Цель почти везде: стрелять на обученный временной паттерн и молчать на семь отвлекающих.  
Оценка: 8 проб (сколько ответов совпали с эталоном). Отдельно: попали ли в цель, нет ли стрельбы на все восемь проб.

Конфиги селективности: [`StructTrain/`](.) (этот каталог). Бенчи аксонов: [`../NeuralElements/AxoneLengthDelayStudy/`](../NeuralElements/AxoneLengthDelayStudy/). Пути ниже — относительно `StructTrain/`. Канон раскладки: [`LAYOUT.md`](LAYOUT.md) (`…/{Train,Test}`).

Уточнения к ранней сводке (разд. 3, 5, 6) включены в текст ниже.

---

## Как читать метрики

| Термин | Смысл |
|--------|--------|
| Обучение завершено | Флаг «нужно учить» сброшен, длины дендритов выросли с «1 1 1 1», порог откалиброван (не холодный 0.0115) |
| Точность 6/8 | 6 из 8 проб совпали с желаемым поведением (**legacy** `match`, только in-window) |
| Стрельба на все пробы | Нейрон отвечает на все 8 паттернов |
| Ворота качества (legacy) | Цель поражена и нет стрельбы на все и точность ≥ 4/8 |
| Ворота аудита (`ok_audit`) | legacy-strict (late = ошибка) **и** один спайк на trial (`response_quality=ok_single`) **и** `n=8` |
| Ложный пропуск цели | На целевом паттерне нет генерации |
| Ложное срабатывание | Генерация на отвлекающем паттерне |
| late_fp / пачка / per-stim | Поздний спайк / пачка / ответ на каждый стимул паттерна — **не** успех (см. аудит) |

---

## Хронология кампаний

| Период | Кампания | Папка | Что исследовали |
|--------|----------|-------|-----------------|
| 13–14 авг | Фаза A | [`SelectivityPhaseA/`](SelectivityPhaseA/) | Порог зоны локальной временной интеграции, допуск синхронизации, коэффициент подстройки сопротивления |
| 14–18 авг | Пресинаптическое торможение | [`SelectivityPresynapticInhib/`](SelectivityPresynapticInhib/) | Сила торможения (множитель k), автопорог, сжатие и растяжение длительности паттерна |
| 18–21 авг | Ученик «ветка» | [`TimeNeuronTimeLearnerBranch/{Train,Test}`](TimeNeuronTimeLearnerBranch/), [`…_NextSegInh/`](TimeNeuronTimeLearnerBranch_NextSegInh/), [`…_PreInh250/`](TimeNeuronTimeLearnerBranch_PreInh250/) | Нормализация амплитуд кончиков, торможение следующего сегмента, пресинаптическое торможение k=2.5 |
| 21–23 авг | Быстрый отклик; короткий спан; аксоны | [`SelectivityFastResponse/`](SelectivityFastResponse/), [`SelectivityFastSpan/`](SelectivityFastSpan/), [`../NeuralElements/AxoneLengthDelayStudy/`](../NeuralElements/AxoneLengthDelayStudy/) | Постоянная диссоциации × ёмкость; сжатые 100/50/25 мс; бенчи аксонов |
| 23 авг | Калибровка порога + ремонт пайплайна | [`SelectivityLtzCalibrate/`](SelectivityLtzCalibrate/) (`AsymRmLtzCal/`, `FastSpanLtzCal/`, …) | Автокалибровка после структурного обучения; исправление масштаба паттернов |
| 27 авг – 8 сен | Асимметричная мембрана | [`SelectivityAsymRm/`](SelectivityAsymRm/) | Пакеты A/B/C × спаны × gen/preinh; доводка двух залипших Pack C gen |

---

## 1. Фаза A — конфигурационные рычаги (13 авг)

**Расположение:** [`SelectivityPhaseA/`](SelectivityPhaseA/)

| В отчёте | Каталог |
|----------|---------|
| EXP00 база | [`SelectivityPhaseA/EXP00_baseline`](SelectivityPhaseA/EXP00_baseline) |
| EXP01 | [`SelectivityPhaseA/EXP01_ltz_threshold_sweep`](SelectivityPhaseA/EXP01_ltz_threshold_sweep) |
| EXP02 | [`SelectivityPhaseA/EXP02_ltzone_average_mode`](SelectivityPhaseA/EXP02_ltzone_average_mode) |
| EXP03 | [`SelectivityPhaseA/EXP03_sync_tolerance_015`](SelectivityPhaseA/EXP03_sync_tolerance_015) |
| EXP04 | [`SelectivityPhaseA/EXP04_sync_tolerance_010`](SelectivityPhaseA/EXP04_sync_tolerance_010) |
| EXP05 | [`SelectivityPhaseA/EXP05_resistance_gain_025`](SelectivityPhaseA/EXP05_resistance_gain_025) |
| EXP06 | [`SelectivityPhaseA/EXP06_ltzone_integration`](SelectivityPhaseA/EXP06_ltzone_integration) |

Алгоритм: ученик времени на классическом нейроне-генераторе, эталон ~0.48 с, длины порядка [49, 41, 25, 1].

| Опыт | Что меняли | Диапазон | Сходимость | Точность теста | Конфиги |
|------|------------|----------|------------|----------------|---------|
| EXP00 база | контроль | порог 0.0115 | веса уже обучены | 4/8 | [Train](SelectivityPhaseA/EXP00_baseline/Train) · [Test](SelectivityPhaseA/EXP00_baseline/Test) |
| EXP01 | только порог | 0.0115…0.0135 | без переобучения | лучшее 6/8 при 0.0135 | [Train](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Train) · [Test](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Test) |
| EXP02 | среднее vs сумма по зоне | 0 / 1 | без переобучения | 4/8 | [Train](SelectivityPhaseA/EXP02_ltzone_average_mode/Train) · [Test](SelectivityPhaseA/EXP02_ltzone_average_mode/Test) |
| EXP03 | допуск синхронизации | 0.015 | переобучение; Done за 160 с не зафиксирован | 3/8 | [Train](SelectivityPhaseA/EXP03_sync_tolerance_015/Train) · [Test](SelectivityPhaseA/EXP03_sync_tolerance_015/Test) |
| EXP04 | допуск синхронизации | 0.010 | переобучение | 4/8 | [Train](SelectivityPhaseA/EXP04_sync_tolerance_010/Train) · [Test](SelectivityPhaseA/EXP04_sync_tolerance_010/Test) |
| EXP05 | коэффициент подстройки сопротивления | 0.25 | переобучение | 4/8 | [Train](SelectivityPhaseA/EXP05_resistance_gain_025/Train) · [Test](SelectivityPhaseA/EXP05_resistance_gain_025/Test) |
| EXP06 | класс/интеграция зоны | разные варианты | без переобучения | до 6/8 (как порог 0.0135) | [Train](SelectivityPhaseA/EXP06_ltzone_integration/Train) · [Test](SelectivityPhaseA/EXP06_ltzone_integration/Test) |

Порог: **ручной перебор** фиксированного порога (не «без подстройки»). Лучший результат фазы: 0.0135 → 6/8 **со стрельбой на цель**.

---

## 2. Пресинаптическое торможение (14–18 авг)

**Расположение:** [`SelectivityPresynapticInhib/`](SelectivityPresynapticInhib/)

### 2.1 Перебор силы торможения k

Основная сетка — после GUI-обучения с **автокалибровкой порога** (не холодный 0.0115). Ранние прототипы (отчёт 13 авг) шли при фиксированном 0.0115 и часто не сходились. Каталоги основной сетки — с суффиксом `_autothr`, где он есть; иначе базовое имя.

| В отчёте | Каталог(и) |
|----------|------------|
| EXP00 автопорог | [`EXP00_baseline_autothr`](SelectivityPresynapticInhib/EXP00_baseline_autothr) |
| EXP01…03 (k 0.5…2.0) | [`EXP01_preinh_050_autothr`](SelectivityPresynapticInhib/EXP01_preinh_050_autothr), [`EXP02_preinh_100_autothr`](SelectivityPresynapticInhib/EXP02_preinh_100_autothr), [`EXP03_preinh_200_autothr`](SelectivityPresynapticInhib/EXP03_preinh_200_autothr) |
| EXP04 (k=2.5) | [`EXP04_preinh_250`](SelectivityPresynapticInhib/EXP04_preinh_250) |
| EXP05–10 | [`EXP05_preinh_300`](SelectivityPresynapticInhib/EXP05_preinh_300) … [`EXP09_preinh_1000`](SelectivityPresynapticInhib/EXP09_preinh_1000), [`EXP10_preinh_180`](SelectivityPresynapticInhib/EXP10_preinh_180) |
| EXP11–12, 14 | [`EXP11_preinh_210`](SelectivityPresynapticInhib/EXP11_preinh_210), [`EXP12_preinh_220`](SelectivityPresynapticInhib/EXP12_preinh_220), [`EXP14_preinh_260`](SelectivityPresynapticInhib/EXP14_preinh_260) |
| EXP13, 15 | [`EXP13_preinh_240`](SelectivityPresynapticInhib/EXP13_preinh_240), [`EXP15_preinh_270`](SelectivityPresynapticInhib/EXP15_preinh_270) |

| Опыт | k | Обучение | Длины (примерно) | Порог | Точность | Конфиги |
|------|---|----------|------------------|-------|----------|---------|
| EXP00 автопорог | — | завершено | 49 41 25 1 | ~0.0125 | 4/8 | [Train](SelectivityPresynapticInhib/EXP00_baseline_autothr/Train) · [Test](SelectivityPresynapticInhib/EXP00_baseline_autothr/Test) |
| EXP01…03 | 0.5…2.0 | завершено | ~49… | ~0.02–0.03 | 4/8…5/8 (k=2) | [01](SelectivityPresynapticInhib/EXP01_preinh_050_autothr/Train)·[T](SelectivityPresynapticInhib/EXP01_preinh_050_autothr/Test), [02](SelectivityPresynapticInhib/EXP02_preinh_100_autothr/Train)·[T](SelectivityPresynapticInhib/EXP02_preinh_100_autothr/Test), [03](SelectivityPresynapticInhib/EXP03_preinh_200_autothr/Train)·[T](SelectivityPresynapticInhib/EXP03_preinh_200_autothr/Test) |
| EXP04 | 2.5 | завершено | 51 43 25 1 | ~0.030 | 6/8 | [Train](SelectivityPresynapticInhib/EXP04_preinh_250/Train) · [Test](SelectivityPresynapticInhib/EXP04_preinh_250/Test) |
| EXP05–10 | 3…10 | завершено | ~51 43 25 1 | ~0.03 | 5/8 | [05 Train](SelectivityPresynapticInhib/EXP05_preinh_300/Train)·[T](SelectivityPresynapticInhib/EXP05_preinh_300/Test) … [10](SelectivityPresynapticInhib/EXP10_preinh_180/Train)·[T](SelectivityPresynapticInhib/EXP10_preinh_180/Test) |
| EXP11–12, 14 | 2.1 / 2.2 / 2.6 | завершено | 51 43 25 1 | ~0.030 | 6/8 | [11](SelectivityPresynapticInhib/EXP11_preinh_210/Train)·[T](SelectivityPresynapticInhib/EXP11_preinh_210/Test), [12](SelectivityPresynapticInhib/EXP12_preinh_220/Train)·[T](SelectivityPresynapticInhib/EXP12_preinh_220/Test), [14](SelectivityPresynapticInhib/EXP14_preinh_260/Train)·[T](SelectivityPresynapticInhib/EXP14_preinh_260/Test) |
| EXP13, 15 | 2.4 / 2.7 | завершено | … | ~0.03 | 5/8 | [13](SelectivityPresynapticInhib/EXP13_preinh_240/Train)·[T](SelectivityPresynapticInhib/EXP13_preinh_240/Test), [15](SelectivityPresynapticInhib/EXP15_preinh_270/Train)·[T](SelectivityPresynapticInhib/EXP15_preinh_270/Test) |

Окно лучших k ≈ 2.1–2.6. Выше 7/8 на этой сетке не вышли.

### 2.2 Сжатие длительности (100 / 50 / 25 / 10 мс)

Каталоги: [`EXP20_span100ms_baseline`](SelectivityPresynapticInhib/EXP20_span100ms_baseline) / [`EXP21_…_preinh250`](SelectivityPresynapticInhib/EXP21_span100ms_preinh250), [`EXP22`](SelectivityPresynapticInhib/EXP22_span50ms_baseline)/[`EXP23`](SelectivityPresynapticInhib/EXP23_span50ms_preinh250) (50 мс), [`EXP24`](SelectivityPresynapticInhib/EXP24_span25ms_baseline)/[`EXP25`](SelectivityPresynapticInhib/EXP25_span25ms_preinh250) (25 мс), [`EXP26`](SelectivityPresynapticInhib/EXP26_span10ms_baseline)/[`EXP27`](SelectivityPresynapticInhib/EXP27_span10ms_preinh250) (10 мс).

После исправления метрик (не смотреть «точность» без факта выстрела): на коротких спанах часто стрельба на все пробы или провал ворот. Якоря несжатых 4/8 и 6/8 при проверке не деградировали.

### 2.3 Растяжение (200 / 300 / 400 мс)

Каталоги: [`EXP30`](SelectivityPresynapticInhib/EXP30_span200ms_baseline)/[`EXP31`](SelectivityPresynapticInhib/EXP31_span200ms_preinh250) (200 мс), [`EXP32`](SelectivityPresynapticInhib/EXP32_span300ms_baseline)/[`EXP33`](SelectivityPresynapticInhib/EXP33_span300ms_preinh250) (300 мс), [`EXP34`](SelectivityPresynapticInhib/EXP34_span400ms_baseline)/[`EXP35`](SelectivityPresynapticInhib/EXP35_span400ms_preinh250) (400 мс).

Якоря перед расширением — OK. Стабильного выигрыша «как у k=2.5 на полном спане» не получили.

---

## 3. Ученик «ветка» (18–21 авг) — уточнение про 6/8 и 7/8

**Расположение:** [`TimeNeuronTimeLearnerBranch/{Train,Test}`](TimeNeuronTimeLearnerBranch/) (канон после аудита 2026-09-10). То же для `_NextSegInh` / `_PreInh250`.

| В отчёте | Каталог |
|----------|---------|
| База (R×N + калибровка, amp-eq) | [`TimeNeuronTimeLearnerBranch/`](TimeNeuronTimeLearnerBranch/) |
| Торможение следующего сегмента | [`TimeNeuronTimeLearnerBranch_NextSegInh/`](TimeNeuronTimeLearnerBranch_NextSegInh/) |
| Пресинаптическое торможение k=2.5 | [`TimeNeuronTimeLearnerBranch_PreInh250/`](TimeNeuronTimeLearnerBranch_PreInh250/) |
| Доп. verify | [`TimeNeuronTimeLearnerBranch/Test_savedcheck*`](TimeNeuronTimeLearnerBranch/) |

Алгоритм: один дендрит, импульсы на разных сегментах; обучение длины + нормализация амплитуд; в конце обучения — **встроенная калибровка порога по пику** (доля от пика, обычно ×0.99).

### Итоговые цифры

| Вариант | Обучение | Legacy acc | ok_audit (2026-09-10) | Комментарий | Конфиги |
|---------|----------|------------|------------------------|-------------|---------|
| База | завершено | 6/8 | **0** (per_stim, late_fp=2, max_spikes=6) | late считался «тишиной» | [Train](TimeNeuronTimeLearnerBranch/Train) · [Test](TimeNeuronTimeLearnerBranch/Test) |
| NextSegInh | завершено | 7/8 | **0** (per_stim, late_fp=4) | demoted | [Train](TimeNeuronTimeLearnerBranch_NextSegInh/Train) · [Test](TimeNeuronTimeLearnerBranch_NextSegInh/Test) |
| PreInh250 | завершено | 7/8 | **0** (per_stim, late_fp=3) | demoted | [Train](TimeNeuronTimeLearnerBranch_PreInh250/Train) · [Test](TimeNeuronTimeLearnerBranch_PreInh250/Test) |

**Важно:** legacy 6/8 и 7/8 — цель стреляла (`fn=0`), но аудит показал **late_fp** и **per-stim / multi-spike** морфологию. Это не audit PASS.

### Ложные интерпретации «7/8»

| Ситуация | Точность | Цель | Почему не считать успехом |
|----------|----------|------|---------------------------|
| PreInh250 при неполном копировании весов Test | 7/8 | молчит | совпадение за счёт тишины отвлекающих |
| Ручной XML с торможением без переобучения | 7/8 | молчит (пропуск цели) | не обучался с торможением |
| late_fp на nontarget (in-window тишина) | 7/8 legacy | стреляет | `match` игнорирует late; demote в `ok_strict`/`ok_audit` |
| per-stim / пачка (max_spikes≥2) | любой | любой | брак модели/гиперпараметров |

Лучший **legacy** результат периода на ветке: 7/8 со стрельбой на цель — **снят** аудитом 2026-09-10.
---

## 4. Быстрый отклик мембраны (21 авг)

**Расположение:** [`SelectivityFastResponse/`](SelectivityFastResponse/)

| В отчёте | Каталог |
|----------|---------|
| Контроль (D≈0.005, C≈1e-9) | [`SelectivityFastResponse/EXP00CtrlExp04`](SelectivityFastResponse/EXP00CtrlExp04) |
| D=0.002, C=2.5e-10 | [`SelectivityFastResponse/EXPD002C25e11`](SelectivityFastResponse/EXPD002C25e11) |
| D↓ при C=1e-9 | [`EXPD002C1e9`](SelectivityFastResponse/EXPD002C1e9), [`EXPD001C1e9`](SelectivityFastResponse/EXPD001C1e9) |
| Прочие ячейки сетки D×C | [`EXPD001C5e10`](SelectivityFastResponse/EXPD001C5e10), [`EXPD001C25e11`](SelectivityFastResponse/EXPD001C25e11), [`EXPD002C5e10`](SelectivityFastResponse/EXPD002C5e10), [`EXPD005C5e10`](SelectivityFastResponse/EXPD005C5e10), [`EXPD005C25e11`](SelectivityFastResponse/EXPD005C25e11) |

Меняли постоянную диссоциации синапса (0.005 / 0.002 / 0.001 с) и ёмкость мембраны (~1e-9 / 5e-10 / 2.5e-10).  
Порог: **фиксированный холодный 0.0115** (без автокалибровки в этой кампании).

| Ячейка | Диссоциация | Ёмкость | Цель стреляет | Точность | Замечание | Конфиги |
|--------|-------------|---------|---------------|----------|-----------|---------|
| Контроль | ~0.005 | ~1e-9 | да | 1/8 | перестрел | [Train](SelectivityFastResponse/EXP00CtrlExp04/Train) · [Test](SelectivityFastResponse/EXP00CtrlExp04/Test) |
| D=0.002, C=2.5e-10 | 0.002 | 2.5e-10 | да | 1/8 | самый быстрый пик | [Train](SelectivityFastResponse/EXPD002C25e11/Train) · [Test](SelectivityFastResponse/EXPD002C25e11/Test) |
| D↓ при C=1e-9 | 0.002/0.001 | 1e-9 | нет | 7/8 «молчанием» | брак цели | [D002 Train](SelectivityFastResponse/EXPD002C1e9/Train)·[T](SelectivityFastResponse/EXPD002C1e9/Test), [D001](SelectivityFastResponse/EXPD001C1e9/Train)·[T](SelectivityFastResponse/EXPD001C1e9/Test) |

Ускорение EPSP достигнуто; избирательность не улучшилась.

---

## 5. Короткий спан FastSpan (21–23 авг) — уточнение валидности

**Расположение:** [`SelectivityFastSpan/`](SelectivityFastSpan/)

| В отчёте | Каталог |
|----------|---------|
| 100 мс gen / preinh | [`EXP_span100ms_fast`](SelectivityFastSpan/EXP_span100ms_fast), [`EXP_span100ms_fast_preinh`](SelectivityFastSpan/EXP_span100ms_fast_preinh) |
| 50 мс gen / preinh | [`EXP_span50ms_fast`](SelectivityFastSpan/EXP_span50ms_fast), [`EXP_span50ms_fast_preinh`](SelectivityFastSpan/EXP_span50ms_fast_preinh) |
| 25 мс gen / preinh | [`EXP_span25ms_fast`](SelectivityFastSpan/EXP_span25ms_fast), [`EXP_span25ms_fast_preinh`](SelectivityFastSpan/EXP_span25ms_fast_preinh) |
| 25 мс, шаг времени 10k | [`EXP_span25ms_fast_ts10k`](SelectivityFastSpan/EXP_span25ms_fast_ts10k), [`EXP_span25ms_fast_preinh_ts10k`](SelectivityFastSpan/EXP_span25ms_fast_preinh_ts10k) |

### Валидность прогонов

Все прогоны FastSpan **до 23 августа 2026 невалидны**: скрипт масштаба паттерна сжимал интервалы in-place с полом 1.5 мс без сброса из эталона [0.01, 0.08, 0.16, 0.24] с. Фактический спан обучения был ~4–6 мс при метках 25/50/100 мс; окна допуска считались под заявленный спан.

Следствие: **все прогоны в интервале 21–22 августа по FastSpan невалидны**. Таблицы точности/режима из тех дней не использовать.

Единственный валидный пересчёт: **23 августа** (проверка паттернов 16/16 PASS).

**Cleanup 2026-09-08:** с диска удалены логи/StatisticLog/баки/stale CSV эпохи битого scale (до 23 авг); выполнен `SKIP_TRAIN=1` Test-rerun — канон по-прежнему ≥2026-08-23 (см. `SelectivityFastSpan/JOURNAL.md`). Объективный FAIL (fire_all / silent) сохранён.

### Результаты валидного прогона (порог 0.0115)

| Спан | gen / preinh | Точность | Режим | Ворота | Конфиги |
|------|--------------|----------|-------|--------|---------|
| 100 мс | оба | 1/8 | стрельба на все | FAIL | gen [Tr](SelectivityFastSpan/EXP_span100ms_fast/Train)·[Te](SelectivityFastSpan/EXP_span100ms_fast/Test), preinh [Tr](SelectivityFastSpan/EXP_span100ms_fast_preinh/Train)·[Te](SelectivityFastSpan/EXP_span100ms_fast_preinh/Test) |
| 50 мс | оба | 1/8 | стрельба на все | FAIL | gen [Tr](SelectivityFastSpan/EXP_span50ms_fast/Train)·[Te](SelectivityFastSpan/EXP_span50ms_fast/Test), preinh [Tr](SelectivityFastSpan/EXP_span50ms_fast_preinh/Train)·[Te](SelectivityFastSpan/EXP_span50ms_fast_preinh/Test) |
| 25 мс | оба | 1/8 | стрельба на все | FAIL | gen [Tr](SelectivityFastSpan/EXP_span25ms_fast/Train)·[Te](SelectivityFastSpan/EXP_span25ms_fast/Test), preinh [Tr](SelectivityFastSpan/EXP_span25ms_fast_preinh/Train)·[Te](SelectivityFastSpan/EXP_span25ms_fast_preinh/Test) |
| 25 мс, шаг времени 10k | оба | 7/8 | тишина (цель не стреляет) | FAIL | gen [Tr](SelectivityFastSpan/EXP_span25ms_fast_ts10k/Train)·[Te](SelectivityFastSpan/EXP_span25ms_fast_ts10k/Test), preinh [Tr](SelectivityFastSpan/EXP_span25ms_fast_preinh_ts10k/Train)·[Te](SelectivityFastSpan/EXP_span25ms_fast_preinh_ts10k/Test) |

---

## 6. Калибровка порога и асимметричная мембрана (23 авг – 8 сен)

**Расположение:**
- калибровка Pack A: [`SelectivityLtzCalibrate/AsymRmLtzCal/`](SelectivityLtzCalibrate/AsymRmLtzCal/);
- основная сетка A/B/C: [`SelectivityAsymRm/`](SelectivityAsymRm/).

### Уточнение: «до п.5 всё без подстройки порога?»

**Нет.** До короткого спана порог уже подстраивали:

1. Фаза A — ручной перебор фиксированного порога.  
2. Пресинаптическое торможение (основная сетка) — автокалибровка после обучения.  
3. Ученик «ветка» — встроенная калибровка по пику.  
4. Быстрый отклик и валидный короткий спан — как раз шли при холодном 0.0115.

Новое в этой волне: сделать калибровку **систематическим ответом** на стрельбу на все пробы на коротких спанах и на сетке асимметричной мембраны (после диагноза 18/18 fire_all при 0.0115).

### AsymRmLtzCal (пакет A)

Каталоги: [`EXP_span25ms_packA_gen`](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen) / [`_preinh`](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh), то же для [`span50`](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen) и [`span100`](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen).

На живом прогоне: 1 из 6 дошёл до завершения с калибровкой — спан 25 мс gen, порог ≈0.0885, тест 6/8, ворота PASS (цель стреляет, не fire_all). Остальные — stall обучения.

### SelectivityAsymRm (18 конфигов)

Шаблон имени: `SelectivityAsymRm/EXP_span{25,50,100}ms_pack{A,B,C}_{gen,preinh}`.

| В отчёте | Каталог |
|----------|---------|
| PASS-тест (span25 packA gen) | [`SelectivityAsymRm/EXP_span25ms_packA_gen`](SelectivityAsymRm/EXP_span25ms_packA_gen) |
| Stuck Pack C gen 50 / 100 | [`EXP_span50ms_packC_gen`](SelectivityAsymRm/EXP_span50ms_packC_gen), [`EXP_span100ms_packC_gen`](SelectivityAsymRm/EXP_span100ms_packC_gen) |
| Пилоты D∝span | [`EXP_span50ms_packA_gen_Dspan`](SelectivityAsymRm/EXP_span50ms_packA_gen_Dspan), [`EXP_span100ms_packA_gen_Dspan`](SelectivityAsymRm/EXP_span100ms_packA_gen_Dspan) |
| Пилоты AmpDtAudit | [`EXP_span50ms_packC_gen_ampaudit`](SelectivityAsymRm/EXP_span50ms_packC_gen_ampaudit), [`EXP_span100ms_packC_gen_ampaudit`](SelectivityAsymRm/EXP_span100ms_packC_gen_ampaudit) |

Три пакета мембраны × спаны 25/50/100 мс × gen/preinh.

Первый массовый прогон (конец августа, порог 0.0115): 18/18 стрельба на все, точность 1/8.

На 8 сентября:

| Статус | Число |
|--------|-------|
| Обучение завершено + порог не холодный | 16 / 18 |
| Не завершено | 2 (Pack C gen, спаны 50 и 100 мс) |

**Тест 2026-09-08** на 16 Done (`SELECTIVITY_REPORT.md`): ворота PASS **1/16** — `EXP_span25ms_packA_gen` (6/8, цель стреляет). Остальные в основном стрельба на все пробы при калиброванном пороге; один silent. Рычаг H1 tip-reset на двух Pack C gen — FAIL (TipR снова к Rmax); отпечаток 16 Done сохранён.

**Параметры span:** D/C/Rm внутри пакета **одинаковы** для 25/50/100 мс; со span масштабируются только ISI и Peak/SyncTol — см. [`SelectivityAsymRm/PARAM_SPAN_COMPARE.md`](SelectivityAsymRm/PARAM_SPAN_COMPARE.md). Пилоты D∝span и AmpDtAudit — только на **копиях** EXP (`*_Dspan`, `*_ampaudit`).


---

## 7. Прочие работы того же окна

| Тема | Папка | Результат |
|------|-------|-----------|
| Элементы аксона / задержка vs длина | [`../NeuralElements/AxoneLengthDelayStudy/`](../NeuralElements/AxoneLengthDelayStudy/) | бенчи и смоук; не основная таблица 8-пробной селективности |
| Починка копирования весов Train→Test | (скрипты внутри групп выше) | критично для честных 6/8 и 7/8 на ветке |
| Протоколы «обучение завершено» | см. `SELECTIVITY_*` / `verify_*` в группах | холодный порог запрещён как успех |

---

## Сводная таблица алгоритмов

| Алгоритм | Параметры | Лучшая сходимость | Лучшая точность | Цель стреляет? | Порог | Конфиги (пример) |
|----------|-----------|-------------------|-----------------|----------------|-------|-------------------|
| Классический ученик + порог | 0.0115→0.0135 | веса базы | 6/8 | да | ручной | [Train](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Train) · [Test](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Test) |
| + пресинаптическое торможение | k≈0.5…10, пик 2.1–2.6 | почти все Done | 6/8 | да (в лучших) | автокалибровка | [Train](SelectivityPresynapticInhib/EXP04_preinh_250/Train) · [Test](SelectivityPresynapticInhib/EXP04_preinh_250/Test) |
| Ученик «ветка» + сегментное / preinh | amp-eq, Inh на L+1, k=2.5 | Done | legacy 7/8; **ok_audit=0** (late+per_stim) | да | встроенная калибровка | [Train](TimeNeuronTimeLearnerBranch_PreInh250/Train) · [Test](TimeNeuronTimeLearnerBranch_PreInh250/Test) |
| Быстрая мембрана D×C | D 0.001–0.005; C 2.5e-10–1e-9 | большинство Done | 1/8 при успешном train | да (при 1/8) | холодный 0.0115 | [Train](SelectivityFastResponse/EXPD002C25e11/Train) · [Test](SelectivityFastResponse/EXPD002C25e11/Test) |
| Короткий спан 25–100 мс (валидный, с 23 авг) | D=0.002, C=2.5e-10 | train идёт | 1/8 fire_all или тишина | fire_all: да; ts10k: нет | холодный 0.0115 | [Train](SelectivityFastSpan/EXP_span25ms_fast/Train) · [Test](SelectivityFastSpan/EXP_span25ms_fast/Test) |
| Асимметричная мембрана A/B/C | 3×3×2 | 16/18 Done | тест 1/16 gate PASS (span25 packA gen 6/8) | да на PASS; иначе чаще fire_all | сначала 0.0115, затем калибровка на Done | [Train](SelectivityAsymRm/EXP_span25ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packA_gen/Test) |
| Автокалибровка порога Pack A | после структурного обучения | 1/6 в первой LtzCal-волне | 6/8 | да | автокалибровка | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test) |

---

## Что не упустить

1. Метрика «точность» без режима стрельбы вводила в заблуждение — исправили воротами.  
2. Все FastSpan до 23 августа (включая 21–22) невалидны.  
3. Legacy 6/8 и 7/8 на ветке — со стрельбой на цель, но **аудит 2026-09-10** demote из‑за late_fp и per-stim/multi-spike (`ok_audit=0`).  
4. Подстройка порога была и до п.5 (фаза A, PSI-автопорог, ветка); п.6 сделал калибровку центральным рычагом против fire_all на коротких/асимметричных сетках.  
5. Практический потолок **audit-pass** за месяц: AsymRm/LtzCal `span25 packA gen` 6/8 single-spike; PSI/PhaseA отдельные 4–6/8. Legacy «7/8 на ветке» больше не канон.  
6. Сейчас: 16/18 асимметричных конфигов с завершённым обучением; два Pack C gen открыты.  
7. Полный аудит: [`AUDIT_REPORT.md`](AUDIT_REPORT.md), layout: [`LAYOUT.md`](LAYOUT.md).

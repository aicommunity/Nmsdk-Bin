# Журнал timing / элементы (NeuralElements + StructTrain)

Хронология работ по сжатию паттернов и ускорению EPSP. Актуальные результаты — только в linked REPORT; старые FastSpan прогоны с broken pattern (~5 мс) **невалидны**.

---

## 2026-08-21 — TipEpsCombined / dual-pulse gate

### Цель
Проверить separability двух EPSP на ISI, соответствующих span 100/50/25 мс.

### Наблюдения
Все D×ISI прошли sep≥0.30; на ISI25 Bio D=5 мс sep=0.47 (впритык), D=0.001 sep=0.98.

### Вывод
Синапс готов к 25 мс при D≤0.002. Мембрана — узкое место по τ. Рабочий набор: D=0.002, C=2.5e-10 (`NSPNeuronGenD002C25e11`).

---

## 2026-08-23 — FastSpan pattern fix + valid rerun

### Проблема
Обнаружена системная ошибка масштабирования: все 8 FastSpan EXP имели learner span ~4–6 мс при метках 25/50/100 мс (in-place scale + floor 1.5 ms). Предыдущие выводы по fire_all на FastSpan относились к неверному стимулу.

### Исправления
Идемпотентный `patch_pattern_scale.py`, fresh `copy_config` в `setup_fastspan.sh`, `verify_pattern_span.py`.

### Результат (valid patterns)
- TS=2000 (6 EXP): fire_all, gate FAIL — см. [`SelectivityFastSpan/REPORT.md`](../StructTrain/SelectivityFastSpan/REPORT.md)
- TS=10000 (2 EXP): silent, target_hit=0 — нужна калибровка LTZ
- FastResponse: контрольный аудит паттернов 9/9 OK, span 480 мс

### Вывод
Узкий EPSP необходим, но недостаточен для селективности на сжатых span при текущем learner. Следующий этап — алгоритм / Preinh / tip, не повторный sweep без новой гипотезы.

---

## 2026-08-23 — SelectivityLtzCalibrate (structural learning analysis)

Глубокий анализ train↔test gap и LTZ readout: [`SelectivityLtzCalibrate/ANALYSIS_structural_learning.md`](../StructTrain/SelectivityLtzCalibrate/ANALYSIS_structural_learning.md).

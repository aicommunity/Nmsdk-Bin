# Журнал SelectivityFastSpan

---

## 2026-08-21 22:08 — FastSpan R1 (D002C25e11 × span 100/50/25)

### Цель
Проверить, даёт ли узкий EPSP quality-gate на сжатых паттернах.

### Конфиги
6 EXP, MAX_JOBS=4, TRAIN_T=160, TEST_T=20.

### Наблюдения
Все 6: target_hit=1, fires=8/8, Acc=1/8, gate FAIL (fire_all).

### Вывод
Быстрые элементы не сняли перестрел на коротких span.

### Следующий шаг
Эскалация Peak floor в PulseLib.

---

## 2026-08-21 22:35 — Escalate Peak floor

### Цель
Не давать cable floor ~40 мс перекрывать PeakMeasureMargin на коротких T.

### Изменения
`NNeuronTimeLearner(.Branch)`: margin = XML Peak, если он уже cable floor; `kDelayPerSegDefault=0.005`.

### Наблюдения
Повтор 25/50: снова fire_all.

### Вывод
Блокер не только Peak floor.

---

## 2026-08-21 23:03 — Escalate TimeStep 10k + thr 0.04

### Цель
Тонкая дискретизация и выше порог на span25.

### Наблюдения
Снова fire_all. soma_amp_sum почти одинаков на target и distractors (~0.16–0.17).

### Вывод
На 25 мс разные ISI не дают различимой амплитуды на соме после обучения — нужна другая метрика/механика селективности, не только C/D и SyncTol.

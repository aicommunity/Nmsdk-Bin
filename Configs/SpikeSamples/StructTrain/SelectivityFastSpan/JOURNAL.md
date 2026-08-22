# Журнал SelectivityFastSpan

---

## 2026-08-21 22:08 — FastSpan R1 (D002C25e11 × span 100/50/25)

### Цель
Проверить, даёт ли узкий EPSP quality-gate на сжатых паттернах.

### Конфиги
6 EXP, MAX_JOBS=4, TRAIN_T=160, TEST_T=20. Каталог параметров — `REPORT.md`.

| EXP | NeuronClass | span | D/C / Preinh | GlobalTS | SyncTol | PeakMargin |
|-----|-------------|------|--------------|----------|---------|------------|
| `EXP_span100ms_fast` | `NSPNeuronGenD002C25e11` | 100 | 0.002 / 2.5e-10 | 2000 | 0.004167 | 0.005833 |
| `EXP_span100ms_fast_preinh` | `NSPNeuronGenPreinh2_5` | 100 | k=2.5 + intent D/C | 2000 | 0.004167 | 0.005833 |
| `EXP_span50ms_fast` | `NSPNeuronGenD002C25e11` | 50 | 0.002 / 2.5e-10 | 2000 | 0.002083 | 0.002917 |
| `EXP_span50ms_fast_preinh` | `NSPNeuronGenPreinh2_5` | 50 | k=2.5 + intent D/C | 2000 | 0.002083 | 0.002917 |
| `EXP_span25ms_fast` | `NSPNeuronGenD002C25e11` | 25 | 0.002 / 2.5e-10 | 2000 | 0.0015 | 0.002 |
| `EXP_span25ms_fast_preinh` | `NSPNeuronGenPreinh2_5` | 25 | k=2.5 + intent D/C | 2000 | 0.0015 | 0.002 |

Cold: TipR=86e6×4, L=1, ResistanceAdjustGain=0.4, Delay=1.5, ResetToUntrainedState=1.

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

### Конфиги
| EXP | NeuronClass | GlobalTS | FixedLTZ | Sync/Peak | паттерн |
|-----|-------------|----------|----------|-----------|---------|
| `EXP_span25ms_fast_ts10k` | `NSPNeuronGenD002C25e11` | 10000 | 0.04 | 0.0015 / 0.002 | как span25 |
| `EXP_span25ms_fast_preinh_ts10k` | `NSPNeuronGenPreinh2_5` | 10000 | 0.04 | 0.0015 / 0.002 | как span25 |

### Наблюдения
Снова fire_all. soma_amp_sum почти одинаков на target и distractors (~0.16–0.17).

### Вывод
На 25 мс разные ISI не дают различимой амплитуды на соме после обучения — нужна другая метрика/механика селективности, не только C/D и SyncTol.

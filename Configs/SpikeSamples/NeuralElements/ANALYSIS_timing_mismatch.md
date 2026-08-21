# Анализ несовместимости таймингов (span 100 / 50 / 25 мс)

## Вердикт

Корректной сходимости селективности для **span паттерна** 100 / 50 / 25 мс (после сжатия эталона 0.48 с) добиться не удалось, кроме Preinh@100 мс (Acc 5/8). На 50/25 мс доминирует перестрел (`fire_all`) при завершённом обучении. Ускорение EPSP (SelectivityFastResponse) на несжатом паттерне не закрыло сжатые span.

## Эталон и сжатие

Эталон `InputPattern = [0.01, 0.08, 0.16, 0.24]` (с) → span 1→4 ≈ **0.48 с**.

Сжатие: `α = T / 0.48`, floor ISI = **1.5 мс** (`patch_pattern_scale.py`).

| T (span) | α | min ISI (оценка, 0.08·α с floor) | SyncTol₀ | Peak floor learner (~40 мс) |
|----------|---|----------------------------------|----------|----------------------------|
| 100 мс | 0.2083 | ~16.7 мс | ~4.2 мс | перекрывает T |
| 50 мс | 0.1042 | ~8.3 мс | ~2.1 мс | перекрывает |
| 25 мс | 0.0521 | ~4.2 мс | 1.5 мс | перекрывает |

## Элементные постоянные времени (Bio)

| Элемент | Параметр | Значение | Комментарий |
|---------|----------|----------|-------------|
| NPSynapseBio | DissociationTC | 5 мс | хвост синапса |
| NPSynapseBio | SecretionTC | 1 мс | фронт |
| NPExcChannelBio | Capacity | 1e-9 | |
| NPExcChannelBio | R / Rm | ~1e7 | RC ≈ **10 мс** |
| TimeStep | GlobalTimeStep | 2000 | dt = 0.5 мс |
| FastResponse | t_peak ctrl / best | ~89 / ~30 мс | несжатый паттерн |

Дискретный распад: `VDissociationTC = DissociationTC * TimeStep`; без входа `PreOutput *= (1 - 1/VDissociationTC)`.

## Gate для элементных бенчей (до SyncTol-tune)

1. **FWHM** ≤ `0.5 * min_ISI(T)` → для 25 мс: FWHM ≲ **2.1 мс**.
2. **Separability** (два импульса с ISI = min_ISI(T)):  
   `sep = (min(p1,p2) - trough) / min(p1,p2) ≥ 0.30`.

Если TipEps не проходит gate — **запрещено** крутить SyncTol/Peak на StructTrain: это маскирует физику.

## Источники

- `StructTrain/SelectivityPresynapticInhib/REPORT_time_compress.md`
- `StructTrain/SelectivityFastResponse/REPORT.md`
- `Libraries/Nmsdk-PulseLib/Core/NPulseSynapse.cpp`, `NPulseLibrary.cpp`

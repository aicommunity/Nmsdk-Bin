# Анализ несовместимости таймингов (span 100 / 50 / 25 мс)

## Вердикт

Корректной сходимости селективности для **span паттерна** 100 / 50 / 25 мс (после сжатия эталона 0.48 с) при TS=2000 добиться не удалось.  
**SelectivityFastSpan rerun 2026-08-23** (valid patterns, D=0.002, C=2.5e-10, verify pattern+D/C PASS): 6 EXP TS=2000 — `fire_all`; 2 EXP ts10k — `silent`.  
Ускорение EPSP (SelectivityFastResponse) на несжатом паттерне также не дало селективности (fp=7).  
Контроль: FastResponse аудит 2026-08-23 — 9/9 EXP, span 480 мс OK.

## Эталон и сжатие

Эталон `InputPattern = [0.01, 0.08, 0.16, 0.24]` (с) → span 1→4 ≈ **0.48 с**.

Сжатие: `α = T / 0.48`, scale **из канона** (идемпотентно), floor ISI = **0.5 мс** (`FLOOR_SEC=0.0005` в `patch_pattern_scale.py`).

| T (span) | α | min ISI (0.08·α) | SyncTol₀ | PeakMargin₀ |
|----------|---|------------------|----------|-------------|
| 100 мс | 0.2083 | ~16.7 мс | ~4.2 мс | ~5.8 мс |
| 50 мс | 0.1042 | ~8.3 мс | ~2.1 мс | ~2.9 мс |
| 25 мс | 0.0521 | ~4.2 мс | ~1.0 мс | ~2.0 мс |

## Элементные постоянные времени (Bio)

| Элемент | Параметр | Значение | Комментарий |
|---------|----------|----------|-------------|
| NPSynapseBio | DissociationTC | 5 мс | хвост синапса |
| NPSynapseBio | SecretionTC | 1 мс | фронт |
| NPExcChannelBio | Capacity | 1e-9 | |
| NPExcChannelBio | R / Rm | ~1e7 | RC ≈ **10 мс** |
| TimeStep | GlobalTimeStep | 2000 | dt = 0.5 мс |
| FastResponse | t_peak ctrl / best | ~89 / ~30 мс | несжатый паттерн; `EXPD002C25e11` |

Дискретный распад: `VDissociationTC = DissociationTC * TimeStep`; без входа `PreOutput *= (1 - 1/VDissociationTC)`.

## Конфиги исследования (каталог)

| Набор | Путь | Ключевые конфиги | Роль |
|-------|------|------------------|------|
| Диагноз | `NeuralElements/ANALYSIS_timing_mismatch.md` | — | числа ISI vs EPSP |
| Синапс FWHM | `NeuralElements/SynapseBioTcSweep/` | `cells/D005`, `D002`, `D001`, `D0005` | Dissoc ∈ {5,2,1,0.5} мс |
| Мембрана τ | `NeuralElements/ChannelRcSweep/` | `cells/3a_C*`, `3b_C*` | C ∈ {1e-9…1e-10}, D=5 мс / 1 мс |
| Dual-pulse | `NeuralElements/TipEpsCombined/` | `cells/D*_ISI*`, `CH_D001_C*_ISI25` | sep на ISI 16.7/8.3/4.2 мс |
| Сетка D×C | `StructTrain/SelectivityFastResponse/` | `EXP00CtrlExp04`, `EXPD00{5,2,1}C*` | несжатый паттерн, latency |
| Сжатые span | `StructTrain/SelectivityFastSpan/` | `EXP_span{100,50,25}ms_fast[_preinh][_ts10k]` | quality-gate; Preinh=`…Preinh2_5D002C25e11` |

Рабочая пара после бенчей: **D=0.002, C=2.5e-10** → `NSPNeuronGenD002C25e11` / `NSPNeuronGenPreinh2_5D002C25e11`.

## Gate для элементных бенчей (до SyncTol-tune)

1. **FWHM** ≤ `0.5 * min_ISI(T)` → для 25 мс: FWHM ≲ **2.1 мс**.
2. **Separability** (два импульса с ISI = min_ISI(T)):  
   `sep = (min(p1,p2) - trough) / min(p1,p2) ≥ 0.30`.

Если TipEps не проходит gate — **запрещено** крутить SyncTol/Peak на StructTrain: это маскирует физику.

## Источники

- `StructTrain/SelectivityPresynapticInhib/REPORT_time_compress.md`
- `StructTrain/SelectivityFastResponse/REPORT.md`
- `StructTrain/SelectivityFastSpan/REPORT.md`
- `NeuralElements/*/REPORT.md`
- `Libraries/Nmsdk-PulseLib/Core/NPulseSynapse.cpp`, `NPulseLibrary.cpp`

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

## 2026-08-27 — AsymRmSettle (Exc-only C+Rm+Rsyn)

### Цель
Подобрать (C, ExcRm, ExcRsyn) с settle ≪ ISI25 (~4.17 мс) при gen off, без Inh.

### Наблюдения
- GTS=2000 + C≤2.5e-11 → численная осцилляция канала (Ti·TS≲0.5). Рабочий шаг: **GTS=20000**.
- Pack A (2.5e-11, 1e7, 8.6e7): τ=0.25 мс, settle5%=0.70 мс.
- Pack B (1e-11, 1e7, 5e7): settle=0.25 мс.
- Pack C = (2.5e-11, **5e6**, 8.6e7), не C=5e-12 (osc).
- ctrl FastResponse C=2.5e-10: settle=7.45 мс — не проходит ISI25.

### Вывод
Lock Pack A/B/C → UploadClass AsymRm + кампания SelectivityAsymRm (Inh=10×Exc). См. [`AsymRmSettle/REPORT.md`](AsymRmSettle/REPORT.md).

---

## 2026-09-11 — ChannelRcSweep + AsymRm span25 last-pulse

### Наблюдение
`EXP_span25ms_packA_gen` (C=2.5e-11, τ≈0.25 мс): formal `ok_audit` без last-pulse (`t_rel≈0.001` vs end≈0.025). Demote из реестра успехов. DIAG: mix H-sync/H-tau.

### ChannelRcSweep
- Добавлена ячейка `3b_C25e12` (C=2.5e-11).
- Gate span25: τ ≥ 0.3·EstDelayPerSeg ≈ 1.5 мс → **C=2.5e-10 PASS**, C=2.5e-11 FAIL.
- Новый класс: `NSPNeuronGenAsymRmD001C25e11` (AsymRm + C=2.5e-10).

### C++ (смежно)
- Analyzer: `neuron_fired` только после last stim полного паттерна (≥4 импульса).
- Learner: peak window anti-overlap по delay следующего дендрита; peak_synced может сдвинуть L к соседу с меньшим \|dt\|.

См. [`ChannelRcSweep/REPORT.md`](ChannelRcSweep/REPORT.md), [`StructTrain/SelectivityAsymRm/DIAG_LAST_PULSE_span25_packA.md`](../StructTrain/SelectivityAsymRm/DIAG_LAST_PULSE_span25_packA.md).

---

## 2026-09-11 — AsymRm C1e9 + EstDelayPerSeg XML (span25)

После FAIL tip/thr: физическая τ + seed EstDelay.

- `EstDelayPerSeg` — pub parameter (не wipe в ResizeSyncVectors).
- `NSPNeuronGenAsymRmD001C1e9` (C=1e-9).
- packA retrain Done L=`15 12 8 1`, Cap=1e-9; Test: **late** first spike на всех пробах, но `fire_all`/`per_stim` — last-pulse timing без селективности.

См. [`DIAG_LAST_PULSE_span25_packA.md`](../StructTrain/SelectivityAsymRm/DIAG_LAST_PULSE_span25_packA.md).

---

## 2026-09-11 — AsymRm packA Rsyn floor PASS

`ResistanceMin=2e7`, TipR reset to `8.6e7`, FixedLTZ=`0.0096` on C1e9+EstDelay=0.002 L=`15 12 8 1`: **ok_audit=1**, 8/8 selective, last-pulse single spike. В реестре [`SUCCESSFUL_EXPERIMENTS.md`](../StructTrain/SUCCESSFUL_EXPERIMENTS.md).

---

## 2026-09-11 — span25 recipe replicate + thr window

- thr window packA ≈0.00956–0.00969; lock **0.00962**.
- PASS replicate: LtzCal twin (clone), `packA_preinh` (Preinh C1e9), `packB_gen`, `packC_gen` (per-exp thr).
- New class: `NSPNeuronGenPreinh2_5AsymRmD001C1e9`.

См. DIAG.

---

## 2026-08-27 — SelectivityAsymRm grid

18 EXP (pack A/B/C × 100/50/25 × gen/preinh), GTS=10000, TRAIN_T=80.  
**Все fire_all** при FixedLTZ=0.0115 — см. [`SelectivityAsymRm/REPORT.md`](../StructTrain/SelectivityAsymRm/REPORT.md).  
Мембранный settle OK; селективность упирается в LTZ/learner, не в C/Rm.

---

## 2026-08-23 — SelectivityLtzCalibrate (structural learning analysis)

Глубокий анализ train↔test gap и LTZ readout: [`SelectivityLtzCalibrate/ANALYSIS_structural_learning.md`](../StructTrain/SelectivityLtzCalibrate/ANALYSIS_structural_learning.md).

## 2026-08-27 — Phase1b AsymRm gen-on dip check

Cold L=1 rebuild of EXPD001C25e11 template with `NSPNeuronGenAsymRmD001C25e12` (GTS=20000):
- verify_element_params: Cap=2.5e-11, ExcR=1e7, InhR=1e8, InhRsyn=8.6e8, Dissoc/Secr=0.001 — OK.
- StatisticLog кампанейронных кампаний не пишет SomaSumPotential (только learner traces); количественный dip-diff vs EXPD001 отложен на Watch/GUI при прогоне SelectivityAsymRm.
- Асимметрия Inh τ=10×Exc зафиксирована в UploadClass Pack A/B/C.


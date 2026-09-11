# Реестр успешных экспериментов StructTrain

Живой список **audit-PASS** конфигов с критерием **last-pulse**: результаты и ссылки на Train/Test.  
Это не хроника кампании — полный контекст в [`CAMPAIGN_REPORT_2026-08_09.md`](CAMPAIGN_REPORT_2026-08_09.md), разбор ворот — в [`AUDIT_REPORT.md`](AUDIT_REPORT.md).

**Срез метрик:** 2026-09-10 · источник [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv) · в таблице ниже — записи после demote AsymRm span25 (2026-09-11).

## Критерий включения

В реестр входит только канонический `<root>/Test` с:

1. `ok_audit = ok_strict ∧ (response_quality = ok_single) ∧ (n = 8)`
2. **Last-pulse:** на цели `neuron_t_rel ≥ 0.8 · pattern_end` (`pattern_end = Σ ISI` пробы)
3. Предпочтительно acc ≥ 7 и без FP; soft 6/8 + early-spike на цели — **не** включать

Точность в таблице — `acc_legacy` (при PASS совпадает с `acc_strict`). Режим — `mode_legacy` из CSV (`selective` / `partial_FA`).

**Не включать:** только `ok_legacy`, Branch demoted (late_fp / per-stim), `fire_all`, burst/per-stim, неполные `n≠8`, early-spike target (`t_rel ≪ pattern_end`), варианты `Test_<tag>/` без gate-CSV.

Термины: глоссарий в CAMPAIGN_REPORT (алгоритм обучения, ответ/спайк, тип компонента LTZone, last-pulse).

## Как обновлять

1. При необходимости прогнать Test (`scripts/rerun_all_tests.sh` или точечный NeuroModelerConsole).
2. Пересчитать метрики через [`scripts/selectivity_metrics.py`](scripts/selectivity_metrics.py) и обновить `AUDIT_GATE_RECOMPUTE.csv` (или его преемник).
3. Проверить last-pulse на цели; синхронизировать таблицы ниже.
4. При demote — удалить строку; кратко зафиксировать причину в AUDIT_REPORT.

## Phase A

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP00_baseline | база (порог 0.0115) | 4/8 | partial_FA | [Train](SelectivityPhaseA/EXP00_baseline/Train) · [Test](SelectivityPhaseA/EXP00_baseline/Test) · [CSV](SelectivityPhaseA/EXP00_baseline/Test/SelectivityLog/results.csv) |
| EXP01_ltz_threshold_sweep | порог FixedLTZ | 6/8 | selective | [Train](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Train) · [Test](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Test) · [CSV](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Test/SelectivityLog/results.csv) |
| EXP02_ltzone_average_mode | `UseAverageLTZonePotential` | 4/8 | partial_FA | [Train](SelectivityPhaseA/EXP02_ltzone_average_mode/Train) · [Test](SelectivityPhaseA/EXP02_ltzone_average_mode/Test) · [CSV](SelectivityPhaseA/EXP02_ltzone_average_mode/Test/SelectivityLog/results.csv) |
| EXP06_ltzone_integration | тип компонента LTZone / τ | 4/8 | partial_FA | [Train](SelectivityPhaseA/EXP06_ltzone_integration/Train) · [Test](SelectivityPhaseA/EXP06_ltzone_integration/Test) · [CSV](SelectivityPhaseA/EXP06_ltzone_integration/Test/SelectivityLog/results.csv) |

Алгоритм: `NNeuronTimeLearner` (несколько дендритов).

## Пресинаптическое торможение (PSI)

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP01_preinh_050 | preinh k=0.5 | 4/8 | partial_FA | [Train](SelectivityPresynapticInhib/EXP01_preinh_050/Train) · [Test](SelectivityPresynapticInhib/EXP01_preinh_050/Test) · [CSV](SelectivityPresynapticInhib/EXP01_preinh_050/Test/SelectivityLog/results.csv) |
| EXP14_preinh_260 | preinh k=2.6 | 6/8 | selective | [Train](SelectivityPresynapticInhib/EXP14_preinh_260/Train) · [Test](SelectivityPresynapticInhib/EXP14_preinh_260/Test) · [CSV](SelectivityPresynapticInhib/EXP14_preinh_260/Test/SelectivityLog/results.csv) |
| EXP15_preinh_270 | preinh k=2.7 | 5/8 | partial_FA | [Train](SelectivityPresynapticInhib/EXP15_preinh_270/Train) · [Test](SelectivityPresynapticInhib/EXP15_preinh_270/Test) · [CSV](SelectivityPresynapticInhib/EXP15_preinh_270/Test/SelectivityLog/results.csv) |
| EXP21_span100ms_preinh250 | span 100 мс + k=2.5 | 5/8 | partial_FA | [Train](SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Test/SelectivityLog/results.csv) |
| EXP31_span200ms_preinh250 | span 200 мс + k=2.5 | 5/8 | partial_FA | [Train](SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Test/SelectivityLog/results.csv) |
| EXP32_span300ms_baseline | span 300 мс baseline | 4/8 | partial_FA | [Train](SelectivityPresynapticInhib/EXP32_span300ms_baseline/Train) · [Test](SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test) · [CSV](SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test/SelectivityLog/results.csv) |
| EXP33_span300ms_preinh250 | span 300 мс + k=2.5 | 4/8 | partial_FA | [Train](SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Test/SelectivityLog/results.csv) |
| EXP34_span400ms_baseline | span 400 мс baseline | 4/8 | partial_FA | [Train](SelectivityPresynapticInhib/EXP34_span400ms_baseline/Train) · [Test](SelectivityPresynapticInhib/EXP34_span400ms_baseline/Test) · [CSV](SelectivityPresynapticInhib/EXP34_span400ms_baseline/Test/SelectivityLog/results.csv) |
| EXP35_span400ms_preinh250 | span 400 мс + k=2.5 | 5/8 | partial_FA | [Train](SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Test/SelectivityLog/results.csv) |

## TimeNeuron (классический алгоритм)

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| TimeNeuronTimeLearner | `NNeuronTimeLearner` (несколько дендритов) | 4/8 | partial_FA | [Train](TimeNeuronTimeLearner/Train) · [Test](TimeNeuronTimeLearner/Test) · [CSV](TimeNeuronTimeLearner/Test/SelectivityLog/results.csv) |

## AsymRm (short-span)

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP_span25ms_packA_gen | C1e9 + EstDelay=0.002 + Rmin=2e7 + TipR base + FixedLTZ=0.00962 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span25ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packA_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packA_preinh | + Preinh2.5 C1e9; thr≈0.00469 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span25ms_packA_preinh/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packA_preinh/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packB_gen | recipe→C1e9; thr≈0.00700 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span25ms_packB_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packB_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packB_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packC_gen | recipe→C1e9; thr≈0.00700 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span25ms_packC_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packC_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packC_gen/Test/SelectivityLog/results.csv) |

## AsymRmLtzCal twin

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP_span25ms_packA_gen | clone Model/Parameters с AsymRm эталона | 8/8 | selective | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test/SelectivityLog/results.csv) |

Алгоритм: `NNeuronTimeLearner`; last-pulse на цели. Разбор: [`SelectivityAsymRm/DIAG_LAST_PULSE_span25_packA.md`](SelectivityAsymRm/DIAG_LAST_PULSE_span25_packA.md).

## Вне реестра

- **Branch** (обучение на одном дендрите): legacy 6–7/8 demoted (`ok_audit=0`, late_fp + per-stim) — см. [`AUDIT_REPORT.md`](AUDIT_REPORT.md).
- Хронология кампаний, ложные успехи, отрицательные результаты — [`CAMPAIGN_REPORT_2026-08_09.md`](CAMPAIGN_REPORT_2026-08_09.md).
- Раскладка каталогов — [`LAYOUT.md`](LAYOUT.md).

## Отложено (фаза 5)

Репликация span25 (twin + A_preinh + B/C gen) **PASS**. Далее по решению: сетка 25→50→100. **Не** автостарт без явного go.

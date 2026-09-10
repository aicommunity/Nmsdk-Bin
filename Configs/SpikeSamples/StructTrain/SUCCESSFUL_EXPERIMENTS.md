# Реестр успешных экспериментов StructTrain

Живой список **audit-PASS** конфигов: результаты и ссылки на Train/Test.  
Это не хроника кампании — полный контекст в [`CAMPAIGN_REPORT_2026-08_09.md`](CAMPAIGN_REPORT_2026-08_09.md), разбор ворот — в [`AUDIT_REPORT.md`](AUDIT_REPORT.md).

**Срез метрик:** 2026-09-10 · источник [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv) · **16** записей с `ok_audit=1`.

## Критерий включения

В реестр входит только канонический `<root>/Test` с:

`ok_audit = ok_strict ∧ (response_quality = ok_single) ∧ (n = 8)`

Точность в таблице — `acc_legacy` (при PASS совпадает с `acc_strict`). Режим — `mode_legacy` из CSV (`selective` / `partial_FA`).

**Не включать:** только `ok_legacy`, Branch demoted (late_fp / per-stim), `fire_all`, burst/per-stim, неполные `n≠8`, варианты `Test_<tag>/` без строки `ok_audit=1` в gate-CSV.

Термины: глоссарий в CAMPAIGN_REPORT (алгоритм обучения, ответ/спайк, тип компонента LTZone).

## Как обновлять

1. При необходимости прогнать Test (`scripts/rerun_all_tests.sh` или точечный NeuroModelerConsole).
2. Пересчитать метрики через [`scripts/selectivity_metrics.py`](scripts/selectivity_metrics.py) и обновить `AUDIT_GATE_RECOMPUTE.csv` (или его преемник).
3. Синхронизировать таблицы ниже со всеми строками `ok_audit=1` (добавить / поправить acc и ссылки).
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

## Асимметричная мембрана и калибровка LTZ

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP_span25ms_packA_gen | асимм. Rm, span 25 мс packA gen | 6/8 | selective | [Train](SelectivityAsymRm/EXP_span25ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packA_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packA_gen (LtzCal) | автокалибровка порога после AsymRm | 6/8 | selective | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test/SelectivityLog/results.csv) |

## TimeNeuron (классический алгоритм)

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| TimeNeuronTimeLearner | `NNeuronTimeLearner` (несколько дендритов) | 4/8 | partial_FA | [Train](TimeNeuronTimeLearner/Train) · [Test](TimeNeuronTimeLearner/Test) · [CSV](TimeNeuronTimeLearner/Test/SelectivityLog/results.csv) |

## Вне реестра

- **Branch** (обучение на одном дендрите): legacy 6–7/8 demoted (`ok_audit=0`, late_fp + per-stim) — см. [`AUDIT_REPORT.md`](AUDIT_REPORT.md).
- Хронология кампаний, ложные успехи, отрицательные результаты — [`CAMPAIGN_REPORT_2026-08_09.md`](CAMPAIGN_REPORT_2026-08_09.md).
- Раскладка каталогов — [`LAYOUT.md`](LAYOUT.md).

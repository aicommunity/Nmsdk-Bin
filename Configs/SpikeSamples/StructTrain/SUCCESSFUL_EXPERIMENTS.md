# Реестр успешных экспериментов StructTrain

Живой список **audit-PASS** конфигов с критерием **last-pulse**: результаты и ссылки на Train/Test.  
Это не хроника кампании — полный контекст в [`CAMPAIGN_REPORT_2026-08_09.md`](CAMPAIGN_REPORT_2026-08_09.md), разбор ворот — в [`AUDIT_REPORT.md`](AUDIT_REPORT.md).

**Срез метрик:** 2026-09-15 (PHASE11 R0) · источник [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv) (**167 Test / 77 `ok_audit=1`**) · MATRIX [`AUDIT_MATRIX_20260915.csv`](AUDIT_MATRIX_20260915.csv) · архивы [`archive/AUDIT_GATE_RECOMPUTE_20260915T074504Z_phase11_reaudit.csv`](archive/AUDIT_GATE_RECOMPUTE_20260915T074504Z_phase11_reaudit.csv), [`archive/AUDIT_GATE_RECOMPUTE_20260915T035752Z_phase10_fast.csv`](archive/AUDIT_GATE_RECOMPUTE_20260915T035752Z_phase10_fast.csv). Журналы: [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md), [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md), [`PHASE11_COVERAGE.md`](PHASE11_COVERAGE.md).

**PHASE12:** cold-replay валидация — манифест [`PHASE12_VALIDATION.md`](PHASE12_VALIDATION.md) (source of truth статусов). Wave 1 = Branch short packA roots; Wave 2+ (clones / FS / AsymRm / Phase6) = **DEFERRED** → тот же манифест. PhaseA / PSI / TimeNeuron в реестре ниже — **ARTIFACT (PHASE12)** (исторический audit, без cold-replay).


## Критерий включения

В реестр входит только канонический `<root>/Test` с:

1. `ok_audit = ok_strict ∧ (response_quality = ok_single) ∧ (n = 8)`
2. **Last-pulse:** на цели `neuron_t_rel ≥ 0.8 · pattern_end` (`pattern_end = Σ ISI` пробы)
3. Предпочтительно acc ≥ 7 и без FP; soft 6/8 + early-spike на цели — **не** включать

Точность в таблице — `acc_legacy` (при PASS совпадает с `acc_strict`). Режим — `mode_legacy` из CSV (`selective` / `partial_FA`).

**Не включать:** только `ok_legacy`, Branch demoted (late_fp / per-stim), `fire_all`, burst/per-stim, неполные `n≠8`, early-spike target (`t_rel ≪ pattern_end`), варианты `Test_<tag>/` без gate-CSV.

Термины: глоссарий в CAMPAIGN_REPORT (алгоритм обучения, ответ/спайк, тип компонента LTZone, last-pulse).

### Слои ворот (без изменения порогов кода)

Реализация: [`scripts/selectivity_metrics.py`](scripts/selectivity_metrics.py); mid-pattern spike на цели **не** ставит `neuron_fired` после фикса `kMinStimForInWindowFire` в `NPatternResponseAnalyzer` (PulseLib; нужен полный 4-pulse паттерн и окно после последнего стимула).

| Слой | Что считает | Порог PASS | Late на чужом | Acc |
|------|-------------|------------|---------------|-----|
| **`ok_legacy`** | in-window `neuron_fired` / `match` | `n=8`, target hit, не `fire_all` | **игнорируется** (тишина) | **≥4** |
| **`ok_strict`** | effective fire = in-window ∨ late | target in-window; чужой: ни fire, ни late | **`late_fp` = ошибка** | **≥4** |
| **`ok_audit`** | `ok_strict` ∧ `ok_single` ∧ `n=8` | один спайк/trial (не burst/per_stim) | как strict | **≥4** (не 8/8) |
| **Last-pulse (реестр)** | `neuron_t_rel ≥ 0.8·pattern_end` на цели | ручная проверка поверх audit | — | — |

Важно:

- Канонический **`ok_audit` не требует 8/8**: PhaseA / PSI / TimeNeuron с **4–6/8** `partial_FA` могут иметь `ok_audit=1` и числятся в реестре ниже — это audit-PASS при частичных in-window FP, не «полная селективность».
- Кампании **PHASE5 (AsymRm 25/50/100)** и **PHASE6 (@480 мс)** дополнительно целят **8/8 selective** + last-pulse (процедурная цель волны, не смена формулы `ok_audit`).
- Mid-pattern / early edge на цели без in-window после last stim → `neuron_fired=0`; late-only на цели → `late_fn`.

Ошибки на чужом (nontarget):

| Сигнал | `ok_legacy` | `ok_strict` / audit |
|--------|-------------|---------------------|
| In-window FP (`neuron_fired=1`) | FA (снижает acc) | FA |
| Late FP (`late_fired=1`, in-window тишина) | **не** FA | **FA** (`late_fp`) |
| `fire_all` | FAIL gate | FAIL gate |
| burst / per_stim | не ломает legacy | `ok_audit=0` (`response_quality`) |

## Как обновлять

1. При необходимости прогнать Test (`scripts/rerun_all_tests.sh` или точечный NeuroModelerConsole).
2. Пересчитать метрики через [`scripts/selectivity_metrics.py`](scripts/selectivity_metrics.py) и обновить `AUDIT_GATE_RECOMPUTE.csv` (или его преемник).
3. Проверить last-pulse на цели; синхронизировать таблицы ниже.
4. При demote — удалить строку; кратко зафиксировать причину в AUDIT_REPORT.

## Phase A

Audit-PASS при **partial_FA 4–6/8** (канон `ok_audit` допускает acc≥4). Кампания рецепта @480 мс: [`SelectivityPhaseA/PHASE6_480_RECIPE.md`](SelectivityPhaseA/PHASE6_480_RECIPE.md) / [`Phase6/`](SelectivityPhaseA/Phase6/).

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
| EXP_span25ms_packB_preinh_C1e9 | PHASE9 P2 clone A; thr≈0.00469 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packC_preinh_C1e9 | PHASE9 P2 clone A; thr≈0.00469 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packB_gen | recipe→C1e9; thr≈0.00700 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span25ms_packB_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packB_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packB_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packC_gen | recipe→C1e9; thr≈0.00700 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span25ms_packC_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packC_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packC_gen/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packA_gen | C1e9; TipR@Rmin `2e7×3+8.6e7`; thr=0.011759; L=`25 23 15 1` | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span50ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packA_gen/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packA_preinh | Preinh C1e9; thr=0.011759 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span50ms_packA_preinh/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packA_preinh/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packB_preinh_C1e9 | PHASE9 P2; thr=0.011759 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packC_preinh_C1e9 | PHASE9 P2; thr=0.011759 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packB_gen | clone A→C1e9; thr=0.011759 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span50ms_packB_gen/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packB_gen/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packB_gen/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packC_gen | clone A→C1e9; thr=0.011759 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span50ms_packC_gen/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packC_gen/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packC_gen/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packA_gen | C1e9; TipR@Rmin; thr=0.006681; L=`52 48 27 1` | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span100ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packA_gen/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packA_preinh | Preinh C1e9; thr=0.006681 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span100ms_packA_preinh/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packA_preinh/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packB_preinh_C1e9 | PHASE9 P2 TipR@Rmin; thr≈0.006681 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packC_preinh_C1e9 | PHASE9 P2 TipR@Rmin; thr≈0.006681 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packB_gen | clone A→C1e9; thr=0.006681 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span100ms_packB_gen/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packB_gen/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packB_gen/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packC_gen | clone A→C1e9; thr=0.006681 | 8/8 | selective | [Train](SelectivityAsymRm/EXP_span100ms_packC_gen/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packC_gen/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packC_gen/Test/SelectivityLog/results.csv) |

## AsymRmLtzCal twin

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP_span25ms_packA_gen | clone Model/Parameters с AsymRm эталона | 8/8 | selective | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packA_gen | clone Test эталона; GTS=20000; thr=0.011759 | 8/8 | selective | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packA_gen | clone Test эталона; GTS=20000; thr=0.006681 | 8/8 | selective | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packA_preinh | PHASE10 T2 Test hygiene from AsymRm A_preinh; thr=0.004686425 | 8/8 | selective | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packA_preinh | T2 TipR@Rmin; thr=0.011759 | 8/8 | selective | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packA_preinh | T2 TipR@Rmin; thr=0.006681015 | 8/8 | selective | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Test/SelectivityLog/results.csv) |

Алгоритм: `NNeuronTimeLearner`; last-pulse на цели. Разбор: [`SelectivityAsymRm/DIAG_LAST_PULSE_span25_packA.md`](SelectivityAsymRm/DIAG_LAST_PULSE_span25_packA.md), фаза 50/100: [`SelectivityAsymRm/PHASE5_SPAN50_100.md`](SelectivityAsymRm/PHASE5_SPAN50_100.md).

**Робастность порога:** PASS на 25/50/100 и gen/preinh/twin/B·C — перенос рецепта и last-pulse, **не** широкий амплитудный запас. Зазор «максимум потенциала зоны на цели − на самом трудном чужом»: @25/~1.5e-4, @50/~1.7e-4 (та же хрупкость), @100/~5e-6 (на порядок хуже). Эталон ~480 мс: зазор ~6e-6 при частичных ложных, не «широкий порог». Диагноз и probe: конфиг tip на Done Test зазор ≥5e-4 не даёт; модель нейрона не меняем. [`SelectivityAsymRm/THR_FRAGILITY_DIAG.md`](SelectivityAsymRm/THR_FRAGILITY_DIAG.md).

## Phase6 @480 мс (рецепт PHASE5-процедуры)

Журнал: [`SelectivityPhaseA/PHASE6_480_RECIPE.md`](SelectivityPhaseA/PHASE6_480_RECIPE.md). Исторические EXP00/TimeNeuron/PSI **не** перезаписаны — только клоны в `Phase6/`. Цель волны 8/8 не достигнута (hard foil trial6); ниже — audit-PASS **7/8** selective + last-pulse.

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP_480_gen_tiprmin | TipR@Rmin + Rmin=2e7 + thr=0.016894 | 7/8 | selective | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Test/SelectivityLog/results.csv) |
| EXP_480_gen_thr_only | mid-thr=0.014386, TipR Done | 7/8 | selective | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Test/SelectivityLog/results.csv) |
| EXP_480_preinh250_tiprmin | PSI EXP04 + TipR@Rmin; thr=0.038722 | 7/8 | selective | [Train](SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Test/SelectivityLog/results.csv) |
| EXP_480_ltzcal_twin_gen | twin clean Test tiprmin | 7/8 | selective | [Train](SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen/Test/SelectivityLog/results.csv) |

Зеркало EXP00 (4/8): [`Phase6/EXP_480_gen_baseline`](SelectivityPhaseA/Phase6/EXP_480_gen_baseline/) — не отдельная строка реестра (дубликат EXP00).

## Branch @480 мс (PHASE7)

Журнал: [`SelectivityBranch/PHASE7_BRANCH_QUALITY.md`](SelectivityBranch/PHASE7_BRANCH_QUALITY.md). Исторический канон Branch trio **demoted** (late_fp+per_stim) — сохранён как эталон «до рецепта». PASS — только клоны TipR@Rmin + mid thr по `soma_amp_sum`.

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP_br480_tiprmin | TipR@Rmin + Rmin=2e7 + thr=0.05149 | 8/8 | selective | [Train](SelectivityBranch/EXP_br480_tiprmin/Train) · [Test](SelectivityBranch/EXP_br480_tiprmin/Test) · [CSV](SelectivityBranch/EXP_br480_tiprmin/Test/SelectivityLog/results.csv) |
| EXP_br480_nextseginh_tiprmin | NextSegInh + tiprmin; thr=0.036298 | 8/8 | selective | [Train](SelectivityBranch/EXP_br480_nextseginh_tiprmin/Train) · [Test](SelectivityBranch/EXP_br480_nextseginh_tiprmin/Test) · [CSV](SelectivityBranch/EXP_br480_nextseginh_tiprmin/Test/SelectivityLog/results.csv) |
| EXP_br480_preinh250_tiprmin | Preinh2.5 + tiprmin; thr=0.111136 | 7/8 | selective | [Train](SelectivityBranch/EXP_br480_preinh250_tiprmin/Train) · [Test](SelectivityBranch/EXP_br480_preinh250_tiprmin/Test) · [CSV](SelectivityBranch/EXP_br480_preinh250_tiprmin/Test/SelectivityLog/results.csv) |

## Branch short-span (PHASE8)

Журнал: [`SelectivityBranch/PHASE8_SHORTSPAN.md`](SelectivityBranch/PHASE8_SHORTSPAN.md). Cold Train Branch C1e9 + TipR@Rmin + mid thr по `soma_amp_sum`. Test: overlay Train Neuron + Generator tips `Dendrite1_{L[i]}`.

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP_br_span25_packA_gen_C1e9 | L=`13 11 7 1`; TipR@Rmin; thr≈0.0718 · **VALIDATED (PHASE12 W1)** | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Test/SelectivityLog/results.csv) · repro soft-cold [`_repro`](_repro/REPRO_COLD_INVESTIGATION.md) |
| EXP_br_span50_packA_gen_C1e9 | L=`13 11 6 1`; TipR@Rmin; thr≈0.0644 · **VALIDATED (PHASE12 W1)** | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packA_gen_C1e9 | L=`25 21 11 1`; Done TipR (не Rmin); thr≈0.00718 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packA_preinh_C1e9 | L=`7 6 4 1`; TipR@Rmin; thr≈0.0517 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packA_preinh_C1e9 | L=`13 11 6 1`; TipR@Rmin; thr≈0.0301 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packA_preinh_C1e9 | L=`22 18 11 1`; TipR@Rmin; thr≈0.0203 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packB_gen_C1e9 | clone packA; thr≈0.0718 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packC_gen_C1e9 | clone packA; thr≈0.0718 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packB_preinh_C1e9 | clone packA; thr≈0.0517 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packC_preinh_C1e9 | clone packA; thr≈0.0517 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packB_gen_C1e9 | clone packA; thr≈0.0644 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packC_gen_C1e9 | clone packA; thr≈0.0644 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packB_preinh_C1e9 | clone packA; thr≈0.0301 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packC_preinh_C1e9 | clone packA; thr≈0.0301 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packB_gen_C1e9 | Done TipR; thr≈0.00718 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packC_gen_C1e9 | Done TipR; thr≈0.00718 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packB_preinh_C1e9 | TipR@Rmin; thr≈0.0203 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packC_preinh_C1e9 | TipR@Rmin; thr≈0.0203 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |

PHASE9 P1: pack B/C — [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md).


## Branch NextSegInh short-span (PHASE9 P3)

Журнал: [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md). Cold Train + `EnableNextSegmentInhibition=1` + TipR@Rmin + mid soma.

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP_br_span25_packA_nextseginh_C1e9 | L=`13 11 7 1`; thr≈0.0718 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packA_nextseginh_C1e9 | L=`14 9 6 1`; thr≈0.0456 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packA_nextseginh_C1e9 | L=`21 17 11 1`; thr≈0.0144 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Test/SelectivityLog/results.csv) |

## Branch NextSegInh short pack B/C (PHASE11 R2.1)

Clone packA + Matrix overlay B/C via `phase8_tiprmin_gate.py --skip-prepare --matrix-only` (no cold Train). Mid `soma_amp_sum`.

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP_br_span25_packB_nextseginh_C1e9 | thr≈0.0476 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packC_nextseginh_C1e9 | thr≈0.0476 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packB_nextseginh_C1e9 | thr≈0.0456 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packC_nextseginh_C1e9 | thr≈0.0456 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packB_nextseginh_C1e9 | thr≈0.0144 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packC_nextseginh_C1e9 | thr≈0.0144 | 8/8 | selective | [Train](SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Test/SelectivityLog/results.csv) |

## FastSpan short C1e9 (PHASE10)

Журнал: [`PHASE10_COVERAGE.md`](PHASE10_COVERAGE.md) P10.2. AsymRm C1e9 neuron + cold Train + TipR@Rmin + mid `ltz`. Last-pulse на цели.

| Имя | Рычаг | Acc | Режим | Конфиги |
|-----|--------|-----|-------|---------|
| EXP_span25ms_fast_C1e9 | AsymRmD001C1e9; thr=0.0328372 | 8/8 | selective | [Train](SelectivityFastSpan/EXP_span25ms_fast_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span25ms_fast_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span25ms_fast_C1e9/Test/SelectivityLog/results.csv) · FS soft-cold repro open [`_repro`](_repro/REPRO_COLD_INVESTIGATION.md) |
| EXP_span25ms_fast_preinh_C1e9 | Preinh2_5AsymRm; thr=0.01563085 | 8/8 | selective | [Train](SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span50ms_fast_preinh_C1e9 | Preinh2_5AsymRm; thr=0.0112976 | 8/8 | selective | [Train](SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_fast_C1e9 | AsymRmD001C1e9; thr=0.01568185 | 7/8 | selective | [Train](SelectivityFastSpan/EXP_span100ms_fast_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span100ms_fast_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span100ms_fast_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_fast_preinh_C1e9 | Preinh2_5AsymRm; thr=0.00708053 | 8/8 | selective | [Train](SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Test/SelectivityLog/results.csv) |

`EXP_span50ms_fast_C1e9` — `ok_audit=1` partial_FA acc5; не в реестре.

## Вне реестра

- **Branch канон** (`TimeNeuronTimeLearnerBranch*`) без tiprmin: legacy 6–7/8 demoted (`ok_audit=0`, late_fp + per_stim) — см. [`AUDIT_REPORT.md`](AUDIT_REPORT.md); PHASE7: [`SelectivityBranch/PHASE7_BRANCH_QUALITY.md`](SelectivityBranch/PHASE7_BRANCH_QUALITY.md).
- Short-span BranchFastSpan / `EXP_br_span25_tiprmin` — fire_all / FAIL (superseded PHASE8 C1e9).
- Хронология кампаний — [`CAMPAIGN_REPORT_2026-08_09.md`](CAMPAIGN_REPORT_2026-08_09.md).
- Раскладка каталогов — [`LAYOUT.md`](LAYOUT.md).

## Отложено

- PHASE6 foil trial6 / br480 preinh250 FP: mid-only **FAIL** (amp inversion) — см. [`PHASE9_COVERAGE.md`](PHASE9_COVERAGE.md) P4 notes; T1 TipR still 7/8.
- FastResponse tiprmin P10.3 — silent / fire_all; D/C sweep вне scope.
- PSI short C1e9 — `ok_audit` partial_FA; cold Train deferred.
- PhaseA EXP03–05 / FastSpanLtzCal — P10.4 docs skip.
- PHASE6 Wave 2 pack B/C @480 мс — нет foil-pack аналогов. См. [`PHASE6_480_RECIPE.md`](SelectivityPhaseA/PHASE6_480_RECIPE.md).
- AsymRmLtzCalBranch stall ×6 — не overwrite; замена = PHASE8. См. [`PHASE7_BRANCH_QUALITY.md`](SelectivityBranch/PHASE7_BRANCH_QUALITY.md).

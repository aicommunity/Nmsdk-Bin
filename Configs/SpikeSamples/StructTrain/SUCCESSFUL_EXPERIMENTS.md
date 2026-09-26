# Реестр успешных экспериментов StructTrain

**Срез HEAD 2026-09-25:** Console SHA-256 `5e7829bf9beb1901336ed15b7595786d5708c40d0dd9c9f2f1329bff3c3a1b63` · PulseLib `8d429e7` · Bin `0600e38`.

Только строки со статусом HEAD **PASS**. Ось — **алгоритм + параметры** (как в полном реестре).  
Полный срез (все протоколы / FAIL / NOT_RETESTED) → [`EXPERIMENTS.md`](EXPERIMENTS.md).  
Контракт cold: [`POST_TRAIN_VERIFY.ru.md`](POST_TRAIN_VERIFY.ru.md). Narrative доработок: [`EXPERIMENTS_AFTER_FIXES.ru.md`](../../../Docs/Audit/TimeLearner-2026-09-24-review/EXPERIMENTS_AFTER_FIXES.ru.md).

## Антипутаница

1. PostTune-клон — work-каталог, не отдельный алгоритм; **Имя** = канонический EXP.
2. PASS на одном протоколе (например SkipTrainGold) не означает SoftCold PASS того же алгоритма — см. соседние строки в [`EXPERIMENTS.md`](EXPERIMENTS.md).
3. PHASE12 / T1 не дают места в этом файле без HEAD PASS.

## Колонки

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|

---

## 1. Branch short-span C1e9

### 1.1. packA gen — span 25 мс

Канон `EXP_br_span25_packA_gen_C1e9`. На HEAD подтверждён только контроль на frozen-весах (без обучения). SoftCold того же алгоритма — **FAIL** ([`EXPERIMENTS.md`](EXPERIMENTS.md) §1.1).

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br_span25_packA_gen_C1e9 | NNeuronTimeLearnerBranch | те же веса; TipR canon mid≈0.0718 | SkipTrainGold | 8/8 | да | selective | **PASS** | — | fires `10000000`; mid 0.0718001 cpp | [posttune-клон](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune) · [`bundle`](_repro/runs/br25_on_20260924T165949Z) · [канон](SelectivityBranch/EXP_br_span25_packA_gen_C1e9) |

Других HEAD PASS по Branch / AsymRm / Phase6 / FastSpan / Phase A на срезе нет.

---

## Риск при NOT_RETESTED

| Риск | Когда | Примеры |
|------|-------|---------|
| **high** | SoftCold | cold FAIL у тех же канонов в EXPERIMENTS |
| **med** | GoldTest на старых весах | Asym50/100; Phase6 7/8 |
| **low** | MatrixClone; partial_FA | pack B/C; Phase A / PSI |

---

## Указатели

| Документ | Роль |
|----------|------|
| [`EXPERIMENTS.md`](EXPERIMENTS.md) | полный реестр по алгоритмам |
| [`PHASE12_VALIDATION.md`](PHASE12_VALIDATION.md) | исторические cold-бейджи |
| [`RELIABILITY_MAP.ru.md`](RELIABILITY_MAP.ru.md) | T1–T5 |
| [`POST_TRAIN_VERIFY.ru.md`](POST_TRAIN_VERIFY.ru.md) | контракт PostTune |
| [`LAYOUT.md`](LAYOUT.md) | раскладка |

## GoldTest retest PASS (2026-09-25)

Console=`4917a2bcbac318d1`; источник: `_repro/GOLD_RETEST_*.csv`.

| Имя | Acc | Цель | Режим | fires | Конфиги |
|-----|-----|------|-------|-------|---------|
| EXP00_baseline | 4/8 | да | partial_FA | 10101110 | [SelectivityPresynapticInhib/EXP00_baseline/Test](SelectivityPresynapticInhib/EXP00_baseline/Test) |
| EXP00_baseline_autothr | 4/8 | да | partial_FA | 10101110 | [SelectivityPresynapticInhib/EXP00_baseline_autothr/Test](SelectivityPresynapticInhib/EXP00_baseline_autothr/Test) |
| EXP00_baseline_margprops | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP00_baseline_margprops/Test](SelectivityPresynapticInhib/EXP00_baseline_margprops/Test) |
| EXP01_ltz_threshold_sweep | 6/8 | да | selective | 10001010 | [SelectivityPhaseA/EXP01_ltz_threshold_sweep/Test](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Test) |
| EXP01_preinh_050 | 4/8 | да | partial_FA | 10101110 | [SelectivityPresynapticInhib/EXP01_preinh_050/Test](SelectivityPresynapticInhib/EXP01_preinh_050/Test) |
| EXP02_ltzone_average_mode | 4/8 | да | partial_FA | 10101110 | [SelectivityPhaseA/EXP02_ltzone_average_mode/Test](SelectivityPhaseA/EXP02_ltzone_average_mode/Test) |
| EXP02_preinh_100 | 4/8 | да | partial_FA | 10101110 | [SelectivityPresynapticInhib/EXP02_preinh_100/Test](SelectivityPresynapticInhib/EXP02_preinh_100/Test) |
| EXP03_preinh_200 | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP03_preinh_200/Test](SelectivityPresynapticInhib/EXP03_preinh_200/Test) |
| EXP04_preinh_250 | 6/8 | да | selective | 10001010 | [SelectivityPresynapticInhib/EXP04_preinh_250/Test](SelectivityPresynapticInhib/EXP04_preinh_250/Test) |
| EXP04_preinh_250_margprops | 6/8 | да | selective | 10001010 | [SelectivityPresynapticInhib/EXP04_preinh_250_margprops/Test](SelectivityPresynapticInhib/EXP04_preinh_250_margprops/Test) |
| EXP04_preinh_250_recheck | 6/8 | да | selective | 10001010 | [SelectivityPresynapticInhib/EXP04_preinh_250_recheck/Test](SelectivityPresynapticInhib/EXP04_preinh_250_recheck/Test) |
| EXP04_sync_tolerance_010 | 4/8 | да | partial_FA | 10101110 | [SelectivityPhaseA/EXP04_sync_tolerance_010/Test](SelectivityPhaseA/EXP04_sync_tolerance_010/Test) |
| EXP05_preinh_300 | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP05_preinh_300/Test](SelectivityPresynapticInhib/EXP05_preinh_300/Test) |
| EXP05_resistance_gain_025 | 4/8 | да | partial_FA | 10101110 | [SelectivityPhaseA/EXP05_resistance_gain_025/Test](SelectivityPhaseA/EXP05_resistance_gain_025/Test) |
| EXP06_ltzone_integration | 4/8 | да | partial_FA | 10101110 | [SelectivityPhaseA/EXP06_ltzone_integration/Test](SelectivityPhaseA/EXP06_ltzone_integration/Test) |
| EXP06_preinh_400 | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP06_preinh_400/Test](SelectivityPresynapticInhib/EXP06_preinh_400/Test) |
| EXP07_preinh_500 | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP07_preinh_500/Test](SelectivityPresynapticInhib/EXP07_preinh_500/Test) |
| EXP08_preinh_600 | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP08_preinh_600/Test](SelectivityPresynapticInhib/EXP08_preinh_600/Test) |
| EXP09_preinh_1000 | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP09_preinh_1000/Test](SelectivityPresynapticInhib/EXP09_preinh_1000/Test) |
| EXP10_preinh_180 | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP10_preinh_180/Test](SelectivityPresynapticInhib/EXP10_preinh_180/Test) |
| EXP11_preinh_210 | 6/8 | да | selective | 10001010 | [SelectivityPresynapticInhib/EXP11_preinh_210/Test](SelectivityPresynapticInhib/EXP11_preinh_210/Test) |
| EXP12_preinh_220 | 6/8 | да | selective | 10001010 | [SelectivityPresynapticInhib/EXP12_preinh_220/Test](SelectivityPresynapticInhib/EXP12_preinh_220/Test) |
| EXP13_preinh_240 | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP13_preinh_240/Test](SelectivityPresynapticInhib/EXP13_preinh_240/Test) |
| EXP14_preinh_260 | 6/8 | да | selective | 10001010 | [SelectivityPresynapticInhib/EXP14_preinh_260/Test](SelectivityPresynapticInhib/EXP14_preinh_260/Test) |
| EXP15_preinh_270 | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP15_preinh_270/Test](SelectivityPresynapticInhib/EXP15_preinh_270/Test) |
| EXP21_span100ms_preinh250 | 5/8 | да | partial_FA | 11110000 | [SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Test](SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Test) |
| EXP31_span200ms_preinh250 | 5/8 | да | partial_FA | 10110010 | [SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Test](SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Test) |
| EXP32_span300ms_baseline | 4/8 | да | partial_FA | 10101110 | [SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test](SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test) |
| EXP33_span300ms_preinh250 | 4/8 | да | partial_FA | 10101110 | [SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Test](SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Test) |
| EXP34_span400ms_baseline | 4/8 | да | partial_FA | 10101110 | [SelectivityPresynapticInhib/EXP34_span400ms_baseline/Test](SelectivityPresynapticInhib/EXP34_span400ms_baseline/Test) |
| EXP35_span400ms_preinh250 | 5/8 | да | partial_FA | 10101010 | [SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Test](SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Test) |
| EXP_br480_nextseginh_tiprmin | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br480_nextseginh_tiprmin/Test](SelectivityBranch/EXP_br480_nextseginh_tiprmin/Test) |
| EXP_br480_preinh250_tiprmin | 7/8 | да | selective | 10001000 | [SelectivityBranch/EXP_br480_preinh250_tiprmin/Test](SelectivityBranch/EXP_br480_preinh250_tiprmin/Test) |
| EXP_br480_tiprmin | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br480_tiprmin/Test](SelectivityBranch/EXP_br480_tiprmin/Test) |
| EXP_br_span100_packA_gen_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Test](SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Test) |
| EXP_br_span100_packA_nextseginh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Test](SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Test) |
| EXP_br_span100_packA_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Test](SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Test) |
| EXP_br_span100_packB_gen_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Test](SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Test) |
| EXP_br_span100_packB_nextseginh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Test](SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Test) |
| EXP_br_span100_packB_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Test](SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Test) |
| EXP_br_span100_packC_gen_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Test](SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Test) |
| EXP_br_span100_packC_nextseginh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Test](SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Test) |
| EXP_br_span100_packC_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Test](SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Test) |
| EXP_br_span25_packA_gen_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Test](SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Test) |
| EXP_br_span25_packA_nextseginh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Test](SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Test) |
| EXP_br_span25_packA_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Test](SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Test) |
| EXP_br_span25_packB_gen_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Test](SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Test) |
| EXP_br_span25_packB_nextseginh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Test](SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Test) |
| EXP_br_span25_packB_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Test](SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Test) |
| EXP_br_span25_packC_gen_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Test](SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Test) |
| EXP_br_span25_packC_nextseginh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Test](SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Test) |
| EXP_br_span25_packC_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Test](SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Test) |
| EXP_br_span50_packA_gen_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Test](SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Test) |
| EXP_br_span50_packA_nextseginh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Test](SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Test) |
| EXP_br_span50_packA_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Test](SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Test) |
| EXP_br_span50_packB_gen_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Test](SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Test) |
| EXP_br_span50_packB_nextseginh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Test](SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Test) |
| EXP_br_span50_packB_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Test](SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Test) |
| EXP_br_span50_packC_gen_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Test](SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Test) |
| EXP_br_span50_packC_nextseginh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Test](SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Test) |
| EXP_br_span50_packC_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Test](SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Test) |
| EXP_span100ms_fast_C1e9 | 7/8 | да | selective | 10100000 | [SelectivityFastSpan/EXP_span100ms_fast_C1e9/Test](SelectivityFastSpan/EXP_span100ms_fast_C1e9/Test) |
| EXP_span100ms_fast_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Test](SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Test) |
| EXP_span100ms_packA_gen | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span100ms_packA_gen/Test](SelectivityAsymRm/EXP_span100ms_packA_gen/Test) |
| EXP_span100ms_packA_preinh | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span100ms_packA_preinh/Test](SelectivityAsymRm/EXP_span100ms_packA_preinh/Test) |
| EXP_span100ms_packB_gen | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span100ms_packB_gen/Test](SelectivityAsymRm/EXP_span100ms_packB_gen/Test) |
| EXP_span100ms_packB_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Test](SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Test) |
| EXP_span100ms_packC_gen | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span100ms_packC_gen/Test](SelectivityAsymRm/EXP_span100ms_packC_gen/Test) |
| EXP_span100ms_packC_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Test](SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Test) |
| EXP_span100ms_preinh250_C1e9 | 6/8 | да | selective | 10100001 | [SelectivityPresynapticInhib/EXP_span100ms_preinh250_C1e9/Test](SelectivityPresynapticInhib/EXP_span100ms_preinh250_C1e9/Test) |
| EXP_span25ms_fast_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityFastSpan/EXP_span25ms_fast_C1e9/Test](SelectivityFastSpan/EXP_span25ms_fast_C1e9/Test) |
| EXP_span25ms_fast_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Test](SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Test) |
| EXP_span25ms_packA_gen | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span25ms_packA_gen/Test](SelectivityAsymRm/EXP_span25ms_packA_gen/Test) |
| EXP_span25ms_packA_preinh | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span25ms_packA_preinh/Test](SelectivityAsymRm/EXP_span25ms_packA_preinh/Test) |
| EXP_span25ms_packB_gen | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span25ms_packB_gen/Test](SelectivityAsymRm/EXP_span25ms_packB_gen/Test) |
| EXP_span25ms_packB_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Test](SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Test) |
| EXP_span25ms_packC_gen | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span25ms_packC_gen/Test](SelectivityAsymRm/EXP_span25ms_packC_gen/Test) |
| EXP_span25ms_packC_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Test](SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Test) |
| EXP_span25ms_preinh250_C1e9 | 5/8 | да | partial_FA | 11110000 | [SelectivityPresynapticInhib/EXP_span25ms_preinh250_C1e9/Test](SelectivityPresynapticInhib/EXP_span25ms_preinh250_C1e9/Test) |
| EXP_span50ms_fast_C1e9 | 5/8 | да | partial_FA | 11110000 | [SelectivityFastSpan/EXP_span50ms_fast_C1e9/Test](SelectivityFastSpan/EXP_span50ms_fast_C1e9/Test) |
| EXP_span50ms_fast_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Test](SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Test) |
| EXP_span50ms_packA_gen | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span50ms_packA_gen/Test](SelectivityAsymRm/EXP_span50ms_packA_gen/Test) |
| EXP_span50ms_packA_preinh | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span50ms_packA_preinh/Test](SelectivityAsymRm/EXP_span50ms_packA_preinh/Test) |
| EXP_span50ms_packB_gen | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span50ms_packB_gen/Test](SelectivityAsymRm/EXP_span50ms_packB_gen/Test) |
| EXP_span50ms_packB_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Test](SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Test) |
| EXP_span50ms_packC_gen | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span50ms_packC_gen/Test](SelectivityAsymRm/EXP_span50ms_packC_gen/Test) |
| EXP_span50ms_packC_preinh_C1e9 | 8/8 | да | selective | 10000000 | [SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Test](SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Test) |
| EXP_span50ms_preinh250_C1e9 | 4/8 | да | partial_FA | 11110001 | [SelectivityPresynapticInhib/EXP_span50ms_preinh250_C1e9/Test](SelectivityPresynapticInhib/EXP_span50ms_preinh250_C1e9/Test) |
| LtzCal/EXP_span100ms_packA_gen | 8/8 | да | selective | 10000000 | [SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Test) |
| LtzCal/EXP_span100ms_packA_preinh | 8/8 | да | selective | 10000000 | [SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Test) |
| LtzCal/EXP_span25ms_packA_gen | 8/8 | да | selective | 10000000 | [SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test) |
| LtzCal/EXP_span25ms_packA_preinh | 8/8 | да | selective | 10000000 | [SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Test) |
| LtzCal/EXP_span50ms_packA_gen | 8/8 | да | selective | 10000000 | [SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Test) |
| LtzCal/EXP_span50ms_packA_preinh | 8/8 | да | selective | 10000000 | [SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Test) |
| Phase6/EXP_480_gen_baseline | 4/8 | да | partial_FA | 10101110 | [SelectivityPhaseA/Phase6/EXP_480_gen_baseline/Test](SelectivityPhaseA/Phase6/EXP_480_gen_baseline/Test) |
| Phase6/EXP_480_gen_thr_only | 7/8 | да | selective | 10000010 | [SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Test](SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Test) |
| Phase6/EXP_480_gen_tiprmin | 7/8 | да | selective | 10000010 | [SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Test](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Test) |
| Phase6/EXP_480_gen_tiprmin_phase10_done_tipr | 7/8 | да | selective | 10000010 | [SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase10_done_tipr/Test](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase10_done_tipr/Test) |
| Phase6/EXP_480_gen_tiprmin_phase9_foil6 | 7/8 | да | selective | 10000010 | [SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase9_foil6/Test](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase9_foil6/Test) |
| Phase6/EXP_480_preinh250_tiprmin | 7/8 | да | selective | 10000010 | [SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Test](SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Test) |
| TimeNeuronTimeLearner | 4/8 | да | partial_FA | 10101110 | [TimeNeuronTimeLearner/Test](TimeNeuronTimeLearner/Test) |

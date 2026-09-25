# Реестр экспериментов StructTrain (полный)

**Срез HEAD 2026-09-25:** Console SHA-256 `5e7829bf9beb1901336ed15b7595786d5708c40d0dd9c9f2f1329bff3c3a1b63` · PulseLib `8d429e7` · Bin `0600e38`.

Полный табличный срез: **PASS + FAIL + NOT_RETESTED** на текущем состоянии алгоритма + параметров + протокола прогона.
Только PASS → [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md).
Контракт cold: [`POST_TRAIN_VERIFY.ru.md`](POST_TRAIN_VERIFY.ru.md). Narrative: [`EXPERIMENTS_AFTER_FIXES.ru.md`](../../../Docs/Audit/TimeLearner-2026-09-24-review/EXPERIMENTS_AFTER_FIXES.ru.md).
Уровни T1–T5 (PHASE12-era) → [`RELIABILITY_MAP.ru.md`](RELIABILITY_MAP.ru.md); **здесь вердикт только колонка HEAD**.

## Антипутаница

1. Одна строка = алгоритм + отличимые параметры + **протокол**. Acc gold и soft-cold FAIL — разные строки.
2. PHASE12 `VALIDATED` / RELIABILITY T1 **≠** HEAD PASS. Без свежего прогона → NOT_RETESTED.
3. `ok_audit=1` допускает Acc≥4; это не автоматический PASS SUCCESSFUL.
4. Одинаковый basename AsymRm / LtzCal: короткое имя с префиксом `LtzCal/…`; путь — в колонке Конфиги.
5. Pack B/C `VALIDATED_CLONE` = MatrixClone, не независимое cold.
6. В таблицах нет хроники remediation; причина FAIL — факты протокола.

## Легенда статусов HEAD

| Статус | Смысл |
|--------|--------|
| **PASS** | Подтверждено на текущем HEAD (bundle в Конфиги) |
| **FAIL** | Повторено на HEAD → не проходит контракт строки |
| **NOT_RETESTED** | Свежего прогона на HEAD нет; Acc/Цель — last-known на диске, не вердикт |

## Колонки

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |

- **Имя** — короткий id (basename; для twin — `LtzCal/…`, `Phase6/…`). Полный путь — в **Конфиги**.
- **Acc** — успешные пробы / 8 (избирательность). `—` если gate CSV не получен.
- **Цель** — сработало ли на правильном (целевом) примере: `да` / `нет` / `—` (нет данных). При Acc 8/8 цель всегда `да`; при Acc&lt;8/8 колонка обязательна.
- **Режим** — `selective` / `partial_FA` (как в старом реестре) или `—`.

## Как обновлять

1. Новый прогон → правка строки и синхронизация [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md).
2. Cold: [`scripts/posttune_verify.py`](scripts/posttune_verify.py), bundle в `_repro/runs/`.
3. GoldTest: `selectivity_metrics.py` + canonical Test; не подменять Acc soft-cold результатом.

---

## A. PostTune / строгий cold (текущий HEAD)

Свежие bundles. Строгая cold-матрица 6 клонов: **0 PASS**. Gold-контроль SkipTrainGold: **1 PASS**.

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| br25_posttune | NNeuronTimeLearnerBranch | span25 TipR canon mid≈0.0718 | SkipTrainGold | 8/8 | да | selective | **PASS** | — | fires `10000000`; mid 0.0718001 cpp | [корень](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune) · [`bundle`](_repro/runs/br25_on_20260924T165949Z) |
| br25_posttune | NNeuronTimeLearnerBranch | TipRMode=CanonRmin; soft-cold L≈`1 1 1 1` | SoftCold+PostTune | — | — | — | **FAIL** | — | NonSeparable; mid=1; нет CSV gate | [корень](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune) · [`bundle`](_repro/runs/br25_on_20260924T170503Z) |
| br25_posttune | NNeuronTimeLearnerBranch | TipRMode=KeepDone | SoftCold+PostTune | — | — | — | **FAIL** | — | NonSeparable | [корень](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune) · [`T3_H1`](../../../Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/T3_H1_canon_vs_keep.json) |
| br25_posttune ×2 | NNeuronTimeLearnerBranch | Canon; soft vs strip init | SoftCold vs StripInit | — | — | — | **FAIL** | — | оба FAIL; без различия | [корень](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune) · [`T3_H3`](../../../Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/T3_H3_soft_vs_strip.json) |
| br25_posttune | NNeuronTimeLearnerBranch | AutoScaleIterationGap 0\|1 | SoftCold+PostTune | — | — | — | **FAIL** | — | оба FAIL; Delay/mid/TipR без различия | [корень](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune) · [`T3_H4`](../../../Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/T3_H4_autoscale.json) |
| br25_posttune_off | NNeuronTimeLearnerBranch | EnablePostTrainTuning=0 | SoftCold+PostTuneOff | 6/8 | да | — | **FAIL** | — | fires `10110000` (2 FA); mid≈0.108833 | [корень](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune_off) · [`bundle`](_repro/runs/br25_off_20260924T204259Z) |
| asym25_posttune | NNeuronTimeLearner | TipRMode=FlatLastR `8.6e7×4` | SoftCold+PostTune | — | — | — | **FAIL** | — | NonSeparable; mid=1; нет CSV | [корень](SelectivityAsymRm/EXP_span25ms_packA_gen_posttune) · [`bundle`](_repro/runs/asym25_20260924T214120Z) |
| asym50_posttune | NNeuronTimeLearner | TipRMode=CanonRmin; Train~640 с | SoftCold+PostTune | 8/8 | да | selective | **FAIL** | — | Need=1 (FAIL приёмки); Test fires `10000000` | [корень](SelectivityAsymRm/EXP_span50ms_packA_gen_posttune) · [`bundle`](_repro/runs/asym50_20260924T214908Z) |
| br100_posttune_keep | NNeuronTimeLearnerBranch | TipRMode=KeepDone | SoftCold+PostTune | — | — | — | **FAIL** | — | NonSeparable; tipr≈snapshot | [корень](SelectivityBranch/EXP_br_span100_packA_gen_C1e9_posttune_keep) · [`bundle`](_repro/runs/br100_keep_20260924T234016Z) |
| br100_posttune_search | NNeuronTimeLearnerBranch | TipRMode=SearchSynthetic | SoftCold+PostTune | 0/8 | нет | — | **FAIL** | — | fires `00000000`; same_reverted | [корень](SelectivityBranch/EXP_br_span100_packA_gen_C1e9_posttune_search) · [`bundle`](_repro/runs/br100_search_20260925T015547Z) |
| Phase6/EXP_480_gen_posttune | NNeuronTimeLearner | TipRMode=CanonRmin; span~480 мс | SoftCold+PostTune | — | — | — | **FAIL** | — | Need=1; Test NonSeparable mid=1 | [корень](SelectivityPhaseA/Phase6/EXP_480_gen_posttune) · [`bundle`](_repro/runs/phase6_480_20260924T234719Z) |

Машинная матрица 6 cold: [`D4_matrix_summary.json`](../../../Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/D4_matrix_summary.json).

---

## B. Branch short-span C1e9

GoldTest = last-known Acc на Test. SoftCold Branch25 gen — §A (FAIL). Pack B/C = MatrixClone.

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br_span25_packA_gen_C1e9 | NNeuronTimeLearnerBranch | L=`13 11 7 1` TipR@Rmin thr≈0.0718 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | gold эквивалент SkipTrainGold §A | [Train](SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packA_gen_C1e9 | NNeuronTimeLearnerBranch | L=`13 11 6 1` TipR@Rmin thr≈0.0644 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packA_gen_C1e9 | NNeuronTimeLearnerBranch | L=`25 21 11 1` Done TipR thr≈0.00718 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packA_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | L=`7 6 4 1` TipR@Rmin thr≈0.0517 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packA_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | L=`13 11 6 1` TipR@Rmin thr≈0.0301 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packA_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | L=`22 18 11 1` TipR@Rmin thr≈0.0203 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packA_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | NextSeg L=`13 11 7 1` thr≈0.0476 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packA_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | NextSeg L=`13 11 6 1` thr≈0.0413 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packA_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | NextSeg L=`21 17 11 1` thr≈0.0144 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | PHASE12 soft-cold L stuck | [Train](SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packB_gen_C1e9 | NNeuronTimeLearnerBranch | packB matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packB_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packB matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packB_gen_C1e9 | NNeuronTimeLearnerBranch | packB matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packB_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packB matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packB_gen_C1e9 | NNeuronTimeLearnerBranch | packB matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packB_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packB matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packC_gen_C1e9 | NNeuronTimeLearnerBranch | packC matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packC_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packC matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packC_gen_C1e9 | NNeuronTimeLearnerBranch | packC matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packC_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packC matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packC_gen_C1e9 | NNeuronTimeLearnerBranch | packC matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packC_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packC matrix-only | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packB_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packB nextseg | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packB_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packB nextseg | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packB_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packB nextseg | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packC_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packC nextseg | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packC_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packC nextseg | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packC_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packC nextseg | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Test/SelectivityLog/results.csv) |

---

## C. Branch ~480 мс tiprmin

Acc — только GoldTest на диске. Soft-cold PHASE12 не воспроизвёл; на HEAD не перепрогонялось.

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br480_tiprmin | NNeuronTimeLearnerBranch | TipR@Rmin thr=0.05149 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityBranch/EXP_br480_tiprmin/Train) · [Test](SelectivityBranch/EXP_br480_tiprmin/Test) · [CSV](SelectivityBranch/EXP_br480_tiprmin/Test/SelectivityLog/results.csv) |
| EXP_br480_nextseginh_tiprmin | NNeuronTimeLearnerBranch | NextSeg + tiprmin thr=0.036298 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityBranch/EXP_br480_nextseginh_tiprmin/Train) · [Test](SelectivityBranch/EXP_br480_nextseginh_tiprmin/Test) · [CSV](SelectivityBranch/EXP_br480_nextseginh_tiprmin/Test/SelectivityLog/results.csv) |
| EXP_br480_preinh250_tiprmin | NNeuronTimeLearnerBranch | Preinh2.5 tiprmin thr=0.111136 | GoldTest | 7/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest; 1 FA на фольге | [Train](SelectivityBranch/EXP_br480_preinh250_tiprmin/Train) · [Test](SelectivityBranch/EXP_br480_preinh250_tiprmin/Test) · [CSV](SelectivityBranch/EXP_br480_preinh250_tiprmin/Test/SelectivityLog/results.csv) |

---

## D. AsymRm short-span

SoftCold posttune span25 Flat / span50 Canon — FAIL в §A.

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_span25ms_packA_gen | NNeuronTimeLearner | span25 C1e9 TipR base thr≈0.00962 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span25ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packA_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packA_preinh | NNeuronTimeLearner | span25 Preinh2.5 thr≈0.00469 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span25ms_packA_preinh/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packA_preinh/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packB_gen | NNeuronTimeLearner | span25 packB thr≈0.00700 | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span25ms_packB_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packB_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packB_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packC_gen | NNeuronTimeLearner | span25 packC thr≈0.00700 | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span25ms_packC_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packC_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packC_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packB_preinh_C1e9 | NNeuronTimeLearner | span25 packB preinh thr≈0.00469 | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packC_preinh_C1e9 | NNeuronTimeLearner | span25 packC preinh thr≈0.00469 | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED_CLONE | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packA_gen | NNeuronTimeLearner | span50 TipR@Rmin thr=0.011759 L=`25 23 15 1` | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span50ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packA_gen/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packA_preinh | NNeuronTimeLearner | span50 Preinh thr=0.011759 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span50ms_packA_preinh/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packA_preinh/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packB_gen | NNeuronTimeLearner | span50 packB | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span50ms_packB_gen/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packB_gen/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packB_gen/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packC_gen | NNeuronTimeLearner | span50 packC | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span50ms_packC_gen/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packC_gen/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packC_gen/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packB_preinh_C1e9 | NNeuronTimeLearner | span50 packB preinh | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packC_preinh_C1e9 | NNeuronTimeLearner | span50 packC preinh | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packA_gen | NNeuronTimeLearner | span100 TipR@Rmin thr=0.006681 L=`52 48 27 1` | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span100ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packA_gen/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packA_preinh | NNeuronTimeLearner | span100 Preinh thr=0.006681 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span100ms_packA_preinh/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packA_preinh/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packB_gen | NNeuronTimeLearner | span100 packB | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span100ms_packB_gen/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packB_gen/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packB_gen/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packC_gen | NNeuronTimeLearner | span100 packC | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span100ms_packC_gen/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packC_gen/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packC_gen/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packB_preinh_C1e9 | NNeuronTimeLearner | span100 packB preinh | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packC_preinh_C1e9 | NNeuronTimeLearner | span100 packC preinh | MatrixClone | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |

---

## E. AsymRmLtzCal twin

Имена с префиксом `LtzCal/` — не путать с AsymRm того же basename.

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| LtzCal/EXP_span25ms_packA_gen | NNeuronTimeLearner (LtzCal twin) | twin sync AsymRm span25 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test/SelectivityLog/results.csv) |
| LtzCal/EXP_span25ms_packA_preinh | NNeuronTimeLearner (LtzCal twin) | twin sync AsymRm span25 preinh | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | VALIDATED | last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Test/SelectivityLog/results.csv) |
| LtzCal/EXP_span50ms_packA_gen | NNeuronTimeLearner (LtzCal twin) | twin span50 thr=0.011759 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Test/SelectivityLog/results.csv) |
| LtzCal/EXP_span50ms_packA_preinh | NNeuronTimeLearner (LtzCal twin) | twin span50 preinh | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Test/SelectivityLog/results.csv) |
| LtzCal/EXP_span100ms_packA_gen | NNeuronTimeLearner (LtzCal twin) | twin span100 thr=0.006681 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Test/SelectivityLog/results.csv) |
| LtzCal/EXP_span100ms_packA_preinh | NNeuronTimeLearner (LtzCal twin) | twin span100 preinh | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Test/SelectivityLog/results.csv) |

---

## F. Phase6 ~480 мс tiprmin

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| Phase6/EXP_480_gen_tiprmin | NNeuronTimeLearner | TipR@Rmin thr=0.016894 | GoldTest | 7/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest; 1 FA на фольге | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Test/SelectivityLog/results.csv) |
| Phase6/EXP_480_gen_thr_only | NNeuronTimeLearner | mid-thr=0.014386 TipR Done | GoldTest | 7/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest; 1 FA на фольге | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Test/SelectivityLog/results.csv) |
| Phase6/EXP_480_preinh250_tiprmin | NNeuronTimeLearner | Preinh2.5 TipR@Rmin thr=0.038722 | GoldTest | 7/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest; 1 FA на фольге | [Train](SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Test/SelectivityLog/results.csv) |
| Phase6/EXP_480_ltzcal_twin_gen | NNeuronTimeLearner | twin tiprmin | GoldTest | 7/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest; 1 FA на фольге | [Train](SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen/Test/SelectivityLog/results.csv) |

---

## G. FastSpan C1e9

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_span25ms_fast_C1e9 | NNeuronTimeLearner (FastSpan) | AsymRmD001C1e9 thr=0.0328372 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | FAIL_ROOTCAUSE | last-known GoldTest | [Train](SelectivityFastSpan/EXP_span25ms_fast_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span25ms_fast_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span25ms_fast_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span25ms_fast_preinh_C1e9 | NNeuronTimeLearner (FastSpan) | Preinh2_5 thr=0.01563085 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span50ms_fast_preinh_C1e9 | NNeuronTimeLearner (FastSpan) | Preinh2_5 thr=0.0112976 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_fast_C1e9 | NNeuronTimeLearner (FastSpan) | AsymRmD001C1e9 thr=0.01568185 | GoldTest | 7/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest; 1 FA на фольге | [Train](SelectivityFastSpan/EXP_span100ms_fast_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span100ms_fast_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span100ms_fast_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_fast_preinh_C1e9 | NNeuronTimeLearner (FastSpan) | Preinh2_5 thr=0.00708053 | GoldTest | 8/8 | да | selective | **NOT_RETESTED** | ARTIFACT_KEEP | last-known GoldTest | [Train](SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Test/SelectivityLog/results.csv) |

---

## H. Phase A / TimeNeuron / PSI (старый набор)

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP00_baseline | NNeuronTimeLearner | порог 0.0115 | GoldTest | 4/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPhaseA/EXP00_baseline/Train) · [Test](SelectivityPhaseA/EXP00_baseline/Test) · [CSV](SelectivityPhaseA/EXP00_baseline/Test/SelectivityLog/results.csv) |
| EXP01_ltz_threshold_sweep | NNeuronTimeLearner | порог FixedLTZ | GoldTest | 6/8 | да | selective | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Train) · [Test](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Test) · [CSV](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Test/SelectivityLog/results.csv) |
| EXP02_ltzone_average_mode | NNeuronTimeLearner | UseAverageLTZonePotential | GoldTest | 4/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPhaseA/EXP02_ltzone_average_mode/Train) · [Test](SelectivityPhaseA/EXP02_ltzone_average_mode/Test) · [CSV](SelectivityPhaseA/EXP02_ltzone_average_mode/Test/SelectivityLog/results.csv) |
| EXP06_ltzone_integration | NNeuronTimeLearner | LTZone τ | GoldTest | 4/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPhaseA/EXP06_ltzone_integration/Train) · [Test](SelectivityPhaseA/EXP06_ltzone_integration/Test) · [CSV](SelectivityPhaseA/EXP06_ltzone_integration/Test/SelectivityLog/results.csv) |
| EXP01_preinh_050 | NNeuronTimeLearner + Preinh | preinh k=0.5 | GoldTest | 4/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP01_preinh_050/Train) · [Test](SelectivityPresynapticInhib/EXP01_preinh_050/Test) · [CSV](SelectivityPresynapticInhib/EXP01_preinh_050/Test/SelectivityLog/results.csv) |
| EXP14_preinh_260 | NNeuronTimeLearner + Preinh | preinh k=2.6 | GoldTest | 6/8 | да | selective | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP14_preinh_260/Train) · [Test](SelectivityPresynapticInhib/EXP14_preinh_260/Test) · [CSV](SelectivityPresynapticInhib/EXP14_preinh_260/Test/SelectivityLog/results.csv) |
| EXP15_preinh_270 | NNeuronTimeLearner + Preinh | preinh k=2.7 | GoldTest | 5/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP15_preinh_270/Train) · [Test](SelectivityPresynapticInhib/EXP15_preinh_270/Test) · [CSV](SelectivityPresynapticInhib/EXP15_preinh_270/Test/SelectivityLog/results.csv) |
| EXP21_span100ms_preinh250 | NNeuronTimeLearner + Preinh | span 100 мс + k=2.5 | GoldTest | 5/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Test/SelectivityLog/results.csv) |
| EXP31_span200ms_preinh250 | NNeuronTimeLearner + Preinh | span 200 мс + k=2.5 | GoldTest | 5/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Test/SelectivityLog/results.csv) |
| EXP32_span300ms_baseline | NNeuronTimeLearner + Preinh | span 300 мс baseline | GoldTest | 4/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP32_span300ms_baseline/Train) · [Test](SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test) · [CSV](SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test/SelectivityLog/results.csv) |
| EXP33_span300ms_preinh250 | NNeuronTimeLearner + Preinh | span 300 мс + k=2.5 | GoldTest | 4/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Test/SelectivityLog/results.csv) |
| EXP34_span400ms_baseline | NNeuronTimeLearner + Preinh | span 400 мс baseline | GoldTest | 4/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP34_span400ms_baseline/Train) · [Test](SelectivityPresynapticInhib/EXP34_span400ms_baseline/Test) · [CSV](SelectivityPresynapticInhib/EXP34_span400ms_baseline/Test/SelectivityLog/results.csv) |
| EXP35_span400ms_preinh250 | NNeuronTimeLearner + Preinh | span 400 мс + k=2.5 | GoldTest | 5/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Test/SelectivityLog/results.csv) |
| TimeNeuronTimeLearner | NNeuronTimeLearner | классический канон | GoldTest | 4/8 | да | partial_FA | **NOT_RETESTED** | ARTIFACT | last-known GoldTest | [Train](TimeNeuronTimeLearner/Train) · [Test](TimeNeuronTimeLearner/Test) · [CSV](TimeNeuronTimeLearner/Test/SelectivityLog/results.csv) |

---

## Вне строк / OUT / demoted

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| TimeNeuronTimeLearnerBranch* | NNeuronTimeLearnerBranch | канон без tiprmin | GoldTest | — | — | — | **NOT_RETESTED** | OUT | demoted: late_fp + per_stim | [AUDIT_REPORT](AUDIT_REPORT.md) |
| …Branch_NextSegInh | Branch + NextSeg | канон без tiprmin | GoldTest | — | — | — | **NOT_RETESTED** | OUT | demoted | [PHASE7](SelectivityBranch/PHASE7_BRANCH_QUALITY.md) |
| …Branch_PreInh250 | Branch + Preinh | канон без tiprmin | GoldTest | — | — | — | **NOT_RETESTED** | OUT | demoted | [PHASE7](SelectivityBranch/PHASE7_BRANCH_QUALITY.md) |
| EXP_br_span25_tiprmin | NNeuronTimeLearnerBranch | ранний tiprmin short | GoldTest | — | — | — | **NOT_RETESTED** | OUT | fire_all; superseded PHASE8 | [корень](SelectivityBranch/EXP_br_span25_tiprmin) |

---

## ok_audit=1 вне прежнего SUCCESSFUL

Сводка [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv). В SUCCESSFUL не переносить. HEAD: NOT_RETESTED.

| Имя | Acc | Цель | Режим | HEAD | Конфиги |
|-----|-----|------|-------|------|---------|
| EXP_span50ms_fast_C1e9 | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityFastSpan/EXP_span50ms_fast_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span50ms_fast_C1e9/Test) |
| EXP04_sync_tolerance_010 | 4/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPhaseA/EXP04_sync_tolerance_010/Train) · [Test](SelectivityPhaseA/EXP04_sync_tolerance_010/Test) |
| EXP05_resistance_gain_025 | 4/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPhaseA/EXP05_resistance_gain_025/Train) · [Test](SelectivityPhaseA/EXP05_resistance_gain_025/Test) |
| Phase6/EXP_480_gen_baseline | 4/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_baseline/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_baseline/Test) |
| Phase6/EXP_480_gen_tiprmin_phase10_done_tipr | 7/8 | да | selective | **NOT_RETESTED** | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase10_done_tipr/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase10_done_tipr/Test) |
| Phase6/EXP_480_gen_tiprmin_phase9_foil6 | 7/8 | да | selective | **NOT_RETESTED** | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase9_foil6/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase9_foil6/Test) |
| EXP00_baseline | 4/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP00_baseline/Train) · [Test](SelectivityPresynapticInhib/EXP00_baseline/Test) |
| EXP00_baseline_autothr | 4/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP00_baseline_autothr/Train) · [Test](SelectivityPresynapticInhib/EXP00_baseline_autothr/Test) |
| EXP00_baseline_margprops | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP00_baseline_margprops/Train) · [Test](SelectivityPresynapticInhib/EXP00_baseline_margprops/Test) |
| EXP02_preinh_100 | 4/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP02_preinh_100/Train) · [Test](SelectivityPresynapticInhib/EXP02_preinh_100/Test) |
| EXP03_preinh_200 | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP03_preinh_200/Train) · [Test](SelectivityPresynapticInhib/EXP03_preinh_200/Test) |
| EXP04_preinh_250 | 6/8 | да | selective | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP04_preinh_250/Train) · [Test](SelectivityPresynapticInhib/EXP04_preinh_250/Test) |
| EXP04_preinh_250_margprops | 6/8 | да | selective | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP04_preinh_250_margprops/Train) · [Test](SelectivityPresynapticInhib/EXP04_preinh_250_margprops/Test) |
| EXP04_preinh_250_recheck | 6/8 | да | selective | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP04_preinh_250_recheck/Train) · [Test](SelectivityPresynapticInhib/EXP04_preinh_250_recheck/Test) |
| EXP05_preinh_300 | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP05_preinh_300/Train) · [Test](SelectivityPresynapticInhib/EXP05_preinh_300/Test) |
| EXP06_preinh_400 | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP06_preinh_400/Train) · [Test](SelectivityPresynapticInhib/EXP06_preinh_400/Test) |
| EXP07_preinh_500 | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP07_preinh_500/Train) · [Test](SelectivityPresynapticInhib/EXP07_preinh_500/Test) |
| EXP08_preinh_600 | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP08_preinh_600/Train) · [Test](SelectivityPresynapticInhib/EXP08_preinh_600/Test) |
| EXP09_preinh_1000 | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP09_preinh_1000/Train) · [Test](SelectivityPresynapticInhib/EXP09_preinh_1000/Test) |
| EXP10_preinh_180 | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP10_preinh_180/Train) · [Test](SelectivityPresynapticInhib/EXP10_preinh_180/Test) |
| EXP11_preinh_210 | 6/8 | да | selective | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP11_preinh_210/Train) · [Test](SelectivityPresynapticInhib/EXP11_preinh_210/Test) |
| EXP12_preinh_220 | 6/8 | да | selective | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP12_preinh_220/Train) · [Test](SelectivityPresynapticInhib/EXP12_preinh_220/Test) |
| EXP13_preinh_240 | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP13_preinh_240/Train) · [Test](SelectivityPresynapticInhib/EXP13_preinh_240/Test) |
| EXP_span100ms_preinh250_C1e9 | 6/8 | да | selective | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP_span100ms_preinh250_C1e9/Train) · [Test](SelectivityPresynapticInhib/EXP_span100ms_preinh250_C1e9/Test) |
| EXP_span25ms_preinh250_C1e9 | 5/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP_span25ms_preinh250_C1e9/Train) · [Test](SelectivityPresynapticInhib/EXP_span25ms_preinh250_C1e9/Test) |
| EXP_span50ms_preinh250_C1e9 | 4/8 | да | partial_FA | **NOT_RETESTED** | [Train](SelectivityPresynapticInhib/EXP_span50ms_preinh250_C1e9/Train) · [Test](SelectivityPresynapticInhib/EXP_span50ms_preinh250_C1e9/Test) |

---

## Каталог на диске вне строк

| Семья / класс | Примечание |
|---------------|------------|
| `.bak_phase12_*`, `*_ampaudit`, `*_Dspan` | бэкапы / diag |
| `EXP_br480_diag_*`, Phase6 foil6 / phase9–10 variants | диагностические клоны |
| `AsymRmLtzCalBranch` ×6 | stall; OUT |
| `BranchFastSpan`, `FastSpanLtzCal`, smoke | T5 / OUT |
| `SelectivityFastResponse` ×11 | вне объёма tiprmin |
| PSI EXP без last-pulse в прежнем реестре | см. сводку ok_audit выше |
| XOR, SpikeTrainer, SpikeAnsTrainer | вне selectivity line |

---

## Риск при NOT_RETESTED

| Риск | Когда | Примеры |
|------|-------|---------|
| **high** | SoftCold Train+PostTune; Search/Keep | §A FAIL; br480; nextseg100; FastSpan25 |
| **med** | GoldTest на старых весах | Asym50/100; Phase6 7/8; Branch short packA |
| **low** | MatrixClone B/C; ARTIFACT partial_FA | VALIDATED_CLONE; Phase A / PSI |

---

## Указатели

| Документ | Роль |
|----------|------|
| [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md) | только HEAD PASS |
| [`PHASE12_VALIDATION.md`](PHASE12_VALIDATION.md) | исторические cold-бейджи |
| [`RELIABILITY_MAP.ru.md`](RELIABILITY_MAP.ru.md) | T1–T5 |
| [`POST_TRAIN_VERIFY.ru.md`](POST_TRAIN_VERIFY.ru.md) | контракт PostTune |
| [`EXPERIMENTS_AFTER_FIXES.ru.md`](../../../Docs/Audit/TimeLearner-2026-09-24-review/EXPERIMENTS_AFTER_FIXES.ru.md) | narrative cold |
| [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv) | gate CSV |
| [`LAYOUT.md`](LAYOUT.md) | раскладка |


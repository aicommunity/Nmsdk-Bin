# Реестр экспериментов StructTrain (полный)

**Срез HEAD 2026-09-26:** Console SHA-256 `ec86430e871e9314d61b948565581705bf72116516f32bb79c5091994c4a1a47` (PulseLib eps TL-01 fix) · PulseLib `f3763f3` · Bin *(this commit: harness failure_class/provenance + asym25 P2 note)* · GoldTest wave G historically used Console `4917a2bc…`.

Ось таблиц — **исследуемый алгоритм + параметры** (learner, span, рычаг, pack, TipR-режим рецепта).
Повторный cold/PostTune на текущем HEAD — **не отдельный эксперимент**, а строка(и) того же алгоритма с другим протоколом и вердиктом HEAD.
Только PASS → [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md).
Контракт cold: [`POST_TRAIN_VERIFY.ru.md`](POST_TRAIN_VERIFY.ru.md). Narrative доработок измерения: [`EXPERIMENTS_AFTER_FIXES.ru.md`](../../../Docs/Audit/TimeLearner-2026-09-24-review/EXPERIMENTS_AFTER_FIXES.ru.md) (не ось реестра).
T1–T5 → [`RELIABILITY_MAP.ru.md`](RELIABILITY_MAP.ru.md); **вердикт только колонка HEAD**.

## Антипутаница

1. Одно ядро алгоритма = одно **Имя** (канонический EXP). PostTune-клоны (`…_posttune`) — рабочие каталоги прогона; в таблице ссылаются из Конфиги, не подменяют имя.
2. Разные протоколы одного алгоритма — соседние строки с тем же Именем (GoldTest / SoftCold / SkipTrainGold / …).
3. PHASE12 `VALIDATED` ≠ HEAD PASS. Без прогона на этом срезе → NOT_RETESTED.
4. TipR Canon/Keep/Search/Flat и PostTune on/off — **параметры рецепта**, не новые семьи.
5. Гипотезы soft vs strip / AutoScale 0|1 без различия — примечание к SoftCold, не отдельные строки-алгоритмы.
6. Pack B/C = MatrixClone того же рецепта packA.

## Легенда HEAD

| Статус | Смысл |
|--------|--------|
| **PASS** | Подтверждено на текущем HEAD |
| **FAIL** | Повторено на HEAD → не проходит контракт |
| **NOT_RETESTED** | На HEAD не гоняли; Acc/Цель — last-known на диске |

## Колонки

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |

- **Имя** — канонический короткий id алгоритма. Путь Train/Test/CSV и bundle — в **Конфиги**.
- **Acc** — успешные пробы / 8. `—` если gate CSV нет.
- **Цель** — срабатывание на целевом примере (`да`/`нет`/`—`). При Acc&lt;8/8 обязательно.
- **Протокол** — что измеряли: `GoldTest` (веса на диске) · `SoftCold+PostTune` · `SkipTrainGold` · `MatrixClone` · `SoftCold+PostTuneOff`.

## Как обновлять

1. Новый прогон того же алгоритма → добавить/обновить строку с нужным протоколом рядом с каноном; PASS синхронизировать в SUCCESSFUL.
2. Cold: `scripts/posttune_verify.py`, clean workdir; клон `…_posttune` только как work root.
3. Не заводить отдельную секцию «кампания retest».

---

## 1. Branch short-span C1e9

Алгоритм: `NNeuronTimeLearnerBranch`, ёмкость 1e9, TipR@Rmin (кроме span100 gen — Done TipR), mid по soma.

### 1.1. packA gen — span 25 мс

Канон: `EXP_br_span25_packA_gen_C1e9`. Ниже — тот же алгоритм: gold на диске и прогоны на HEAD.

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br_span25_packA_gen_C1e9 | NNeuronTimeLearnerBranch | L=`13 11 7 1` TipR@Rmin thr≈0.0718 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known на диске | [Train](SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packA_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packA_gen_C1e9 | NNeuronTimeLearnerBranch | те же веса; TipR canon mid≈0.0718 | SkipTrainGold | 8/8 | да | selective | **PASS** | — | контроль контура; fires `10000000` | [posttune-клон](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune) · [`bundle`](_repro/runs/br25_on_20260924T165949Z) |
| EXP_br_span25_packA_gen_C1e9 | NNeuronTimeLearnerBranch | TipRMode=CanonRmin; soft-cold L≈`1 1 1 1` | SoftCold+PostTune | — | — | — | **FAIL** | — | NonSeparable mid=1; soft≡strip; AutoScale 0≡1 — см. T3_H3/H4 | [posttune-клон](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune) · [`bundle`](_repro/runs/br25_on_20260924T170503Z) · [`H1`](../../../Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/T3_H1_canon_vs_keep.json) · [`H3`](../../../Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/T3_H3_soft_vs_strip.json) · [`H4`](../../../Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/T3_H4_autoscale.json) |
| EXP_br_span25_packA_gen_C1e9 | NNeuronTimeLearnerBranch | TipRMode=KeepDone | SoftCold+PostTune | — | — | — | **FAIL** | — | NonSeparable (не только Canon) | [posttune-клон](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune) · [`H1`](../../../Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/T3_H1_canon_vs_keep.json) |
| EXP_br_span25_packA_gen_C1e9 | NNeuronTimeLearnerBranch | EnablePostTrainTuning=0 | SoftCold+PostTuneOff | 6/8 | да | — | **FAIL** | — | fires `10110000` (2 FA); mid≈0.108833 | [клон off](SelectivityBranch/EXP_br_span25_packA_gen_C1e9_posttune_off) · [`bundle`](_repro/runs/br25_off_20260924T204259Z) |

### 1.2. packA gen — span 50 / 100 мс

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br_span50_packA_gen_C1e9 | NNeuronTimeLearnerBranch | L=`13 11 6 1` TipR@Rmin thr≈0.0644 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packA_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packA_gen_C1e9 | NNeuronTimeLearnerBranch | L=`25 21 11 1` Done TipR thr≈0.00718 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packA_gen_C1e9/Test/SelectivityLog/results.csv) |

### 1.3. packA gen span 100 — TipR Keep / Search (тот же канон, PostTune-режимы)

Канон тот же `EXP_br_span100_packA_gen_C1e9`; отличаются только TipRMode при SoftCold.

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br_span100_packA_gen_C1e9 | NNeuronTimeLearnerBranch | TipRMode=KeepDone | SoftCold+PostTune | — | — | — | **FAIL** | — | NonSeparable; tipr≈snapshot | [клон keep](SelectivityBranch/EXP_br_span100_packA_gen_C1e9_posttune_keep) · [`bundle`](_repro/runs/br100_keep_20260924T234016Z) |
| EXP_br_span100_packA_gen_C1e9 | NNeuronTimeLearnerBranch | TipRMode=SearchSynthetic | SoftCold+PostTune | 0/8 | нет | — | **FAIL** | — | fires `00000000`; same_reverted | [клон search](SelectivityBranch/EXP_br_span100_packA_gen_C1e9_posttune_search) · [`bundle`](_repro/runs/br100_search_20260925T015547Z) |

### 1.4. packA preinh

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br_span25_packA_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | L=`7 6 4 1` TipR@Rmin thr≈0.0517 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packA_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packA_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | L=`13 11 6 1` TipR@Rmin thr≈0.0301 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packA_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packA_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | L=`22 18 11 1` TipR@Rmin thr≈0.0203 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packA_preinh_C1e9/Test/SelectivityLog/results.csv) |

### 1.5. packA nextseg

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br_span25_packA_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | L=`13 11 7 1` thr≈0.0476 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packA_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packA_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | L=`13 11 6 1` thr≈0.0413 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packA_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packA_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | L=`21 17 11 1` thr≈0.0144 | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: PHASE12 soft-cold L stuck; gold kept | [Train](SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packA_nextseginh_C1e9/Test/SelectivityLog/results.csv) |

### 1.6. pack B/C (MatrixClone того же рецепта packA)

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br_span25_packB_gen_C1e9 | NNeuronTimeLearnerBranch | packB matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packB_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packB_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packB matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packB_gen_C1e9 | NNeuronTimeLearnerBranch | packB matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packB_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packB_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packB matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packB_gen_C1e9 | NNeuronTimeLearnerBranch | packB matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packB_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packB_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packB matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packC_gen_C1e9 | NNeuronTimeLearnerBranch | packC matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packC_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packC_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packC matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packC_gen_C1e9 | NNeuronTimeLearnerBranch | packC matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packC_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packC_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packC matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packC_gen_C1e9 | NNeuronTimeLearnerBranch | packC matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packC_gen_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packC_preinh_C1e9 | NNeuronTimeLearnerBranch + Preinh | packC matrix-only | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packB_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packB nextseg | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packB_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packB_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packB nextseg | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packB_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packB_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packB nextseg | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packB_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span25_packC_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packC nextseg | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span25_packC_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span50_packC_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packC nextseg | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span50_packC_nextseginh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_br_span100_packC_nextseginh_C1e9 | NNeuronTimeLearnerBranch + NextSeg | packC nextseg | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Train) · [Test](SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Test) · [CSV](SelectivityBranch/EXP_br_span100_packC_nextseginh_C1e9/Test/SelectivityLog/results.csv) |

---

## 2. Branch ~480 мс tiprmin

Acc — GoldTest на диске. Soft-cold в PHASE12 не воспроизвёл; на текущем HEAD отдельного cold не было.

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br480_tiprmin | NNeuronTimeLearnerBranch | TipR@Rmin thr=0.05149 | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityBranch/EXP_br480_tiprmin/Train) · [Test](SelectivityBranch/EXP_br480_tiprmin/Test) · [CSV](SelectivityBranch/EXP_br480_tiprmin/Test/SelectivityLog/results.csv) |
| EXP_br480_nextseginh_tiprmin | NNeuronTimeLearnerBranch + NextSeg | NextSeg tiprmin thr=0.036298 | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityBranch/EXP_br480_nextseginh_tiprmin/Train) · [Test](SelectivityBranch/EXP_br480_nextseginh_tiprmin/Test) · [CSV](SelectivityBranch/EXP_br480_nextseginh_tiprmin/Test/SelectivityLog/results.csv) |
| EXP_br480_preinh250_tiprmin | NNeuronTimeLearnerBranch + Preinh | Preinh2.5 tiprmin thr=0.111136 | GoldTest | 7/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest  Console=4917a2bcbac318d1 fires=10001000; was: last-known GoldTest; 1 FA на фольге | [Train](SelectivityBranch/EXP_br480_preinh250_tiprmin/Train) · [Test](SelectivityBranch/EXP_br480_preinh250_tiprmin/Test) · [CSV](SelectivityBranch/EXP_br480_preinh250_tiprmin/Test/SelectivityLog/results.csv) |

---

## 3. AsymRm short-span

Алгоритм: `NNeuronTimeLearner`, рецепт C1e9 + tip-resistance.

### 3.1. span 25 мс packA gen

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_span25ms_packA_gen | NNeuronTimeLearner | C1e9 TipR base thr≈0.00962 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityAsymRm/EXP_span25ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packA_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packA_gen | NNeuronTimeLearner | TipRMode=FlatLastR `8.6e7×4` | SoftCold+PostTune | — | — | — | **FAIL** | — | NonSeparable; mid=1 | [posttune-клон](SelectivityAsymRm/EXP_span25ms_packA_gen_posttune) · [`bundle`](_repro/runs/asym25_20260924T214120Z) |

### 3.2. span 50 мс packA gen

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_span50ms_packA_gen | NNeuronTimeLearner | TipR@Rmin thr=0.011759 L=`25 23 15 1` | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T123946Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityAsymRm/EXP_span50ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packA_gen/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packA_gen | NNeuronTimeLearner | TipRMode=CanonRmin; Train~640 с | SoftCold+PostTune | 8/8 | да | selective | **FAIL** | — | Need=1 (FAIL приёмки); Test fires `10000000` | [posttune-клон](SelectivityAsymRm/EXP_span50ms_packA_gen_posttune) · [`bundle`](_repro/runs/asym50_20260924T214908Z) |

### 3.3. Остальные AsymRm (GoldTest / MatrixClone, на HEAD не перепрогонялись)

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_span25ms_packA_preinh | NNeuronTimeLearner | span25 Preinh2.5 thr≈0.00469 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityAsymRm/EXP_span25ms_packA_preinh/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packA_preinh/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packB_gen | NNeuronTimeLearner | span25 packB | MatrixClone | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span25ms_packB_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packB_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packB_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packC_gen | NNeuronTimeLearner | span25 packC | MatrixClone | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span25ms_packC_gen/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packC_gen/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packC_gen/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packB_preinh_C1e9 | NNeuronTimeLearner | span25 packB preinh | MatrixClone | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span25ms_packC_preinh_C1e9 | NNeuronTimeLearner | span25 packC preinh | MatrixClone | 8/8 | да | selective | **PASS** | VALIDATED_CLONE | GoldTest  Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span25ms_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packA_preinh | NNeuronTimeLearner | span50 Preinh thr=0.011759 | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T125815Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityAsymRm/EXP_span50ms_packA_preinh/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packA_preinh/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packB_gen | NNeuronTimeLearner | span50 packB | MatrixClone | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T125813Z Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span50ms_packB_gen/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packB_gen/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packB_gen/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packC_gen | NNeuronTimeLearner | span50 packC | MatrixClone | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T125755Z Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span50ms_packC_gen/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packC_gen/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packC_gen/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packB_preinh_C1e9 | NNeuronTimeLearner | span50 packB preinh | MatrixClone | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T131603Z Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span50ms_packC_preinh_C1e9 | NNeuronTimeLearner | span50 packC preinh | MatrixClone | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T131543Z Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span50ms_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packA_gen | NNeuronTimeLearner | span100 TipR@Rmin thr=0.006681 L=`52 48 27 1` | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T132051Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityAsymRm/EXP_span100ms_packA_gen/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packA_gen/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packA_gen/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packA_preinh | NNeuronTimeLearner | span100 Preinh thr=0.006681 | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T132049Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityAsymRm/EXP_span100ms_packA_preinh/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packA_preinh/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packA_preinh/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packB_gen | NNeuronTimeLearner | span100 packB | MatrixClone | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T133820Z Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span100ms_packB_gen/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packB_gen/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packB_gen/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packC_gen | NNeuronTimeLearner | span100 packC | MatrixClone | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T133844Z Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span100ms_packC_gen/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packC_gen/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packC_gen/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packB_preinh_C1e9 | NNeuronTimeLearner | span100 packB preinh | MatrixClone | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T134325Z Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packB_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_packC_preinh_C1e9 | NNeuronTimeLearner | span100 packC preinh | MatrixClone | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T134323Z Console=4917a2bcbac318d1 fires=10000000; was: MatrixClone last-known | [Train](SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Train) · [Test](SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Test) · [CSV](SelectivityAsymRm/EXP_span100ms_packC_preinh_C1e9/Test/SelectivityLog/results.csv) |

---

## 4. AsymRmLtzCal twin

Тот же классический learner; копия/sync с AsymRm. Имя с префиксом `LtzCal/`.

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| LtzCal/EXP_span25ms_packA_gen | NNeuronTimeLearner (LtzCal twin) | twin sync AsymRm span25 | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest 20260925T134339Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_gen/Test/SelectivityLog/results.csv) |
| LtzCal/EXP_span25ms_packA_preinh | NNeuronTimeLearner (LtzCal twin) | twin sync AsymRm span25 preinh | GoldTest | 8/8 | да | selective | **PASS** | VALIDATED | GoldTest 20260925T134857Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span25ms_packA_preinh/Test/SelectivityLog/results.csv) |
| LtzCal/EXP_span50ms_packA_gen | NNeuronTimeLearner (LtzCal twin) | twin span50 thr=0.011759 | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T140052Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_gen/Test/SelectivityLog/results.csv) |
| LtzCal/EXP_span50ms_packA_preinh | NNeuronTimeLearner (LtzCal twin) | twin span50 preinh | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T140102Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span50ms_packA_preinh/Test/SelectivityLog/results.csv) |
| LtzCal/EXP_span100ms_packA_gen | NNeuronTimeLearner (LtzCal twin) | twin span100 thr=0.006681 | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T140500Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_gen/Test/SelectivityLog/results.csv) |
| LtzCal/EXP_span100ms_packA_preinh | NNeuronTimeLearner (LtzCal twin) | twin span100 preinh | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T140939Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Train) · [Test](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Test) · [CSV](SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span100ms_packA_preinh/Test/SelectivityLog/results.csv) |

---

## 5. Phase6 ~480 мс tiprmin

### 5.1. gen tiprmin (канон волны)

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| Phase6/EXP_480_gen_tiprmin | NNeuronTimeLearner | TipR@Rmin thr=0.016894 | GoldTest | 7/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T140316Z Console=4917a2bcbac318d1 fires=10000010; was: last-known GoldTest; 1 FA на фольге | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin/Test/SelectivityLog/results.csv) |
| Phase6/EXP_480_gen_tiprmin | NNeuronTimeLearner | TipRMode=CanonRmin | SoftCold+PostTune | — | — | — | **FAIL** | — | Need=1; Test NonSeparable mid=1 | [posttune-клон](SelectivityPhaseA/Phase6/EXP_480_gen_posttune) · [`bundle`](_repro/runs/phase6_480_20260924T234719Z) |

### 5.2. Прочие Phase6 tiprmin (на HEAD не перепрогонялись)

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| Phase6/EXP_480_gen_thr_only | NNeuronTimeLearner | mid-thr=0.014386 TipR Done | GoldTest | 7/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T140326Z Console=4917a2bcbac318d1 fires=10000010; was: last-known GoldTest; 1 FA на фольге | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_gen_thr_only/Test/SelectivityLog/results.csv) |
| Phase6/EXP_480_preinh250_tiprmin | NNeuronTimeLearner | Preinh2.5 TipR@Rmin thr=0.038722 | GoldTest | 7/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T140556Z Console=4917a2bcbac318d1 fires=10000010; was: last-known GoldTest; 1 FA на фольге | [Train](SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_preinh250_tiprmin/Test/SelectivityLog/results.csv) |
| Phase6/EXP_480_ltzcal_twin_gen | NNeuronTimeLearner | twin tiprmin | GoldTest | 2/8 | да | partial_FA | **FAIL** | ARTIFACT_KEEP | GoldTest 20260925T140550Z Console=4917a2bcbac318d1 fires=11110111; was: last-known GoldTest; 1 FA на фольге | [Train](SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen/Test) · [CSV](SelectivityPhaseA/Phase6/EXP_480_ltzcal_twin_gen/Test/SelectivityLog/results.csv) |

---

## 6. FastSpan C1e9

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_span25ms_fast_C1e9 | NNeuronTimeLearner (FastSpan) | AsymRmD001C1e9 thr=0.0328372 | GoldTest | 8/8 | да | selective | **PASS** | FAIL_ROOTCAUSE | GoldTest 20260925T140937Z Console=4917a2bcbac318d1 fires=10000000; was: PHASE12 FAIL_ROOTCAUSE; last-known gold | [Train](SelectivityFastSpan/EXP_span25ms_fast_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span25ms_fast_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span25ms_fast_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span25ms_fast_preinh_C1e9 | NNeuronTimeLearner (FastSpan) | Preinh2_5 thr=0.01563085 | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T141025Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span25ms_fast_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span50ms_fast_preinh_C1e9 | NNeuronTimeLearner (FastSpan) | Preinh2_5 thr=0.0112976 | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T141235Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span50ms_fast_preinh_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_fast_C1e9 | NNeuronTimeLearner (FastSpan) | AsymRmD001C1e9 thr=0.01568185 | GoldTest | 7/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T142019Z Console=4917a2bcbac318d1 fires=10100000; was: last-known; 1 FA на фольге | [Train](SelectivityFastSpan/EXP_span100ms_fast_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span100ms_fast_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span100ms_fast_C1e9/Test/SelectivityLog/results.csv) |
| EXP_span100ms_fast_preinh_C1e9 | NNeuronTimeLearner (FastSpan) | Preinh2_5 thr=0.00708053 | GoldTest | 8/8 | да | selective | **PASS** | ARTIFACT_KEEP | GoldTest 20260925T142025Z Console=4917a2bcbac318d1 fires=10000000; was: last-known GoldTest | [Train](SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Test) · [CSV](SelectivityFastSpan/EXP_span100ms_fast_preinh_C1e9/Test/SelectivityLog/results.csv) |

---

## 7. Phase A / TimeNeuron / PSI (старый набор)

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP00_baseline | NNeuronTimeLearner | порог 0.0115 | GoldTest | 4/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T142916Z Console=4917a2bcbac318d1 fires=10101110; was: last-known GoldTest | [Train](SelectivityPhaseA/EXP00_baseline/Train) · [Test](SelectivityPhaseA/EXP00_baseline/Test) · [CSV](SelectivityPhaseA/EXP00_baseline/Test/SelectivityLog/results.csv) |
| EXP01_ltz_threshold_sweep | NNeuronTimeLearner | порог FixedLTZ | GoldTest | 6/8 | да | selective | **PASS** | ARTIFACT | GoldTest 20260925T141455Z Console=4917a2bcbac318d1 fires=10001010; was: last-known GoldTest | [Train](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Train) · [Test](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Test) · [CSV](SelectivityPhaseA/EXP01_ltz_threshold_sweep/Test/SelectivityLog/results.csv) |
| EXP02_ltzone_average_mode | NNeuronTimeLearner | UseAverageLTZonePotential | GoldTest | 4/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T141501Z Console=4917a2bcbac318d1 fires=10101110; was: last-known GoldTest | [Train](SelectivityPhaseA/EXP02_ltzone_average_mode/Train) · [Test](SelectivityPhaseA/EXP02_ltzone_average_mode/Test) · [CSV](SelectivityPhaseA/EXP02_ltzone_average_mode/Test/SelectivityLog/results.csv) |
| EXP06_ltzone_integration | NNeuronTimeLearner | LTZone τ | GoldTest | 4/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T141729Z Console=4917a2bcbac318d1 fires=10101110; was: last-known GoldTest | [Train](SelectivityPhaseA/EXP06_ltzone_integration/Train) · [Test](SelectivityPhaseA/EXP06_ltzone_integration/Test) · [CSV](SelectivityPhaseA/EXP06_ltzone_integration/Test/SelectivityLog/results.csv) |
| TimeNeuronTimeLearner | NNeuronTimeLearner | классический канон | GoldTest | 4/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T141725Z Console=4917a2bcbac318d1 fires=10101110; was: last-known GoldTest | [Train](TimeNeuronTimeLearner/Train) · [Test](TimeNeuronTimeLearner/Test) · [CSV](TimeNeuronTimeLearner/Test/SelectivityLog/results.csv) |
| EXP01_preinh_050 | NNeuronTimeLearner + Preinh | preinh k=0.5 | GoldTest | 4/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T141953Z Console=4917a2bcbac318d1 fires=10101110; was: last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP01_preinh_050/Train) · [Test](SelectivityPresynapticInhib/EXP01_preinh_050/Test) · [CSV](SelectivityPresynapticInhib/EXP01_preinh_050/Test/SelectivityLog/results.csv) |
| EXP14_preinh_260 | NNeuronTimeLearner + Preinh | preinh k=2.6 | GoldTest | 6/8 | да | selective | **PASS** | ARTIFACT | GoldTest 20260925T142003Z Console=4917a2bcbac318d1 fires=10001010; was: last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP14_preinh_260/Train) · [Test](SelectivityPresynapticInhib/EXP14_preinh_260/Test) · [CSV](SelectivityPresynapticInhib/EXP14_preinh_260/Test/SelectivityLog/results.csv) |
| EXP15_preinh_270 | NNeuronTimeLearner + Preinh | preinh k=2.7 | GoldTest | 5/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T142230Z Console=4917a2bcbac318d1 fires=10101010; was: last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP15_preinh_270/Train) · [Test](SelectivityPresynapticInhib/EXP15_preinh_270/Test) · [CSV](SelectivityPresynapticInhib/EXP15_preinh_270/Test/SelectivityLog/results.csv) |
| EXP21_span100ms_preinh250 | NNeuronTimeLearner + Preinh | span 100 мс + k=2.5 | GoldTest | 5/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T142049Z Console=4917a2bcbac318d1 fires=11110000; was: last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Test/SelectivityLog/results.csv) |
| EXP31_span200ms_preinh250 | NNeuronTimeLearner + Preinh | span 200 мс + k=2.5 | GoldTest | 5/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T142139Z Console=4917a2bcbac318d1 fires=10110010; was: last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP31_span200ms_preinh250/Test/SelectivityLog/results.csv) |
| EXP32_span300ms_baseline | NNeuronTimeLearner | span 300 мс baseline | GoldTest | 4/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T142209Z Console=4917a2bcbac318d1 fires=10101110; was: last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP32_span300ms_baseline/Train) · [Test](SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test) · [CSV](SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test/SelectivityLog/results.csv) |
| EXP33_span300ms_preinh250 | NNeuronTimeLearner + Preinh | span 300 мс + k=2.5 | GoldTest | 4/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T142240Z Console=4917a2bcbac318d1 fires=10101110; was: last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Test/SelectivityLog/results.csv) |
| EXP34_span400ms_baseline | NNeuronTimeLearner | span 400 мс baseline | GoldTest | 4/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T142354Z Console=4917a2bcbac318d1 fires=10101110; was: last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP34_span400ms_baseline/Train) · [Test](SelectivityPresynapticInhib/EXP34_span400ms_baseline/Test) · [CSV](SelectivityPresynapticInhib/EXP34_span400ms_baseline/Test/SelectivityLog/results.csv) |
| EXP35_span400ms_preinh250 | NNeuronTimeLearner + Preinh | span 400 мс + k=2.5 | GoldTest | 5/8 | да | partial_FA | **PASS** | ARTIFACT | GoldTest 20260925T142424Z Console=4917a2bcbac318d1 fires=10101010; was: last-known GoldTest | [Train](SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Train) · [Test](SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Test) · [CSV](SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Test/SelectivityLog/results.csv) |

---

## SoftCold wave C (auto)

| Имя | Алгоритм | Параметры | Протокол | Acc | Цель | Режим | HEAD | PHASE12 | Примечание | Конфиги |
|-----|----------|-----------|----------|-----|------|-------|------|----------|------------|---------|
| EXP_br_span50_packA_gen_C1e9 | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`br50_gen` rc=1; bundle=`_repro/runs/br50_gen_20260925T144420Z` | `posttune_verify --case br50_gen` |
| EXP_br_span25_packA_preinh_C1e9 | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`br25_preinh` rc=1; bundle=`_repro/runs/br25_preinh_20260925T145223Z` | `posttune_verify --case br25_preinh` |
| EXP_br_span50_packA_preinh_C1e9 | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`br50_preinh` rc=1; bundle=`_repro/runs/br50_preinh_20260925T152911Z` | `posttune_verify --case br50_preinh` |
| EXP_br_span100_packA_preinh_C1e9 | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`br100_preinh` rc=1; bundle=`_repro/runs/br100_preinh_20260925T153639Z` | `posttune_verify --case br100_preinh` |
| EXP_br_span25_packA_nextseginh_C1e9 | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`br25_nextseg` rc=1; bundle=`_repro/runs/br25_nextseg_20260925T154453Z` | `posttune_verify --case br25_nextseg` |
| EXP_br_span50_packA_nextseginh_C1e9 | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`br50_nextseg` rc=1; bundle=`_repro/runs/br50_nextseg_20260925T155256Z` | `posttune_verify --case br50_nextseg` |
| EXP_br_span100_packA_nextseginh_C1e9 | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`br100_nextseg` rc=1; bundle=`_repro/runs/br100_nextseg_20260925T162024Z` | `posttune_verify --case br100_nextseg` |
| EXP_br480_tiprmin | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`br480_tiprmin` rc=1; bundle=`_repro/runs/br480_tiprmin_20260925T172303Z` | `posttune_verify --case br480_tiprmin` |
| EXP_br480_nextseginh_tiprmin | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`br480_nextseg` rc=1; bundle=`_repro/runs/br480_nextseg_20260925T182925Z` | `posttune_verify --case br480_nextseg` |
| EXP_br480_preinh250_tiprmin | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`br480_preinh` rc=1; bundle=`_repro/runs/br480_preinh_20260925T195700Z` | `posttune_verify --case br480_preinh` |
| EXP_span25ms_packA_preinh | — | SoftCold wave C / P2 A/B | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`asym25_preinh` Console=`ec86430e` Need=0 tipr=canon mid=1 (silent) fires_missing gate_rc=1 failure_class=gate_fail; eps-fix: Train completes vs stall risk; quality still NonSeparable; bundles=`_repro/runs/asym25_preinh_20260926T110401Z` (patched) · `_repro/runs/asym25_preinh_20260925T211629Z` (unpatched) | `posttune_verify --case asym25_preinh` |
| EXP_span50ms_packA_preinh | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`asym50_preinh` rc=1; bundle=`_repro/runs/asym50_preinh_20260925T212603Z` | `posttune_verify --case asym50_preinh` |
| EXP_span100ms_packA_gen | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`asym100_gen` rc=1; bundle=`_repro/runs/asym100_gen_20260926T002121Z` | `posttune_verify --case asym100_gen` |
| EXP_span100ms_packA_preinh | — | SoftCold wave C | SoftCold+PostTune | — | — | — | **FAIL** | — | SoftCold case=`asym100_preinh` rc=1; bundle=`_repro/runs/asym100_preinh_20260926T034443Z` | `posttune_verify --case asym100_preinh` |

## SoftCold wave C DEFER (остаток C1 + C2)

Wall-clock stop 2026-09-26: C1 **14 FAIL** в `_repro/SOFTCOLD_C_rcs.txt`; остаток C1 + C2 — явный DEFER.

### Остаток C1

| Имя | case id | Примечание |
|-----|---------|------------|
| Phase6/EXP_480_gen_thr_only | phase6_thr_only | SoftCold DEFER (batch stopped) |
| Phase6/EXP_480_preinh250_tiprmin | phase6_preinh250 | SoftCold DEFER (batch stopped) |
| Phase6/EXP_480_ltzcal_twin_gen | phase6_ltzcal_twin | SoftCold DEFER (batch stopped) |
| EXP_span25ms_fast_C1e9 | fs25_gen | SoftCold DEFER (batch stopped) |
| EXP_span25ms_fast_preinh_C1e9 | fs25_preinh | SoftCold DEFER (batch stopped) |
| EXP_span50ms_fast_preinh_C1e9 | fs50_preinh | SoftCold DEFER (batch stopped) |
| EXP_span100ms_fast_C1e9 | fs100_gen | SoftCold DEFER (batch stopped) |
| EXP_span100ms_fast_preinh_C1e9 | fs100_preinh | SoftCold DEFER (batch stopped) |

### C2

| Имя | case id | Примечание |
|-----|---------|------------|
| LtzCal/EXP_span25ms_packA_gen | ltz25_gen | SoftCold DEFER after C1 |
| LtzCal/EXP_span25ms_packA_preinh | ltz25_preinh | SoftCold DEFER after C1 |
| LtzCal/EXP_span50ms_packA_gen | ltz50_gen | SoftCold DEFER after C1 |
| LtzCal/EXP_span50ms_packA_preinh | ltz50_preinh | SoftCold DEFER after C1 |
| LtzCal/EXP_span100ms_packA_gen | ltz100_gen | SoftCold DEFER after C1 |
| LtzCal/EXP_span100ms_packA_preinh | ltz100_preinh | SoftCold DEFER after C1 |
| EXP00_baseline | pa00_baseline | SoftCold DEFER after C1 |
| EXP01_ltz_threshold_sweep | pa01_ltz_sweep | SoftCold DEFER after C1 |
| EXP02_ltzone_average_mode | pa02_ltzone_avg | SoftCold DEFER after C1 |
| EXP06_ltzone_integration | pa06_ltzone_int | SoftCold DEFER after C1 |
| TimeNeuronTimeLearner | tn_classic | SoftCold DEFER after C1 |
| EXP01_preinh_050 | psi01_050 | SoftCold DEFER after C1 |
| EXP14_preinh_260 | psi14_260 | SoftCold DEFER after C1 |
| EXP15_preinh_270 | psi15_270 | SoftCold DEFER after C1 |
| EXP21_span100ms_preinh250 | psi21_100 | SoftCold DEFER after C1 |
| EXP31_span200ms_preinh250 | psi31_200 | SoftCold DEFER after C1 |
| EXP32_span300ms_baseline | psi32_300 | SoftCold DEFER after C1 |
| EXP33_span300ms_preinh250 | psi33_300 | SoftCold DEFER after C1 |
| EXP34_span400ms_baseline | psi34_400 | SoftCold DEFER after C1 |
| EXP35_span400ms_preinh250 | psi35_400 | SoftCold DEFER after C1 |

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

Сводка [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv). GoldTest retest 2026-09-25 (см. `_repro/GOLD_RETEST_MERGED_20260925.csv`).

| Имя | Acc | Цель | Режим | HEAD | Конфиги |
|-----|-----|------|-------|------|---------|
| EXP00_baseline | 4/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP00_baseline/Train) · [Test](SelectivityPresynapticInhib/EXP00_baseline/Test) |
| EXP00_baseline_autothr | 4/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP00_baseline_autothr/Train) · [Test](SelectivityPresynapticInhib/EXP00_baseline_autothr/Test) |
| EXP00_baseline_margprops | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP00_baseline_margprops/Train) · [Test](SelectivityPresynapticInhib/EXP00_baseline_margprops/Test) |
| EXP02_preinh_100 | 4/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP02_preinh_100/Train) · [Test](SelectivityPresynapticInhib/EXP02_preinh_100/Test) |
| EXP03_preinh_200 | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP03_preinh_200/Train) · [Test](SelectivityPresynapticInhib/EXP03_preinh_200/Test) |
| EXP04_preinh_250 | 6/8 | да | selective | **PASS** | [Train](SelectivityPresynapticInhib/EXP04_preinh_250/Train) · [Test](SelectivityPresynapticInhib/EXP04_preinh_250/Test) |
| EXP04_preinh_250_margprops | 6/8 | да | selective | **PASS** | [Train](SelectivityPresynapticInhib/EXP04_preinh_250_margprops/Train) · [Test](SelectivityPresynapticInhib/EXP04_preinh_250_margprops/Test) |
| EXP04_preinh_250_recheck | 6/8 | да | selective | **PASS** | [Train](SelectivityPresynapticInhib/EXP04_preinh_250_recheck/Train) · [Test](SelectivityPresynapticInhib/EXP04_preinh_250_recheck/Test) |
| EXP04_sync_tolerance_010 | 4/8 | да | partial_FA | **PASS** | [Train](SelectivityPhaseA/EXP04_sync_tolerance_010/Train) · [Test](SelectivityPhaseA/EXP04_sync_tolerance_010/Test) |
| EXP05_preinh_300 | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP05_preinh_300/Train) · [Test](SelectivityPresynapticInhib/EXP05_preinh_300/Test) |
| EXP05_resistance_gain_025 | 4/8 | да | partial_FA | **PASS** | [Train](SelectivityPhaseA/EXP05_resistance_gain_025/Train) · [Test](SelectivityPhaseA/EXP05_resistance_gain_025/Test) |
| EXP06_preinh_400 | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP06_preinh_400/Train) · [Test](SelectivityPresynapticInhib/EXP06_preinh_400/Test) |
| EXP07_preinh_500 | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP07_preinh_500/Train) · [Test](SelectivityPresynapticInhib/EXP07_preinh_500/Test) |
| EXP08_preinh_600 | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP08_preinh_600/Train) · [Test](SelectivityPresynapticInhib/EXP08_preinh_600/Test) |
| EXP09_preinh_1000 | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP09_preinh_1000/Train) · [Test](SelectivityPresynapticInhib/EXP09_preinh_1000/Test) |
| EXP10_preinh_180 | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP10_preinh_180/Train) · [Test](SelectivityPresynapticInhib/EXP10_preinh_180/Test) |
| EXP11_preinh_210 | 6/8 | да | selective | **PASS** | [Train](SelectivityPresynapticInhib/EXP11_preinh_210/Train) · [Test](SelectivityPresynapticInhib/EXP11_preinh_210/Test) |
| EXP12_preinh_220 | 6/8 | да | selective | **PASS** | [Train](SelectivityPresynapticInhib/EXP12_preinh_220/Train) · [Test](SelectivityPresynapticInhib/EXP12_preinh_220/Test) |
| EXP13_preinh_240 | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP13_preinh_240/Train) · [Test](SelectivityPresynapticInhib/EXP13_preinh_240/Test) |
| EXP_span100ms_preinh250_C1e9 | 6/8 | да | selective | **PASS** | [Train](SelectivityPresynapticInhib/EXP_span100ms_preinh250_C1e9/Train) · [Test](SelectivityPresynapticInhib/EXP_span100ms_preinh250_C1e9/Test) |
| EXP_span25ms_preinh250_C1e9 | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP_span25ms_preinh250_C1e9/Train) · [Test](SelectivityPresynapticInhib/EXP_span25ms_preinh250_C1e9/Test) |
| EXP_span50ms_fast_C1e9 | 5/8 | да | partial_FA | **PASS** | [Train](SelectivityFastSpan/EXP_span50ms_fast_C1e9/Train) · [Test](SelectivityFastSpan/EXP_span50ms_fast_C1e9/Test) |
| EXP_span50ms_preinh250_C1e9 | 4/8 | да | partial_FA | **PASS** | [Train](SelectivityPresynapticInhib/EXP_span50ms_preinh250_C1e9/Train) · [Test](SelectivityPresynapticInhib/EXP_span50ms_preinh250_C1e9/Test) |
| Phase6/EXP_480_gen_baseline | 4/8 | да | partial_FA | **PASS** | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_baseline/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_baseline/Test) |
| Phase6/EXP_480_gen_tiprmin_phase10_done_tipr | 7/8 | да | selective | **PASS** | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase10_done_tipr/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase10_done_tipr/Test) |
| Phase6/EXP_480_gen_tiprmin_phase9_foil6 | 7/8 | да | selective | **PASS** | [Train](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase9_foil6/Train) · [Test](SelectivityPhaseA/Phase6/EXP_480_gen_tiprmin_phase9_foil6/Test) |

---

## Риск при SoftCold FAIL / DEFER

| Риск | Когда | Примеры |
|------|-------|---------|
| **high** | SoftCold Train+PostTune | FAIL на HEAD (br25…asym100 C1); DEFER остаток |
| **med** | GoldTest на старых весах | Phase6 twin FAIL Acc 2/8 |
| **low** | MatrixClone GoldTest PASS | pack B/C |

---

## Указатели

| Документ | Роль |
|----------|------|
| [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md) | только HEAD PASS |
| [`POST_TRAIN_VERIFY.ru.md`](POST_TRAIN_VERIFY.ru.md) | контракт PostTune |
| [`EXPERIMENTS_AFTER_FIXES.ru.md`](../../../Docs/Audit/TimeLearner-2026-09-24-review/EXPERIMENTS_AFTER_FIXES.ru.md) | narrative доработок + цифры прогонов |
| [`AUDIT_GATE_RECOMPUTE.csv`](AUDIT_GATE_RECOMPUTE.csv) | gate CSV |
| [`LAYOUT.md`](LAYOUT.md) | раскладка |

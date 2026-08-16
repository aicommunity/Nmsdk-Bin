# REPORT: PSI time-compress (span 100/50/25/10 мс)

Сжатие ISI-паттерна × `NSPNeuronGen` (baseline) vs `NSPNeuronGenPreinh2_5` (k=2.5).  
Эталон несжатого: EXP00 **4/8**, EXP04 **6/8**.

## Протокол качества (Run2)

Источник: `Test/SelectivityLog/results.csv` (ровно 8 trials).

| Условие | Определение |
|--|--|
| `target_hit` | trial0: `neuron_fired=1` и `match=1` |
| `fire_all` | все 8 trials fired |
| **gate PASS** | `target_hit` ∧ ¬`fire_all` ∧ Acc≥4/8 |

Режимы: `selective` | `partial_FA` | `fire_all` | `miss_target` | `silent`.

Tune: cold train → при stall/nodone **climb SyncTol**; после Done — сетка Peak/Agree; accept только PASS. Best-of при исчерпании лимита.

Скрипты: `evaluate_selectivity_csv.py`, `run_time_compress.sh`, `tune_timing_params.py` (`--next-wider-after-sync`).

## Erratum Run1 (Done-only)

Acc без `neuron_fired` вводил в заблуждение. Run1 «tune» = widen SyncTol до Done, не quality-gate.

- GUI-наблюдение Run1: EXP20 без спайка на target; EXP26 fire-all.
- Сравнения «Preinh лучше baseline по Acc» из Run1 **отозваны**.

Сырые числа Run1 сохранены в §Run1 ниже.

## PulseLib

| Свойство | Default | Использование |
|--|--:|--|
| `PeakMeasureMargin` | 0.06 с | `margin = max(PeakMeasureMargin, 0.5·kMaxLengthStep·EstDelayPerSeg)` |
| `DelayAgreeMarginMin` | 0.03 с | `agree_margin = max(SyncTolerance, DelayAgreeMarginMin)` |

При `EstDelayPerSeg=0.01` пол `0.04 с` часто перекрывает XML Peak на коротких T.

## Setup

- ISI: `α = T/0.48`, `max(1.5 мс, v·α)`; `IterationGap=1.5` не трогали
- floor onset ISI: нет на 100 мс; да на 50/25/10 мс
- Timing в Parameters **и** Model; новые EXP не создавались

### Начальные timing

| T | α | SyncTol₀ | Peak₀ | Agree₀ |
|--:|--:|--:|--:|--:|
| 100 мс | 0.208 | 4.17 мс | 5.83 мс | 5.83 мс |
| 50 мс | 0.104 | 2.08 мс | 2.92 мс | 2.92 мс |
| 25 мс | 0.052 | 1.50 мс | 2.00 мс | 2.00 мс |
| 10 мс | 0.021 | 1.50 мс | 2.00 мс | 2.00 мс |

## Run2 (quality-tune) — главная таблица

| EXP | T | Neuron | Sync | Peak | Agree | L | thr | Acc | fires | mode | gate | tune |
|--|--:|--|--:|--:|--:|--|--:|--:|--|--|--|--:|
| EXP20 | 100 | baseline | 4.17 мс | 5.83 мс | 5.83 мс | `[12,11,7,1]` | 0.0147 | **2/8** | `11111110` | `partial_FA` | **FAIL** | 0 |
| EXP21 | 100 | Preinh2.5 | 4.17 мс | 5.83 мс | 5.83 мс | `[11,9,6,1]` | 0.0321 | **5/8** | `11110000` | `partial_FA` | **PASS** | 0 |
| EXP22 | 50 | baseline | 4.17 мс | 2.92 мс | 4.17 мс | `[7,6,5,1]` | 0.0174 | **1/8** | `11111111` | `fire_all` | **FAIL** | 2 |
| EXP23 | 50 | Preinh2.5 | 6.25 мс | 2.92 мс | 6.25 мс | `[5,5,4,1]` | 0.0340 | **3/8** | `11111100` | `partial_FA` | **FAIL** | 3 |
| EXP24 | 25 | baseline | 2.25 мс | 1.88 мс | 2.25 мс | `[4,4,3,1]` | 0.0195 | **3/8** | `11111100` | `partial_FA` | **FAIL** | 1 |
| EXP25 | 25 | Preinh2.5 | 3.00 мс | 1.88 мс | 3.00 мс | `[5,5,4,1]` | 0.0179 | **1/8** | `11111111` | `fire_all` | **FAIL** | 2 |
| EXP26 | 10 | baseline | 4.50 мс | 1.50 мс | 4.50 мс | `[3,3,2,1]` | 0.0234 | **1/8** | `11111111` | `fire_all` | **FAIL** | 5 |
| EXP27 | 10 | Preinh2.5 | 3.00 мс | 1.50 мс | 3.00 мс | `[4,4,3,1]` | 0.0115 | **1/8** | `11111111` | `fire_all` | **FAIL** | 4 |

Все EXP: `phase -> Done`, 8-row CSV. PulseLib / DissociationTC **не** менялись.

### Per-EXP (Run2)

- **EXP20:** target hit, но FA на 6/7 distractors → Acc 2/8, gate FAIL. Сетка Peak не улучшила Acc (15 попыток).
- **EXP21:** единственный **PASS** (5/8, fa=3). Сравнение baseline↔Preinh на 100 мс валидно: Preinh заметно лучше.
- **EXP22:** fire-all после Done; Peak-варианты при Sync≥4.17 мс не сняли FA.
- **EXP23:** partial_FA Acc 3/8 (лучше fire-all baseline), но <4 → FAIL.
- **EXP24:** partial_FA Acc 3/8 FAIL.
- **EXP25–27:** fire-all Acc 1/8 FAIL (селективности нет).

### Сравнение Run2

Сравнивать Acc **только** где оба не в `{fire_all, miss_target, silent}`:

| T | baseline | Preinh | Сравнение |
|--:|--|--|--|
| 100 мс | FAIL Acc2 `partial_FA` | **PASS Acc5** | Preinh лучше (валидно) |
| 50 мс | FAIL `fire_all` | FAIL Acc3 `partial_FA` | несравнимо / Preinh менее плох |
| 25 мс | FAIL Acc3 | FAIL `fire_all` | несравнимо / baseline менее плох |
| 10 мс | FAIL `fire_all` | FAIL `fire_all` | оба провал селективности |

Vs несжатый EXP00/04: сжатие **ломает** quality-gate на всех T кроме Preinh 100 мс.

## Run1 (Done-only) — архив

| EXP | Acc | tune | mode (оценка) | вердикт |
|--|--:|--:|--|--|
| EXP20 | 2/8 | 0 | miss_target (GUI) | unsatisfactory |
| EXP21 | 5/8 | 0 | selective/partial_FA | comparable |
| EXP22 | 1/8 | pre-widen | fire_all | unsatisfactory |
| EXP23 | 3/8 | pre-widen | partial_FA | weak |
| EXP24 | 3/8 | 1 | partial_FA | weak |
| EXP25 | 1/8 | 4 | fire_all | unsatisfactory |
| EXP26 | 1/8 | 6 | fire_all | unsatisfactory |
| EXP27 | 1/8 | 0† | fire_all | unsatisfactory |

† margins скопированы с EXP26.

## §Regression margprops (без изменений)

| Конфиг | Acc | Критерий |
|--|--:|--|
| EXP00_baseline_margprops | **5/8** | ≥4/8 OK |
| EXP04_preinh_250_margprops | **6/8** | ≥6/8 OK |

Не переучивались в Run2.

## Блокеры / эскалация

- На 10/25 мс (и baseline 50 мс) quality-tune **не** вывел из `fire_all` / Acc&lt;4: Peak XML бессилен при поле `0.5·8·EstDelayPerSeg=0.04 с`; ISI ≤ DissociationTC (5 мс) → smear.
- Следующая эскалация (вне этого прогона): правка формулы Peak / `EstDelayPerSeg` / DissociationTC — по отдельному запросу.

## Артефакты

- Конфиги: `EXP20`…`EXP27` (+ margprops)
- На EXP: `RESULT.txt`, `QUALITY.txt`, `tune_log.txt`, `Test/SelectivityLog/results.csv`
- Логи: `run_quality_100_50.log`, `run_quality_50_resume.log`, `run_quality_25_10.log`
- Скрипты: `evaluate_selectivity_csv.py`, `run_time_compress.sh`, `tune_timing_params.py`, `patch_pattern_scale.py`

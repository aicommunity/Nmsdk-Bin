# REPORT: PSI time-expand (span 200/300/400 мс)

Расширение ISI-паттерна (α=T/0.48 > 1) × `NSPNeuronGen` (baseline) vs `NSPNeuronGenPreinh2_5` (k=2.5).  
Эталон несжатого 0.48 с: EXP00 **4/8**, EXP04 **6/8**. Сжатие: [REPORT_time_compress.md](REPORT_time_compress.md).

## Протокол качества

Как Run2 time-compress: `evaluate_selectivity_csv.py`.

| Условие | Определение |
|--|--|
| `target_hit` | trial0 fired ∧ match |
| `fire_all` | все 8 fired |
| **gate PASS** | `target_hit` ∧ ¬`fire_all` ∧ Acc≥4/8 |

Tune: [`run_time_compress.sh`](scripts/run_time_compress.sh) (SyncTol climb + Peak grid; **без early stop** на первом PASS; best-of по Acc среди gate PASS).

## Anchor recheck (до EXP30 train)

Test-only (без cold retrain). Полная таблица: [ANCHOR_recheck.md](ANCHOR_recheck.md).

| Конфиг | expect | Acc | OK |
|--|--:|--:|--|
| EXP00_baseline_autothr | 4/8 | 4/8 | **OK** |
| EXP00_baseline | 4/8 | 4/8 | **OK** |
| EXP04_preinh_250 | 6/8 | 6/8 | **OK** |
| EXP00_baseline_margprops | 5/8 | 5/8 | **OK** |
| EXP04_preinh_250_margprops | 6/8 | 6/8 | **OK** |
| EXP21_span100ms_preinh250 | 5/8 PASS | 5/8 | **OK** |

**Итог:** якоря не деградировали.

## Setup

- Скрипт: `scripts/setup_time_expand.sh` (не трогает EXP00–27)
- ISI: `α = T/0.48`, `max(1.5 мс, v·α)`; `IterationGap=1.5` не масштабируется
- Timing₀ в Parameters **и** Model; Interface — golden XML

| T | α | SyncTol₀ | Peak₀ | Agree₀ |
|--:|--:|--:|--:|--:|
| 200 мс | 0.417 | 8.33 мс | 11.67 мс | 11.67 мс |
| 300 мс | 0.625 | 12.5 мс | 17.5 мс | 17.5 мс |
| 400 мс | 0.833 | 16.7 мс | 23.3 мс | 23.3 мс |

## Результаты EXP30–35 (Run3, full-tune)

Повтор на существующих конфигах, без новых директорий. Сетка Peak/Agree **доисследована** (`attempts_ran=20`); best остался init (`tune=0`, `best_idx=0`). Acc совпал с первым прогоном (early stop).

| EXP | T | Neuron | Sync | Peak | Agree | L | thr | Acc | fires | mode | gate | attempts |
|--|--:|--|--:|--:|--:|--|--:|--:|--|--|--|--:|
| EXP30 | 200 | baseline | 8.33 мс | 11.67 мс | 11.67 мс | `[22,19,12,1]` | 0.0131 | **3/8** | `10111110` | `partial_FA` | **FAIL** | 20 |
| EXP31 | 200 | Preinh2.5 | 8.33 мс | 11.67 мс | 11.67 мс | `[23,19,13,1]` | 0.0265 | **5/8** | `10110010` | `partial_FA` | **PASS** | 20 |
| EXP32 | 300 | baseline | 12.5 мс | 17.5 мс | 17.5 мс | `[32,27,17,1]` | 0.0131 | **4/8** | `10101110` | `partial_FA` | **PASS** | 20 |
| EXP33 | 300 | Preinh2.5 | 12.5 мс | 17.5 мс | 17.5 мс | `[33,29,17,1]` | 0.0302 | **4/8** | `10101110` | `partial_FA` | **PASS** | 20 |
| EXP34 | 400 | baseline | 16.7 мс | 23.3 мс | 23.3 мс | `[41,36,22,1]` | 0.0133 | **4/8** | `10101110` | `partial_FA` | **PASS** | 20 |
| EXP35 | 400 | Preinh2.5 | 16.7 мс | 23.3 мс | 23.3 мс | `[43,36,22,1]` | 0.0305 | **5/8** | `10101010` | `partial_FA` | **PASS** | 20 |

Все EXP: `phase -> Done`, 8-row CSV. PulseLib не менялся.

### Сравнения

| T | baseline | Preinh | Сравнение |
|--:|--|--|--|
| 200 мс | FAIL Acc3 | **PASS Acc5** | Preinh лучше (валидно) |
| 300 мс | **PASS Acc4** | **PASS Acc4** | ничья |
| 400 мс | **PASS Acc4** | **PASS Acc5** | Preinh чуть лучше |

Vs несжатый EXP00/04: на 300–400 мс baseline достигает floor Acc≥4 (как EXP00). Preinh 200/400 даёт **5/8** и **не достигает 6/8** даже после полной сетки — это не артефакт early stop. Отличие от EXP04 остаётся: другой span/ISI, другие L/thr, масштабированные Peak/Agree (не legacy 20/60/30 мс).  
Vs сжатие EXP20–27: расширение **существенно лучше** (5/6 gate PASS vs почти сплошной FAIL на ≤100 мс).

### Выводы

1. При T→0.48 с селективность восстанавливается; fire-all не наблюдается.
2. Preinh k=2.5 помогает на 200 мс (вытягивает baseline из FAIL) и на 400 мс (+1 Acc).
3. EXP30 baseline остаётся слабым (Acc3) после 20 попыток Peak/Agree.
4. Полная сетка не подняла EXP31/35 с 5/8 до 6/8; разрыв с EXP04 — эффект условий (span + timing), не недотюна.
5. Якоря EXP00/EXP04 подтверждены до старта серии (не переучивались в Run3).

## Артефакты

- Конфиги: `EXP30`…`EXP35`
- На EXP: `RESULT.txt`, `QUALITY.txt`, `tune_log.txt`, `Test/SelectivityLog/results.csv`
- Якоря: `ANCHOR_recheck.md`, `*/QUALITY_anchor.txt`
- Лог: `run_fulltune_rerun.log` (Run3), `run_expand_200_400.log` (первый прогон)
- Скрипты: `setup_time_expand.sh`, `run_time_compress.sh`, `evaluate_selectivity_csv.py`

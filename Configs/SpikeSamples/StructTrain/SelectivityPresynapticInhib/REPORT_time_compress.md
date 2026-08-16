# REPORT: PSI time-compress (span 100/50/25/10 мс)

Сжатие ISI-паттерна × `NSPNeuronGen` (baseline) vs `NSPNeuronGenPreinh2_5` (k=2.5).  
Эталон несжатого: EXP00 **4/8**, EXP04 **6/8**.

## PulseLib

В `NNeuronTimeLearner` вынесены хардкоды в `UProperty` (`ptPubParameter`):

| Свойство | Default | Использование |
|--|--:|--|
| `PeakMeasureMargin` | 0.06 с | `margin = max(PeakMeasureMargin, 0.5·kMaxLengthStep·EstDelayPerSeg)` |
| `DelayAgreeMarginMin` | 0.03 с | `agree_margin = max(SyncTolerance, DelayAgreeMarginMin)` |

Дефолты ctor/`Init` = прежние константы → конфиги без тегов байт-в-байт как раньше.  
Пересборка: `NeuroModelerConsole` (PulseLib.core). ClDesc: `Bin/ClDesc/PulseLibrary/ru-RU/NNeuronTimeLearner.xml`.

**Замечание:** при `EstDelayPerSeg=0.01` вторичный член `0.5·8·0.01 = 0.04 с` часто **перекрывает** уменьшенный `PeakMeasureMargin` на коротких T; на практике решающим рычагом для Done был **SyncTolerance** (дискретный шаг L не укладывался в узкий tol).

## Setup

- Скрипты: `scripts/patch_pattern_scale.py`, `setup_time_compress.sh`, `tune_timing_params.py`, `run_time_compress.sh`
- ISI: `α = T/0.48`, `max(1.5 мс, v·α)`; `IterationGap=1.5` не трогали
- floor onset ISI: **нет** на 100 мс; **да** на 50/25/10 мс
- XML: `SyncTolerance` / `PeakMeasureMargin` / `DelayAgreeMarginMin` в Parameters **и** Model

### Начальные timing (план)

| T | α | SyncTol₀ | Peak₀ | Agree₀ |
|--:|--:|--:|--:|--:|
| 100 мс | 0.208 | 4.17 мс | 5.83 мс | 5.83 мс |
| 50 мс | 0.104 | 2.08 мс | 2.92 мс | 2.92 мс |
| 25 мс | 0.052 | 1.50 мс | 2.00 мс | 2.00 мс |
| 10 мс | 0.021 | 1.50 мс | 2.00 мс | 2.00 мс |

## Результаты сжатых EXP

| EXP | T | Neuron | SyncTol→final | Peak | Agree | L | thr | Acc | tune |
|--|--:|--|--:|--:|--:|--|--:|--:|--:|
| EXP20 | 100 | baseline | 4.17 мс | 5.83 мс | 5.83 мс | `[12,11,7,1]` | 0.0147 | **2/8** | 0 |
| EXP21 | 100 | Preinh2.5 | 4.17 мс | 5.83 мс | 5.83 мс | `[11,9,6,1]` | 0.0321 | **5/8** | 0 |
| EXP22 | 50 | baseline | **8.33 мс** (Δ_min) | 2.92 мс | 8.33 мс | `[7,6,5,1]` | 0.0174 | **1/8** | pre-widen |
| EXP23 | 50 | Preinh2.5 | **8.33 мс** | 2.92 мс | 8.33 мс | `[5,5,4,1]` | 0.0340 | **3/8** | pre-widen |
| EXP24 | 25 | baseline | **2.25 мс** | 1.88 мс | 2.25 мс | `[4,4,3,1]` | 0.0195 | **3/8** | 1 |
| EXP25 | 25 | Preinh2.5 | **3.00 мс** | 1.88 мс | 3.00 мс | `[5,5,4,1]` | 0.0179 | **1/8** | 4 |
| EXP26 | 10 | baseline | **4.50 мс** | 2.00 мс | 4.50 мс | `[3,3,2,1]` | 0.0234 | **1/8** | 6 |
| EXP27 | 10 | Preinh2.5 | **4.50 мс** (с EXP26) | 2.00 мс | 4.50 мс | `[4,4,3,1]` | 0.0116 | **1/8** | 0† |

† Preinh 10 мс: финальные margins скопированы с успешного baseline EXP26 (политика плана).

Все 8 EXP: `phase -> Done`, autothr, `results.csv`. Deep/DissociationTC **не** трогали.

### Per-trial (match)

| EXP | t0..t7 |
|--|--|
| EXP20 | 1 0 0 0 0 0 0 1 |
| EXP21 | 1 0 0 0 1 1 1 1 |
| EXP22 | 1 0 0 0 0 0 0 0 |
| EXP23 | 1 0 0 0 0 0 1 1 |
| EXP24 | 1 0 0 0 0 0 1 1 |
| EXP25 | 1 0 0 0 0 0 0 0 |
| EXP26 | 1 0 0 0 0 0 0 0 |
| EXP27 | 1 0 0 0 0 0 0 0 |

### Сравнение vs несжатый / внутри T

- Сжатие **роняет** accuracy относительно EXP00/04; L пропорционально короче (меньше нужная задержка).
- На **100 и 50 мс** Preinh лучше baseline (5/8 vs 2/8; 3/8 vs 1/8).
- На **25 мс** baseline лучше Preinh (3/8 vs 1/8); на **10 мс** оба **1/8** (селективность почти потеряна: матч в основном на target-trial).
- Auto-tune: на 50 мс SyncTol₀≪ residual `lastAbsDt` (~3–7 мс) → Done только после widen до ~Δ_min / 0.25T; на 10 мс аналогично до 4.5 мс.

## §Regression EXP00 / EXP04 (`*_margprops`)

Отдельные копии (оригиналы не затёрты), явные defaults `PeakMeasureMargin=0.06`, `DelayAgreeMarginMin=0.03`, `SyncTolerance=0.02`. Cold retrain+test.

| Конфиг | L | thr | Acc | Критерий |
|--|--|--:|--:|--|
| EXP00_baseline_margprops | `[49,41,25,1]` | 0.0128 | **5/8** | ≥4/8 — **OK** (чуть выше эталона) |
| EXP04_preinh_250_margprops | `[51,43,25,1]` | 0.0302 | **6/8** | ≥6/8 — **OK** |

Вывод: вынос свойств в UProperty при дефолтах = **no-op** по смыслу регрессии; L/thr в том же порядке, что у EXP00/EXP04.

## Deep / эскалация

- **Не эскалировали** DissociationTC / физику кабеля: Done достигался подбором SyncTol (+ Peak/Agree).
- Остаточный риск на 10/25 мс: ISI ≤ DissociationTC (5 мс) → smear; accuracy 1–3/8.
- `PeakMeasureMargin` на коротких T частично бессилен из‑за пола `0.5·8·EstDelayPerSeg`; если понадобится реальное сужение окон — отдельная правка формулы / `EstDelayPerSeg` (вне scope без запроса).

## Артефакты

- Конфиги: `EXP20`…`EXP27`, `EXP00_baseline_margprops`, `EXP04_preinh_250_margprops`
- Логи: `run_span100_50.log`, `run_span50_resume.log`, `run_span25_10.log`, `run_exp27.log`, `run_margprops.log`
- Скрипты: `scripts/setup_time_compress.sh`, `patch_pattern_scale.py`, `tune_timing_params.py`, `run_time_compress.sh`

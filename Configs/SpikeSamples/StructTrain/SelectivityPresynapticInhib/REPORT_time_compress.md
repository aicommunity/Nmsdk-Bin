# REPORT: PSI time-compress (span 100/50/25/10 мс)

Сжатие ISI-паттерна × `NSPNeuronGen` (baseline) vs `NSPNeuronGenPreinh2_5` (k=2.5).  
Эталон несжатого: EXP00 **4/8**, EXP04 **6/8**.

## Erratum (2026-08-16)

**Acc = sum(match)/8 без режима срабатывания (`neuron_fired`) вводит в заблуждение.**

| Режим | Смысл | Acc может быть | Вердикт |
|--|--|--|--|
| `miss_target` | нет спайка на class=1 (корректный пример) | >0 за счёт «тишины» на distractors | обучение **провалено** |
| `fire_all` | спайк на всех 8 trials | часто **1/8** (матч только на target) | селективности **нет** |
| `selective` / `partial_FA` | target hit, не fire-all | Acc осмысленен | единственные режимы для сравнения |

Явные кейсы Run1:

- **EXP20** (100 мс baseline): в GUI / по `ltz_max` vs thr — **нет срабатывания на корректном примере** (`miss_target`). Формальный Acc 2/8 **не** означает удачное обучение.
- **EXP26** (10 мс baseline): **срабатывание на всех примерах** (`fire_all`). Acc 1/8 — формальный артефакт, не селективность.

Прошлый «tune» (`run_time_compress.sh`) останавливался на **`phase -> Done`**: widen `SyncTolerance` при stall. **PeakMeasureMargin / DelayAgreeMarginMin** для качества теста **не** подбирались; EXP20/21 — `tune=0` (только init). Сравнение «Preinh лучше baseline на 100/50 по Acc» из Run1 **отозвано**.

Полный повтор с quality-gate (target hit ∧ ¬fire_all ∧ Acc≥4/8) и сеткой Sync/Peak/Agree — **следует** (Run2).

## PulseLib

В `NNeuronTimeLearner` вынесены хардкоды в `UProperty` (`ptPubParameter`):

| Свойство | Default | Использование |
|--|--:|--|
| `PeakMeasureMargin` | 0.06 с | `margin = max(PeakMeasureMargin, 0.5·kMaxLengthStep·EstDelayPerSeg)` |
| `DelayAgreeMarginMin` | 0.03 с | `agree_margin = max(SyncTolerance, DelayAgreeMarginMin)` |

Дефолты ctor/`Init` = прежние константы → конфиги без тегов байт-в-байт как раньше.  
Пересборка: `NeuroModelerConsole` (PulseLib.core). ClDesc: `Bin/ClDesc/PulseLibrary/ru-RU/NNeuronTimeLearner.xml`.

**Замечание:** при `EstDelayPerSeg=0.01` вторичный член `0.5·8·0.01 = 0.04 с` часто **перекрывает** уменьшенный `PeakMeasureMargin` на коротких T; на практике решающим рычагом для Done был **SyncTolerance**.

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

## Run1 (Done-only tune) — сырые факты

Числа ниже сохранены как факты первого прогона. **Выводы по сравнению Acc отозваны** (см. Erratum). Mode — качественная оценка по GUI/логам/паттерну срабатывания (CSV после GUI местами урезаны).

| EXP | T | Neuron | SyncTol→final | Peak | Agree | L | thr | Acc | tune | mode (оценка) | вердикт |
|--|--:|--|--:|--:|--:|--|--:|--:|--:|--|--|
| EXP20 | 100 | baseline | 4.17 мс | 5.83 мс | 5.83 мс | `[12,11,7,1]` | 0.0147 | **2/8** | 0 | `miss_target` | unsatisfactory |
| EXP21 | 100 | Preinh2.5 | 4.17 мс | 5.83 мс | 5.83 мс | `[11,9,6,1]` | 0.0321 | **5/8** | 0 | `selective` / `partial_FA` | comparable |
| EXP22 | 50 | baseline | **8.33 мс** | 2.92 мс | 8.33 мс | `[7,6,5,1]` | 0.0174 | **1/8** | pre-widen | `fire_all` | unsatisfactory |
| EXP23 | 50 | Preinh2.5 | **8.33 мс** | 2.92 мс | 8.33 мс | `[5,5,4,1]` | 0.0340 | **3/8** | pre-widen | `partial_FA` | weak |
| EXP24 | 25 | baseline | **2.25 мс** | 1.88 мс | 2.25 мс | `[4,4,3,1]` | 0.0195 | **3/8** | 1 | `partial_FA` | weak |
| EXP25 | 25 | Preinh2.5 | **3.00 мс** | 1.88 мс | 3.00 мс | `[5,5,4,1]` | 0.0179 | **1/8** | 4 | `fire_all` | unsatisfactory |
| EXP26 | 10 | baseline | **4.50 мс** | 2.00 мс | 4.50 мс | `[3,3,2,1]` | 0.0234 | **1/8** | 6 | `fire_all` | unsatisfactory |
| EXP27 | 10 | Preinh2.5 | **4.50 мс** (с EXP26) | 2.00 мс | 4.50 мс | `[4,4,3,1]` | 0.0116 | **1/8** | 0† | `fire_all` | unsatisfactory |

† Preinh 10 мс: margins скопированы с EXP26 (политика Run1; в Run2 каждый EXP ищет независимо).

Все 8 EXP: `phase -> Done`, autothr. Deep/DissociationTC **не** трогали. Tune = widen SyncTol до Done, не quality-gate.

### Per-trial (match only) — Run1

Без колонки `neuron_fired` интерпретация match **ненадёжна** ( Acc 1/8 при fire-all выглядит как «слабый успех»).

| EXP | t0..t7 match |
|--|--|
| EXP20 | 1 0 0 0 0 0 0 1 |
| EXP21 | 1 0 0 0 1 1 1 1 |
| EXP22 | 1 0 0 0 0 0 0 0 |
| EXP23 | 1 0 0 0 0 0 1 1 |
| EXP24 | 1 0 0 0 0 0 1 1 |
| EXP25 | 1 0 0 0 0 0 0 0 |
| EXP26 | 1 0 0 0 0 0 0 0 |
| EXP27 | 1 0 0 0 0 0 0 0 |

### Сравнение Run1 (отозвано как вывод)

- Сырой Acc после сжатия ниже EXP00/04; L короче.
- **Нельзя** утверждать «Preinh лучше baseline на 100/50»: baseline 100 мс — `miss_target`, baseline 50 мс — `fire_all`.
- Acc 1/8 на 10 мс у обоих — **провал селективности** (`fire_all`), не «ничья со слабым Acc».
- Auto-tune Run1: на 50/10 мс SyncTol₀≪ residual `lastAbsDt` → Done только после widen.

## §Regression EXP00 / EXP04 (`*_margprops`)

Отдельные копии (оригиналы не затёрты), явные defaults `PeakMeasureMargin=0.06`, `DelayAgreeMarginMin=0.03`, `SyncTolerance=0.02`. Cold retrain+test.

| Конфиг | L | thr | Acc | Критерий |
|--|--|--:|--:|--|
| EXP00_baseline_margprops | `[49,41,25,1]` | 0.0128 | **5/8** | ≥4/8 — **OK** (чуть выше эталона) |
| EXP04_preinh_250_margprops | `[51,43,25,1]` | 0.0302 | **6/8** | ≥6/8 — **OK** |

Вывод: вынос свойств в UProperty при дефолтах = **no-op** по смыслу регрессии; L/thr в том же порядке, что у EXP00/EXP04.

## Deep / эскалация

- **Не эскалировали** DissociationTC / физику кабеля: Done достигался подбором SyncTol (+ Peak/Agree).
- Остаточный риск на 10/25 мс: ISI ≤ DissociationTC (5 мс) → smear.
- `PeakMeasureMargin` на коротких T частично бессилен из‑за пола `0.5·8·EstDelayPerSeg`; если понадобится реальное сужение окон — отдельная правка формулы / `EstDelayPerSeg` (вне scope без запроса).

## Артефакты

- Конфиги: `EXP20`…`EXP27`, `EXP00_baseline_margprops`, `EXP04_preinh_250_margprops`
- Логи Run1: `run_span100_50.log`, `run_span50_resume.log`, `run_span25_10.log`, `run_exp27.log`, `run_margprops.log`
- Скрипты: `scripts/setup_time_compress.sh`, `patch_pattern_scale.py`, `tune_timing_params.py`, `run_time_compress.sh`

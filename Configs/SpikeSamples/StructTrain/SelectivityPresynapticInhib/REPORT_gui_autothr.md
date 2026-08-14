# PSI GUI-train + autothr — отчёт

Date: 2026-08-14  
Протокол: StructTrain `TimeNeuronTimeLearner` / `TimeNeuronTimeLearnerTest` (8 trials).  
Метрика: `NPatternResponseAnalyzer` → `SelectivityLog/results.csv` (`match` 0/1).

См. также: [REPORT.md](REPORT.md) (старый console без `-S`), [REPORT_autothr.md](REPORT_autothr.md).

## 1. Итог

GUI-train EXP01/EXP02 (сессия NeuroModeler PID 1036112, оба сохранены) **учит длины**. Старый console 1/8 был на **несохранённом / несошедшемся** train (`L=[1,1,1,1]`), а не доказательство «PSI не учится».

| EXP | k | Train | L | Calibrated thr | Test |
|-----|--:|-------|---|---------------:|:----:|
| EXP00_baseline_autothr | — | уже Done | `[49, 41, 25, 1]` | **0.01254** | **4/8** |
| EXP01_preinh_050 | 0.5 | GUI sync + console continue → Done | `[49, 41, 25, 1]` | **0.01978** | **4/8** |
| EXP02_preinh_100 | 1.0 | GUI Done + autothr | `[49, 44, 25, 1]` | **0.03015** | **4/8** |
| EXP03_preinh_200 | 2.0 | console cold `-S` после фикса PulseLib | `[49, 41, 25, 1]` | **0.02996** | **5/8** |

Веса GUI EXP01/EXP02 **не затирались** (`setup_experiments.sh` / `prepare_gui_psi_train.py` на них не гонялись).

## 2. Правки PulseLib

### 2.1. Останов amp-norm (`NoImproveResistanceCount`)

Файл: `Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp` (`ChangeSynapseResistanceStatus`).

Раньше счётчик сбрасывался при любом уменьшении `|dt|`. Микро-осцилляция `1.30e-5 ↔ 1.16e-5` вокруг `kAmpNormEps=1e-5` обнуляла `noImpR` каждый второй шаг → escape `noImpR>=3` никогда не срабатывал.

Теперь:

- `|dt|≤eps` или падение `|dt|` вдвое — сброс;
- **далеко** от цели (`|dt| > kAmpOscillationBand=0.005`) — сброс при любом улучшении (медленный crawl `0.07→0.065` не должен замораживать R);
- **вблизи** цели — инкремент на ничтожных колебаниях (случай EXP01).

`kAmpNormEps` не трогали.

Дополнительно: `ApplyLoadedAnchorProperties()` при continue-load (`ResetToUntrainedState=0`, кабели уже обучены, `Initial==0`) восстанавливает `InitialSomaPotential` из файла — иначе amp-norm видит `initial=[0,0,0,ref]` и не заканчивается.

### 2.2. PSI k=2: мёртвая зона `(1−k·Pre)·Pre`

Файл: `NPulseSynapse.h` / `NPulseSynapse.cpp`, то же в `NPulseSynChannel.cpp`.

Формула `Output = C·(1−k·p)·p` с `C=4k/R` неотрицательна только при `p < 1/k`. При **k=2** это `p<0.5`. Все tip-синапсы сидят на одном `Generator1` (полный 4-спайковый берст). После первого импульса `Pre` остаётся выше 0.5 → импульсы 2–4 дают ток 0.

Симптом (первые итерации без фикса): `peakValid=[1,1,0,0]`, `amp≈[0.036, 6e-4, 4e-7, 2e-10]`, bootstrap «waiting valid ref peak», `L` остаётся `[1,1,1,1]`. У EXP01/02 GUI на `L=1` уже `peakValid=[1,1,1,1]`.

Фикс: `PresynapticInhibitionConductance` — если гейт `(1−k·p)` ушёл в минус, на **активном входе** оставляем остаток `kPsiMinGate=0.05`, в диссоциации — 0 (пол на всём шаге давал DC-утечку и раздувал soma amp). Пик параболы при `p=1/(2k)` не меняется.

После фикса EXP03: `peakValid=[1,1,1,1]` с iter=0, рост `L` как у EXP01/02 (`1→9→17→25→…→[49,41,25,1]`), Done + autothr.

## 3. EXP00 — baseline autothr

Уже Done, `thr=0.01254` (`min + 0.85·(max−min)`). Тест **4/8**, те же FP 2,4,5,6. Порог 0.01254 не отсекает FP с `ltz_max≥0.0117`. Не перегонялся.

## 4. EXP02 — GUI Done + autothr 0.030

GUI: `IsNeedToTrain=0`, `L=[49,44,25,1]`, iter=29  
`CalibrateFixedLTZ min=8.11e-5 max=0.03545 f=0.85 → thr=0.030145`.

Старый test **1/8** при `thr=0.0115` был на несошедшемся/несохранённом train **или** на GUI-весах без калибровки: все 8 trials стреляли (`ltz_max≈0.015`).

После sync Train→Test с калиброванным порогом:

CSV: [`EXP02_preinh_100/Test/SelectivityLog/results.csv`](EXP02_preinh_100/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | t_rel | match |
|------:|------:|--------:|:-----:|------:|:-----:|
| 0 | 1 | 0.03080 | 1 | 0.486 | 1 |
| 1 | 0 | 0.02609 | 0 | −1 | 1 |
| 2 | 0 | 0.03037 | 1 | 0.493 | 0 |
| 3 | 0 | 0.02476 | 0 | −1 | 1 |
| 4 | 0 | 0.03093 | 1 | 0.486 | 0 |
| 5 | 0 | 0.03028 | 1 | 0.490 | 0 |
| 6 | 0 | 0.03067 | 1 | 0.484 | 0 |
| 7 | 0 | 0.02773 | 0 | −1 | 1 |

**Accuracy 4/8.** Target `t_rel≈0.486`. Три TN молчат. Четыре FP всё ещё с `ltz_max≈0.030` (чуть выше калиброванного порога).

## 5. EXP01 — stall ampDt и continue

GUI до паузы (iter≈61): sync успешен (`lastAbsDt≤0.02`, `L=[49,41,25,1]`, `peakValid=[1,1,1,1]`), Done **нет**, autothr не вызывался.

Нормализация падала на dend0/dend1: `|ampDt|≈1.16e-5…1.40e-5` при `eps=1e-5`, знак чередовался, `noImpR` 0↔1. EXP02 проскочил, потому что `|ampDt|` сел ниже 1e-5.

Continue (веса GUI, `ResetToUntrainedState=0`, `StructureBuildMode=0`, `IsNeedToTrain=1`, console `-S`) после фикса noImpR + restore Initial: **Done**, `thr=0.019783`.

CSV: [`EXP01_preinh_050/Test/SelectivityLog/results.csv`](EXP01_preinh_050/Test/SelectivityLog/results.csv) — **4/8**, тот же паттерн FP 2,4,5,6, `ltz_max≈0.020`.

## 6. EXP03 — k=2, рост длин, Done, test 5/8

Первый console cold-train без фикса PSI: `peakValid=[1,1,0,0]`, ref без пика, `L` не росли. Не закрывали как «не сошлось».

После `PresynapticInhibitionConductance` + уточнения noImpR (не замораживать R на большом `|ampDt|`):

- iter=0: `peakValid=[1,1,1,1]`, `amp≈0.036` на всех сомах;
- iter=26: `L=[49,41,25,1]`, `lastAbsDt=[0.0195,0.0195,0.0165]`;
- `CalibrateFixedLTZ min=2.26e-5 max=0.03525 f=0.85 → thr=0.02996`;
- XML: `IsNeedToTrain=0`, `UseFixedLTZThreshold=1`.

CSV: [`EXP03_preinh_200/Test/SelectivityLog/results.csv`](EXP03_preinh_200/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | t_rel | match |
|------:|------:|--------:|:-----:|------:|:-----:|
| 0 | 1 | 0.03076 | 1 | 0.491 | 1 |
| 1 | 0 | 0.02439 | 0 | −1 | 1 |
| 2 | 0 | 0.03010 | 1 | 0.497 | 0 |
| 3 | 0 | 0.02482 | 0 | −1 | 1 |
| 4 | 0 | 0.03032 | 1 | 0.493 | 0 |
| 5 | 0 | 0.02837 | 0 | −1 | **1** |
| 6 | 0 | 0.03077 | 1 | 0.490 | 0 |
| 7 | 0 | 0.02620 | 0 | −1 | 1 |

**Accuracy 5/8.** Trial 5 (ISI `0.24/0.22/0.02`) стал TN: `ltz_max=0.0284 < 0.030`. FP 2,4,6 остаются на грани порога.

## 7. Выводы

1. PSI k=0.5 и k=1 **обучается** (длины как baseline), если train доводят до Done и **сохраняют** XML (`-S` / GUI Save).
2. Console 1/8 в [REPORT.md](REPORT.md) — артефакт `L=[1,1,1,1]` без save, не свойств PSI.
3. Autothr поднимает порог (0.0125 / 0.020 / 0.030) и переводит EXP02 с 1/8 на 4/8; FP с `ltz_max` чуть выше калибровки остаются.
4. k=2 требовал фикса формулы: мёртвая зона `p≥0.5` глушила поздние спайки общего берста. После фикса — рост L, Done, test **5/8**.

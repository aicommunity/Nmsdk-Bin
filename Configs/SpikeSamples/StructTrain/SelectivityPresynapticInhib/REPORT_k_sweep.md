# PSI k-sweep — отчёт

Date: 2026-08-14 (волна 1 EXP04–06); extend 2026-08-15 (EXP07–15 + регрессия EXP04).  
База сравнения: EXP03 k=2 → **5/8** ([REPORT_gui_autothr.md](REPORT_gui_autothr.md)).  
Протокол: cold train `NeuroModelerConsole -t 90 -x -S`, sync Train→Test, test `-t 20 -x`.  
Метрика: `SelectivityLog/results.csv` (`match` 0/1).  
EXP00–06 **не затирались** при setup EXP07–15.

## 1. Итог

| EXP | k | Сходимость | L | Calibrated thr | Test | vs EXP03 5/8 | vs EXP04 6/8 |
|-----|--:|:----------:|---|---------------:|:----:|:------------:|:------------:|
| EXP00_baseline_autothr | — | Done (ранее) | `[49, 41, 25, 1]` | 0.01254 | 4/8 | хуже | хуже |
| EXP01_preinh_050 | 0.5 | Done (ранее) | `[49, 41, 25, 1]` | 0.01978 | 4/8 | хуже | хуже |
| EXP02_preinh_100 | 1.0 | Done (ранее) | `[49, 44, 25, 1]` | 0.03015 | 4/8 | хуже | хуже |
| EXP03_preinh_200 | 2.0 | Done (ранее) | `[49, 41, 25, 1]` | 0.02996 | **5/8** | база | хуже |
| **EXP04_preinh_250** | **2.5** | Done | `[51, 43, 25, 1]` | **0.03017** | **6/8** | **лучше** | лучший |
| EXP05_preinh_300 | 3.0 | Done | `[51, 43, 25, 1]` | 0.02968 | 5/8 | ничья | хуже |
| EXP06_preinh_400 | 4.0 | Done | `[51, 43, 25, 1]` | 0.02964 | 5/8 | ничья | хуже |
| EXP07_preinh_500 | 5.0 | Done | `[51, 43, 25, 1]` | 0.02960 | 5/8 | ничья | хуже |
| EXP08_preinh_600 | 6.0 | Done | `[51, 43, 25, 1]` | 0.03002 | 5/8 | ничья | хуже |
| EXP09_preinh_1000 | 10.0 | Done | `[52, 44, 25, 1]` | 0.02986 | 5/8 | ничья | хуже |
| EXP10_preinh_180 | 1.8 | Done | `[49, 41, 25, 1]` | 0.03027 | 5/8 | ничья | хуже |
| **EXP11_preinh_210** | **2.1** | Done | `[51, 43, 25, 1]` | **0.03032** | **6/8** | **лучше** | ничья |
| **EXP12_preinh_220** | **2.2** | Done | `[51, 43, 25, 1]` | **0.03031** | **6/8** | **лучше** | ничья |
| EXP13_preinh_240 | 2.4 | Done | `[51, 43, 25, 1]` | 0.02971 | 5/8 | ничья | хуже |
| **EXP14_preinh_260** | **2.6** | Done | `[51, 43, 25, 1]` | **0.03019** | **6/8** | **лучше** | ничья |
| EXP15_preinh_270 | 2.7 | Done | `[51, 43, 25, 1]` | 0.02994 | 5/8 | ничья | хуже |

**Эффект:** плато **6/8** на k∈{2.1, 2.2, 2.5, 2.6}; новый лучший (≥7/8) не найден. Вне плато (≤1.8, =2.0/2.4/2.7, ≥3) — **5/8** (ничья с EXP03).  
Критерии сходимости: `phase -> Done`, `IsNeedToTrain=0`, выросшие L, `UseFixedLTZThreshold=1`, ненулевой `FixedLTZThreshold`.

## 2. Правки PulseLib (до / во время sweep)

### 2.1. Прототипы Storage

В `NPulseLibrary.cpp` зарегистрированы:

`0.5, 1.0, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 10.0, 1.8, 2.1, 2.2`  
и при extend: **`2.4, 2.6, 2.7`** → `…Preinh2_4` / `2_6` / `2_7`.

Имена 0.5…2.5 и существующие Preinh* не менялись. Поведение learner / остатка / `OutputConstData` при extend **не** менялось — только новые классы.

### 2.2. Остаток гейта при k>2

`PresynapticInhibitionConductance` (`NPulseSynapse.h`): при `k>2`  
`min_gate = 0.05 * (2/k)`, чтобы абсолютный остаток в мёртвой зоне оставался ~0.4/R как у калибровки k=2. При k=2 поведение не меняется. Для 2.4–2.7 и 5/6/10 гейт уже покрывает — не трогали.

### 2.3. `OutputConstData` после Copy

`OutputConstData` не UProperty: после `TakeObject`/`Copy` прототипа часто `C=0` → `amp=0`, `peakValid=[0,0,0,0]`.  
Фикс: пересчёт `C=4k/R` в `ABuild` и в `ACalculate2` при включённом PSI.

### 2.4. Конфиги

Скрипт [`scripts/setup_k_sweep.sh`](scripts/setup_k_sweep.sh) создаёт только новые EXP (не трогает EXP00–06).  
`setup_experiments.sh` **не** вызывался.  
Перед cold-train: `prepare_gui_psi_train.py` + patch `NeuronClassName` в **Parameters и Model** (грязный `TimeNeuronTimeLearner` / `MaxCalculationModelTime=0` иначе даёт ложный «не сошлось» / `amp=0`).

## 3. Регрессия EXP04 после регистрации Preinh2_4/2_6/2_7

Cold retrain+test в копии [`EXP04_preinh_250_recheck/`](EXP04_preinh_250_recheck/) (`NSPNeuronGenPreinh2_5`), оригинал EXP04 не затирался.

| | L | thr | Test |
|--|---|----:|:----:|
| EXP04 оригинал | `[51, 43, 25, 1]` | 0.03017 | **6/8** |
| EXP04 recheck | `[51, 43, 25, 1]` | 0.03017 | **6/8** |

Критерий ≥6/8 выполнен; per-trial совпадает с оригиналом (TN на trial 2; FP 4,6). Поведенческий фикс learner/гейта не вносился — регрессия по факту регистрации новых прототипов.

## 4. Per-trial (сошедшие EXP)

### EXP04 k=2.5 — 6/8

CSV: [`EXP04_preinh_250/Test/SelectivityLog/results.csv`](EXP04_preinh_250/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | t_rel | match |
|------:|------:|--------:|:-----:|------:|:-----:|
| 0 | 1 | 0.03095 | 1 | 0.492 | 1 |
| 1 | 0 | 0.02558 | 0 | −1 | 1 |
| 2 | 0 | 0.03014 | 0 | −1 | **1** |
| 3 | 0 | 0.02474 | 0 | −1 | 1 |
| 4 | 0 | 0.03079 | 1 | 0.492 | 0 |
| 5 | 0 | 0.02946 | 0 | −1 | 1 |
| 6 | 0 | 0.03106 | 1 | 0.491 | 0 |
| 7 | 0 | 0.02605 | 0 | −1 | 1 |

Выигрыш относительно EXP03: trial 2 стал TN. FP 4 и 6 остаются чуть выше порога.

### EXP05 k=3.0 — 5/8

CSV: [`EXP05_preinh_300/Test/SelectivityLog/results.csv`](EXP05_preinh_300/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | t_rel | match |
|------:|------:|--------:|:-----:|------:|:-----:|
| 0 | 1 | 0.03042 | 1 | 0.492 | 1 |
| 1 | 0 | 0.02535 | 0 | −1 | 1 |
| 2 | 0 | 0.02980 | 1 | 0.499 | 0 |
| 3 | 0 | 0.02458 | 0 | −1 | 1 |
| 4 | 0 | 0.03017 | 1 | 0.492 | 0 |
| 5 | 0 | 0.02914 | 0 | −1 | 1 |
| 6 | 0 | 0.03055 | 1 | 0.491 | 0 |
| 7 | 0 | 0.02584 | 0 | −1 | 1 |

Паттерн как у EXP03: TN 1,3,5,7; FP 2,4,6.

### EXP06 k=4.0 — 5/8

CSV: [`EXP06_preinh_400/Test/SelectivityLog/results.csv`](EXP06_preinh_400/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | t_rel | match |
|------:|------:|--------:|:-----:|------:|:-----:|
| 0 | 1 | 0.03014 | 1 | 0.493 | 1 |
| 1 | 0 | 0.02536 | 0 | −1 | 1 |
| 2 | 0 | 0.02976 | 1 | 0.500 | 0 |
| 3 | 0 | 0.02458 | 0 | −1 | 1 |
| 4 | 0 | 0.03014 | 1 | 0.494 | 0 |
| 5 | 0 | 0.02898 | 0 | −1 | 1 |
| 6 | 0 | 0.03018 | 1 | 0.492 | 0 |
| 7 | 0 | 0.02581 | 0 | −1 | 1 |

### EXP07 k=5.0 — 5/8

CSV: [`EXP07_preinh_500/Test/SelectivityLog/results.csv`](EXP07_preinh_500/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | match |
|------:|------:|--------:|:-----:|:-----:|
| 0 | 1 | 0.03010 | 1 | 1 |
| 1 | 0 | 0.02536 | 0 | 1 |
| 2 | 0 | 0.02976 | 1 | 0 |
| 3 | 0 | 0.02458 | 0 | 1 |
| 4 | 0 | 0.03031 | 1 | 0 |
| 5 | 0 | 0.02882 | 0 | 1 |
| 6 | 0 | 0.03010 | 1 | 0 |
| 7 | 0 | 0.02578 | 0 | 1 |

### EXP08 k=6.0 — 5/8

CSV: [`EXP08_preinh_600/Test/SelectivityLog/results.csv`](EXP08_preinh_600/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | match |
|------:|------:|--------:|:-----:|:-----:|
| 0 | 1 | 0.03046 | 1 | 1 |
| 1 | 0 | 0.02559 | 0 | 1 |
| 2 | 0 | 0.03010 | 1 | 0 |
| 3 | 0 | 0.02474 | 0 | 1 |
| 4 | 0 | 0.03056 | 1 | 0 |
| 5 | 0 | 0.02890 | 0 | 1 |
| 6 | 0 | 0.03081 | 1 | 0 |
| 7 | 0 | 0.02594 | 0 | 1 |

### EXP09 k=10.0 — 5/8

CSV: [`EXP09_preinh_1000/Test/SelectivityLog/results.csv`](EXP09_preinh_1000/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | match |
|------:|------:|--------:|:-----:|:-----:|
| 0 | 1 | 0.03066 | 1 | 1 |
| 1 | 0 | 0.02597 | 0 | 1 |
| 2 | 0 | 0.02995 | 1 | 0 |
| 3 | 0 | 0.02463 | 0 | 1 |
| 4 | 0 | 0.03046 | 1 | 0 |
| 5 | 0 | 0.02875 | 0 | 1 |
| 6 | 0 | 0.03040 | 1 | 0 |
| 7 | 0 | 0.02580 | 0 | 1 |

### EXP10 k=1.8 — 5/8

CSV: [`EXP10_preinh_180/Test/SelectivityLog/results.csv`](EXP10_preinh_180/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | match |
|------:|------:|--------:|:-----:|:-----:|
| 0 | 1 | 0.03074 | 1 | 1 |
| 1 | 0 | 0.02465 | 0 | 1 |
| 2 | 0 | 0.03041 | 1 | 0 |
| 3 | 0 | 0.02501 | 0 | 1 |
| 4 | 0 | 0.03076 | 1 | 0 |
| 5 | 0 | 0.02870 | 0 | 1 |
| 6 | 0 | 0.03076 | 1 | 0 |
| 7 | 0 | 0.02643 | 0 | 1 |

### EXP11 k=2.1 — 6/8

CSV: [`EXP11_preinh_210/Test/SelectivityLog/results.csv`](EXP11_preinh_210/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | match |
|------:|------:|--------:|:-----:|:-----:|
| 0 | 1 | 0.03097 | 1 | 1 |
| 1 | 0 | 0.02554 | 0 | 1 |
| 2 | 0 | 0.03002 | 0 | **1** |
| 3 | 0 | 0.02460 | 0 | 1 |
| 4 | 0 | 0.03093 | 1 | 0 |
| 5 | 0 | 0.02950 | 0 | 1 |
| 6 | 0 | 0.03094 | 1 | 0 |
| 7 | 0 | 0.02564 | 0 | 1 |

Trial 2 TN (как у k=2.5); FP 4,6.

### EXP12 k=2.2 — 6/8

CSV: [`EXP12_preinh_220/Test/SelectivityLog/results.csv`](EXP12_preinh_220/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | match |
|------:|------:|--------:|:-----:|:-----:|
| 0 | 1 | 0.03080 | 1 | 1 |
| 1 | 0 | 0.02554 | 0 | 1 |
| 2 | 0 | 0.03002 | 0 | **1** |
| 3 | 0 | 0.02461 | 0 | 1 |
| 4 | 0 | 0.03076 | 1 | 0 |
| 5 | 0 | 0.02948 | 0 | 1 |
| 6 | 0 | 0.03117 | 1 | 0 |
| 7 | 0 | 0.02563 | 0 | 1 |

### EXP13 k=2.4 — 5/8

CSV: [`EXP13_preinh_240/Test/SelectivityLog/results.csv`](EXP13_preinh_240/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | match |
|------:|------:|--------:|:-----:|:-----:|
| 0 | 1 | 0.03051 | 1 | 1 |
| 1 | 0 | 0.02539 | 0 | 1 |
| 2 | 0 | 0.02986 | 1 | 0 |
| 3 | 0 | 0.02461 | 0 | 1 |
| 4 | 0 | 0.03034 | 1 | 0 |
| 5 | 0 | 0.02930 | 0 | 1 |
| 6 | 0 | 0.03019 | 1 | 0 |
| 7 | 0 | 0.02588 | 0 | 1 |

Thr ниже (0.02971) → trial 2 снова FP.

### EXP14 k=2.6 — 6/8

CSV: [`EXP14_preinh_260/Test/SelectivityLog/results.csv`](EXP14_preinh_260/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | match |
|------:|------:|--------:|:-----:|:-----:|
| 0 | 1 | 0.03086 | 1 | 1 |
| 1 | 0 | 0.02562 | 0 | 1 |
| 2 | 0 | 0.03019 | 0 | **1** |
| 3 | 0 | 0.02478 | 0 | 1 |
| 4 | 0 | 0.03070 | 1 | 0 |
| 5 | 0 | 0.02949 | 0 | 1 |
| 6 | 0 | 0.03094 | 1 | 0 |
| 7 | 0 | 0.02608 | 0 | 1 |

Ничья с лучшим (k=2.5).

### EXP15 k=2.7 — 5/8

CSV: [`EXP15_preinh_270/Test/SelectivityLog/results.csv`](EXP15_preinh_270/Test/SelectivityLog/results.csv)

| trial | class | ltz_max | fired | match |
|------:|------:|--------:|:-----:|:-----:|
| 0 | 1 | 0.03076 | 1 | 1 |
| 1 | 0 | 0.02563 | 0 | 1 |
| 2 | 0 | 0.03006 | 1 | 0 |
| 3 | 0 | 0.02480 | 0 | 1 |
| 4 | 0 | 0.03059 | 1 | 0 |
| 5 | 0 | 0.02949 | 0 | 1 |
| 6 | 0 | 0.03083 | 1 | 0 |
| 7 | 0 | 0.02613 | 0 | 1 |

### EXP04 recheck k=2.5 — 6/8

CSV: [`EXP04_preinh_250_recheck/Test/SelectivityLog/results.csv`](EXP04_preinh_250_recheck/Test/SelectivityLog/results.csv)

Идентично оригиналу EXP04 (см. §3).

## 5. Выводы

1. Плато **6/8** на k≈**2.1–2.6** (точки 2.1, 2.2, 2.5, 2.6); **k=2.4 и 2.7** дают 5/8 из‑за сдвига thr относительно ltz trial 2.
2. Высокие k (5/6/10) и k=1.8 сходятся, но accuracy **5/8** — ничья с EXP03, не лучше текущего пика.
3. Новый лучший (≥7/8) не найден; FP на trials 4 и 6 остаются на всех 6/8-точках.
4. Регрессия k=2.5 после добавления Preinh2_4/2_6/2_7: **6/8**, L/thr совпали с оригиналом.
5. Для воспроизводимости cold-train: `prepare_gui_psi_train.py`, patch NeuronClass в Parameters **и** Model, `-S` после Done.

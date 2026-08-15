# PSI k-sweep — отчёт

Date: 2026-08-14  
База сравнения: EXP03 k=2 → **5/8** ([REPORT_gui_autothr.md](REPORT_gui_autothr.md)).  
Протокол: cold train `NeuroModelerConsole -t 90 -x -S`, sync Train→Test, test `-t 20 -x`.  
Метрика: `SelectivityLog/results.csv` (`match` 0/1).  
EXP00–03 **не переобучались** (только строки сравнения).

## 1. Итог

| EXP | k | Сходимость | L | Calibrated thr | Test | vs EXP03 5/8 |
|-----|--:|:----------:|---|---------------:|:----:|:------------:|
| EXP00_baseline_autothr | — | Done (ранее) | `[49, 41, 25, 1]` | 0.01254 | 4/8 | хуже |
| EXP01_preinh_050 | 0.5 | Done (ранее) | `[49, 41, 25, 1]` | 0.01978 | 4/8 | хуже |
| EXP02_preinh_100 | 1.0 | Done (ранее) | `[49, 44, 25, 1]` | 0.03015 | 4/8 | хуже |
| EXP03_preinh_200 | 2.0 | Done (ранее) | `[49, 41, 25, 1]` | 0.02996 | **5/8** | база |
| **EXP04_preinh_250** | **2.5** | Done | `[51, 43, 25, 1]` | **0.03017** | **6/8** | **лучше** |
| EXP05_preinh_300 | 3.0 | Done | `[51, 43, 25, 1]` | 0.02968 | 5/8 | ничья |
| EXP06_preinh_400 | 4.0 | Done | `[51, 43, 25, 1]` | 0.02964 | 5/8 | ничья |

**Эффект найден:** k=2.5 даёт строго лучше 5/8. Волны 2 (k=5/6/10) и 3 (k=1.8/2.1/2.2) **не запускались**.

Критерии сходимости выполнены для EXP04–06: `phase -> Done`, `IsNeedToTrain=0`, выросшие L, `UseFixedLTZThreshold=1`, ненулевой `FixedLTZThreshold`.

## 2. Правки PulseLib (до / во время sweep)

### 2.1. Прототипы Storage

В `NPulseLibrary.cpp` зарегистрированы все запасные k одной сборкой:

`0.5, 1.0, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 10.0, 1.8, 2.1, 2.2`  
→ `NPSynapseBioPreinh*` / `NPMembraneBioPreinh*` / `NSPNeuronGenPreinh*`.

Имена 0.5 / 1.0 / 2.0 не менялись.

### 2.2. Остаток гейта при k>2

`PresynapticInhibitionConductance` (`NPulseSynapse.h`): при `k>2`  
`min_gate = 0.05 * (2/k)`, чтобы абсолютный остаток в мёртвой зоне оставался ~0.4/R как у калибровки k=2. При k=2 поведение не меняется.

### 2.3. `OutputConstData` после Copy

`OutputConstData` не UProperty: после `TakeObject`/`Copy` прототипа часто `C=0` → `amp=0`, `peakValid=[0,0,0,0]`.  
Фикс: пересчёт `C=4k/R` в `ABuild` и в `ACalculate2` при включённом PSI.

### 2.4. Конфиги

Скрипт [`scripts/setup_k_sweep.sh`](scripts/setup_k_sweep.sh) создаёт только новые EXP (не трогает EXP00–03).  
`setup_experiments.sh` **не** вызывался.  
Перед cold-train: `prepare_gui_psi_train.py` + `patch_neuron_class.py` (грязный `TimeNeuronTimeLearner` / `MaxCalculationModelTime=0` иначе даёт ложный «не сошлось»).

Первый прогон EXP05 без повторного prepare дал `amp=[0,0,0,0]` при `BuildStructure` сначала с `Preinh2_5`, затем `Preinh3_0`. После cold-prepare k=3/4 сошлись штатно.

## 3. Per-trial (сошедшие EXP04–06)

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

Выигрыш относительно EXP03: trial 2 стал TN (`ltz_max=0.03014 < thr=0.03017`; у k=2 это был FP). FP 4 и 6 остаются чуть выше порога.

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

Паттерн как у EXP03: TN 1,3,5,7; FP 2,4,6. Trial 5 снова TN (`ltz_max < thr`).

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

Снова 5/8, те же FP 2,4,6.

## 4. Выводы

1. Усиление PSI до **k=2.5** улучшает тест до **6/8** (один дополнительный TN на trial 2) при той же схеме autothr.
2. Дальнейшее усиление **k=3 и k=4** сходится (L≈`[51,43,25,1]`, thr≈0.0297), но accuracy возвращается к **5/8** — ничья с k=2, не хуже baseline 4/8.
3. Волны 2/3 не нужны: критерий эффекта (≥6/8) выполнен на волне 1.
4. Для воспроизводимости cold-train новых Preinh-классов обязательны `prepare_gui_psi_train.py`, `-S` после Done и пересчёт `OutputConstData` в синапсе.

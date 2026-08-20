# Branch: tip amp-eq + EnableNextSegmentInhibition — сводный отчёт

Date: 2026-08-20  
Компонент: `NNeuronTimeLearnerBranch` (один дендрит, N импульсов на разных сегментах).  
Протокол: cold train `NeuroModelerConsole -t 160 -x -S` → sync Train→Test → test `-t 20 -x`.  
Метрика: `NPatternResponseAnalyzer` → `SelectivityLog/results.csv` (`match` 0/1 + `error_class` / `late_fired`), 8 trials (1 target + 7 negative).
`PostPatternWindow=0.5`, `LateResponseWindow=1.5` (поздние LTZone-спайки вне окна match → `late_fp` / `late_fn`).

Код: [`Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearnerBranch.cpp`](../../../../../Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearnerBranch.cpp)  
Алгоритм: [`ALGORITHM.md`](ALGORITHM.md)

PulseLib: `df1bdfa` — tip amp-eq + `EnableNextSegmentInhibition`.  
Bin: `26c1770` — retrain + конфиги NextSegInh.

---

## 1. Контекст и мотивация

После встроенных этапов Done (**R×N** + **CalibrateLtz**, peak×0.99) baseline BranchTest давал **6/8** (fn=0, fp=2). Наблюдения:

1. **Перекос tip-амплитуд.** Mute не amp-tune якорь `N−1` (`ChangeSynapseResistanceStatus` early-return). Равномерный `R×N` сохраняет относительный перекос; проксимальный Exc на `Dendrite1_1` доминирует на recognition.
2. **Сегментное торможение.** Ручной пост-hoc XML (`TimeNeuronTimeLearnerBranchTest_NextSegInh`, `StructureBuildMode=0`): тот же Generator → Exc@L + Inh@L+1 → **7/8**, но **fn=1** (target soma≈0.035 &lt; FixedLTZ≈0.066). Нужен learner-режим с обучением «с Inh».

---

## 2. Что сделано в коде

### 2.1 Amp-eq перед parallel recognition

`ScaleTipResistancesForParallelActivation`:

```
I_ref = mean(InitialSomaPotential[0..N-2] where Initial > 0)
R[i]  = Clamp(R[i] * N * (Initial[i] / I_ref))   // Initial≤0 → только ×N
```

Mute-solo вклады выравниваются к distal target, затем ×N → ~1/N проводимости на tip при all-on.

### 2.2 `EnableNextSegmentInhibition` (default `false`)

| | поведение |
|--|--|
| cable | `ChainLengthMax = max(L[0..N-2]) + 1` |
| проводка | Exc@`L[k]` + Inh@`L[k]+1`, `Type=1`, `R=SynapseResistanceBase` |
| mute | Exc+Inh активного tip → **2** links |
| Done / CalibrateLtz | все пары → **2N** links |
| Inh R | без отдельного тюна в первом прогоне |

ClDesc: [`NNeuronTimeLearnerBranch.xml`](../../../../ClDesc/PulseLibrary/ru-RU/NNeuronTimeLearnerBranch.xml).

---

## 3. Карта конфигов

| Роль | Путь | Флаг Inh | Accuracy |
|------|------|:--------:|:--------:|
| Train baseline | [`TimeNeuronTimeLearnerBranch`](./) | 0 | — (train) |
| Test baseline | [`TimeNeuronTimeLearnerBranchTest`](../TimeNeuronTimeLearnerBranchTest/) | 0 | **6/8** |
| Train NextSegInh | [`TimeNeuronTimeLearnerBranch_NextSegInh`](../TimeNeuronTimeLearnerBranch_NextSegInh/) | 1 | — (train) |
| Test NextSegInh | [`TimeNeuronTimeLearnerBranchTest_NextSegInh`](../TimeNeuronTimeLearnerBranchTest_NextSegInh/) | 1 | **7/8** |
| Static Inh (ручной XML, до learner-флага) | тот же Test_NextSegInh (старый прогон) | XML-hack | **7/8** (fn=1) |

---

## 4. Состояние после обучения

### 4.1 Baseline (amp-eq, без Inh)

| Параметр | Значение |
|----------|----------|
| `DendriteLength` | `[85, 46, 25, 1]` |
| `InitialSomaPotential` | ≈`[0.0158, 0.0158, 0.0158, 0.0196]` |
| `TipSynapseResistance` | ≈`[4.00e6, 1.03e8, 8.82e7, 4.28e8]` |
| Scale tip3 (якорь) | `N×(I/I_ref) ≈ 4.97` (I_ref≈0.0158; якорь лишь слегка выше distal) |
| `FixedLTZThreshold` | **0.0728** (peak≈0.0735 × 0.99) |
| gen_links Done | 4 (Exc only) |

В этом cold-прогоне Initial якоря ≈0.02 (не ~0.15, как в более старом Done-state), поэтому amp-eq почти совпадает с чистым ×N для tip0..2 и даёт умеренный boost tip3.

### 4.2 NextSegInh (обучен с флагом)

| Параметр | Значение |
|----------|----------|
| `DendriteLength` | `[89, 46, 25, 1]` |
| Inh сегменты | `{90, 47, 26, 2}` |
| `InitialSomaPotential` | ≈`[0.0083, 0.0081, 0.0083, 0.0940]` |
| `TipSynapseResistance` | ≈`[4.04e6, 1.27e8, 1.15e8, 3.92e9]` |
| Scale tip3 | ≈**45.5** (I_ref≈0.0083; якорь ~11× сильнее distal → сильный amp-eq) |
| `FixedLTZThreshold` | **0.0650** (peak≈0.0656 × 0.99) |
| gen_links Calibrate/Done | **8** (4 Exc + 4 Inh) |

С Inh mute-амплитуды distal ниже → I_ref падает, amp-eq якоря становится существенным (R tip3 ~ Base×45).

---

## 5. Результаты теста (8 trials)

### 5.1 Сводка

| Эксперимент | acc | fn | fp | late_fp | late_fn | FixedLTZ | L |
|-------------|:---:|:--:|:--:|:-------:|:------:|---------:|---|
| Pre-amp-eq (R×N only, ранее) | **6/8** | 0 | 2 (4,6) | — | — | ≈0.066 | `[69,42,25,1]` |
| **Baseline amp-eq** | **6/8** | 0 | 2 (**2**,6) | **2** (1,7) | 0 | 0.0728 | `[85,46,25,1]` |
| Static NextSegInh (XML, без retrain) | **7/8** | **1** | 0 | — | — | ≈0.066 | `[69,42,25,1]`+Inh |
| **Trained NextSegInh** | **7/8** | **0** | 1 (6) | **4** (1,2,5,7) | 0 | 0.0650 | `[89,46,25,1]`+Inh |

### 5.2 Baseline amp-eq — trials

CSV: [`TimeNeuronTimeLearnerBranchTest/SelectivityLog/results.csv`](../TimeNeuronTimeLearnerBranchTest/SelectivityLog/results.csv)

| trial | class | fired | late | late_t_rel | soma_amp_sum | match | error_class |
|------:|------:|------:|-----:|-----------:|-------------:|------:|:-----------:|
| 0 | 1 | 1 | 0 | — | 0.0728 | **1** | ok |
| 1 | 0 | 0 | 1 | 1.21 | 0.0728 | **1** | **late_fp** |
| 2 | 0 | 1 | 0 | — | 0.0729 | 0 | **fp** |
| 3 | 0 | 0 | 0 | — | 0.0559 | **1** | ok |
| 4 | 0 | 0 | 0 | — | 0.0719 | **1** | ok |
| 5 | 0 | 0 | 0 | — | 0.0721 | **1** | ok |
| 6 | 0 | 1 | 0 | — | 0.0751 | 0 | **fp** |
| 7 | 0 | 0 | 1 | 1.17 | 0.0728 | **1** | **late_fp** |

In-window FP: trials **2** и **6**. Дополнительно **2× late_fp** (1, 7).

### 5.3 Trained NextSegInh — trials

CSV: [`TimeNeuronTimeLearnerBranchTest_NextSegInh/SelectivityLog/results.csv`](../TimeNeuronTimeLearnerBranchTest_NextSegInh/SelectivityLog/results.csv)

| trial | class | fired | late | late_t_rel | soma_amp_sum | match | error_class |
|------:|------:|------:|-----:|-----------:|-------------:|------:|:-----------:|
| 0 | 1 | 1 | 0 | — | 0.0650 | **1** | ok |
| 1 | 0 | 0 | 1 | 1.23 | 0.0650 | **1** | **late_fp** |
| 2 | 0 | 0 | 1 | 0.99 | 0.0650 | **1** | **late_fp** |
| 3 | 0 | 0 | 0 | — | 0.0507 | **1** | ok |
| 4 | 0 | 0 | 0 | — | 0.0637 | **1** | ok |
| 5 | 0 | 0 | 1 | 1.29 | 0.0650 | **1** | **late_fp** |
| 6 | 0 | 1 | 0 | — | 0.0676 | 0 | **fp** |
| 7 | 0 | 0 | 1 | 1.20 | 0.0650 | **1** | **late_fp** |

In-window: **7/8** (fn=0, fp=1 на trial 6).  
Дополнительно: **4× late_fp** (trials 1, 2, 5, 7) — спайк после `PostPatternWindow`, раньше не попадал в `match`/`fired`, но виден в GUI. `late_t_rel` от первого стимула паттерна (~0.5 с после последнего → порог ~0.98 с).

### 5.4 Static Inh (исторический, для сравнения)

Ручная проводка на весах baseline R×N без amp-eq / без retrain с Inh:

| | результат |
|--|--|
| acc | 7/8 |
| fn | 1 (trial 0: soma≈0.035 &lt; FixedLTZ≈0.066) |
| fp | 0 |

Обучение **с** Inh убирает FN за счёт автокалибровки FixedLTZ по parallel peak уже с торможением.

---

## 6. Выводы

1. **Amp-eq** корректен по формуле и обязателен при перекосе `Initial` (особенно с Inh, где I_ref падает). Сам по себе на baseline cold-прогоне **не улучшил** accuracy (осталось 6/8); сдвинулся набор FP (4→2).
2. **`EnableNextSegmentInhibition`** в learner воспроизводит ручную схему Exc@L + Inh@L+1, даёт **2N** links после Done и **7/8** без FN по in-window `match`.
3. Лучший текущий Branch-результат по `match`: **trained NextSegInh = 7/8** (лучше baseline 6/8; vs static Inh — тот же acc, но без fn).
4. Анализатор теперь отдельно помечает **late_fp / late_fn** (`LateResponseWindow=1.5`). На NextSegInh при «чистых» 7/8 match есть **4 late_fp** — те самые запоздалые спайки, которые раньше пропускались CSV, но видны в GUI (settle ≈0.01×L ≈0.9 с > Post=0.5 с).
5. Оставшийся in-window FP (trial 6) и late_fp на nontarget — кандидаты на ослабление Inh / контраст / второй порог — вне текущего scope.

---

## 7. Как воспроизвести

```bash
# PulseLib + console
cmake --build build/linux-gcc-debug-local \
  --target Nmsdk-PulseLib.core NeuroModelerConsole -j$(nproc)

# Baseline test (уже обученный)
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranchTest/Project.ini \
  -s -t 20 -x

# NextSegInh test
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranchTest_NextSegInh/Project.ini \
  -s -t 20 -x

# Cold retrain NextSegInh (при необходимости)
# Parameters: EnableNextSegmentInhibition=1, IsNeedToTrain=1, ResetToUntrainedState=1, L=1 1 1 1
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranch_NextSegInh/Project.ini \
  -s -t 160 -x -S
```

---

## 8. Связанные материалы

- [`ALGORITHM.md`](ALGORITHM.md) — amp-eq и § EnableNextSegmentInhibition  
- [`TimeNeuronTimeLearnerBranchTest/README.md`](../TimeNeuronTimeLearnerBranchTest/README.md)  
- [`TimeNeuronTimeLearnerBranchTest_NextSegInh/README.md`](../TimeNeuronTimeLearnerBranchTest_NextSegInh/README.md)  
- [`TimeNeuronTimeLearnerBranch_NextSegInh/README.md`](../TimeNeuronTimeLearnerBranch_NextSegInh/README.md)

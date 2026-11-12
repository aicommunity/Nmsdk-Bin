# Selectivity + Presynaptic Inhibition — Report

Date: 2026-08-13  
Dataset / protocol: StructTrain `TimeNeuronTimeLearner` / `TimeNeuronTimeLearnerTest` (8 trials), `FixedLTZThreshold=0.0115` (без thr-sweep Phase A).  
Метрика: `NPatternResponseAnalyzer` → `SelectivityLog/results.csv` (`match` 0/1).

## 1. Formulas

Tip-синапс (`NPulseSynapse::ACalculate2`):

- `PreOutput` ← secretion (вход) / dissociation (тишина)
- при `UsePresynapticInhibition`: `Output = C * (1 − k · PreOutput) · PreOutput` (clamp ≥ 0)
- иначе: `Output = C · PreOutput`

где `k = InhibitionCoeff`, `C = OutputConstData`.

Нормализация пика квадратика `p − k p²` при `p* = 1/(2k)` равна `C/(4k)`:

- канон: `C = 4k/R` → пик **`1/R`** (как линейный режим при `p → 1`);
- legacy bug в `SetInhibitionCoeff`: `C = 4(k+1)/R` → пик `(1+1/k)/R` (для k=0.5 → `3/R`).

**Исправление (PulseLib):** `SetInhibitionCoeff` выровнен с `SetResistance` / `SetUsePresynapticInhibition`: при PSI и `k>0` → `C=4k/R`, иначе `1/R`. То же для `NPulseSynChannel` / `NContinuesSynChannel::SetInhibitionCoeff` (убрать `+1`). Docs: [`NPulseSynapse.md`](../../../../Libraries/Nmsdk-PulseLib/Docs/Components/NPulseSynapse.md).

`R` у `NPSynapseBio` **не меняли** (`2e7*4.3`).

## 2. Storage chain

Регистрация в `NPulseLibrary.cpp` (без правок `NNeuronTimeLearner`):

| k | Synapse | Membrane | Neuron |
|--:|---------|----------|--------|
| — | `NPSynapseBio` | `NPMembraneBio` | `NSPNeuronGen` |
| 0.5 | `NPSynapseBioPreinh0_5` | `NPMembraneBioPreinh0_5` | `NSPNeuronGenPreinh0_5` |
| 1.0 | `NPSynapseBioPreinh` | `NPMembraneBioPreinh` | `NSPNeuronGenPreinh` |
| 2.0 | `NPSynapseBioPreinh2_0` | `NPMembraneBioPreinh2_0` | `NSPNeuronGenPreinh2_0` |

Preinh-синапс: копия Bio + `InhibitionCoeff=k`, `UsePresynapticInhibition=true`.  
Мембрана: `SynapseClassName` → Preinh (Exc и Inh tip из одного класса).  
Нейрон: зеркало `NSPNeuronGen` с Preinh-мембраной, LTZone thr=0.0117.

После train в Model: baseline PSI=0 (240 флагов); Preinh PSI=1 на tip (16), `InhibitionCoeff` = 0.5 / 1 / 2.

## 3. Config map

| EXP | NeuronClassName | k | Train Done? | L после train | Tip R | Accuracy |
|-----|-----------------|--:|:-----------:|---------------|-------|:--------:|
| EXP00_baseline | `NSPNeuronGen` | — | да | `[49,41,25,1]` | ~25–61M / 86M | **4/8** |
| EXP01_preinh_050 | `NSPNeuronGenPreinh0_5` | 0.5 | **нет** (phase 0, 160 с) | `[1,1,1,1]` | 86M×4 | **1/8** |
| EXP02_preinh_100 | `NSPNeuronGenPreinh` | 1.0 | **нет** | `[1,1,1,1]` | 86M×4 | **1/8** |
| EXP03_preinh_200 | `NSPNeuronGenPreinh2_0` | 2.0 | **нет** | `[1,1,1,1]` | 86M×4 | **1/8** |

Cold start Train: `ResetToUntrainedState=1`, `DendriteLength=1 1 1 1`, tip R=86e6×4, `IsNeedToTrain=1`, `StructureBuildMode=1`.

## 4. Per-EXP tables

### EXP00 — baseline (обучен)

CSV: [`EXP00_baseline/Test/SelectivityLog/results.csv`](EXP00_baseline/Test/SelectivityLog/results.csv)

| trial | class | ISI | ltz_max | soma0 | soma1 | soma2 | soma3 | fired | match |
|------:|------:|-----|--------:|------:|------:|------:|------:|:-----:|:-----:|
| 0 | 1 | 0.08/0.16/0.24 | 0.011815 | 0.01446 | 0.01566 | 0.02209 | 0.01583 | 1 | 1 |
| 1 | 0 | 0.24/0.16/0.08 | 0.010778 | 0.01605 | 0.01599 | 0.02232 | 0.01583 | 0 | 1 |
| 2 | 0 | 0.16/0.08/0.24 | 0.011808 | 0.01605 | 0.01599 | 0.02232 | 0.01583 | 1 | 0 |
| 3 | 0 | 0.16/0.16/0.16 | 0.010756 | 0.01067 | 0.01058 | 0.01578 | 0.01578 | 0 | 1 |
| 4 | 0 | 0.02/0.22/0.24 | 0.011765 | 0.01798 | 0.01863 | 0.02925 | 0.02294 | 1 | 0 |
| 5 | 0 | 0.24/0.22/0.02 | 0.011712 | 0.01810 | 0.01870 | 0.02927 | 0.01821 | 1 | 0 |
| 6 | 0 | 0.04/0.04/0.40 | 0.011732 | 0.02312 | 0.02537 | 0.03730 | 0.01738 | 1 | 0 |
| 7 | 0 | 0.40/0.04/0.04 | 0.011231 | 0.02496 | 0.02537 | 0.03730 | 0.01738 | 0 | 1 |

Accuracy **4/8**. FP: trials 2,4,5,6 (как Phase A EXP00).

### EXP01 — k=0.5 (train не сошёлся)

| trial | class | ISI | ltz_max | soma_* (равны) | fired | t_rel | match |
|------:|------:|-----|--------:|-----------------|:-----:|------:|:-----:|
| 0 | 1 | 0.08/0.16/0.24 | 0.013873 | 0.01387 | 1 | 0.0055 | 1 |
| 1 | 0 | 0.24/0.16/0.08 | 0.013876 | 0.01388 | 1 | 0.0055 | 0 |
| 2 | 0 | 0.16/0.08/0.24 | 0.013876 | 0.01388 | 1 | 0.0055 | 0 |
| 3 | 0 | 0.16/0.16/0.16 | 0.013821 | 0.01382 | 1 | 0.0055 | 0 |
| 4 | 0 | 0.02/0.22/0.24 | 0.013821 | 0.01382 | 1 | 0.0055 | 0 |
| 5 | 0 | 0.24/0.22/0.02 | 0.013821 | 0.01382 | 1 | 0.0055 | 0 |
| 6 | 0 | 0.04/0.04/0.40 | 0.014038 | 0.01404 | 1 | 0.0055 | 0 |
| 7 | 0 | 0.40/0.04/0.04 | 0.014038 | 0.01404 | 1 | 0.0055 | 0 |

Accuracy **1/8** (только trained trial; остальные FP). Немедленный спайк на каждом trial (`t_rel≈5.5 ms`), L=1.

### EXP02 — k=1.0 (train не сошёлся)

Accuracy **1/8**. Паттерн как EXP01: fire на всех 8, `t_rel≈4.5–5 ms`, `ltz_max` ~0.0136–0.0154.

### EXP03 — k=2.0 (train не сошёлся)

Accuracy **1/8**. Fire на всех 8, `t_rel≈8 ms`, `ltz_max` ~0.0140–0.0152.

## 5. Comparison

| Source | Accuracy | Примечание |
|--------|:--------:|------------|
| Phase A EXP00 | 4/8 | те же FP 2,4,5,6 |
| Preinh EXP00 | **4/8** | cold retrain → L=`[49,41,25,1]`, совпадает с Phase A |
| Preinh EXP01–03 | **1/8** | обучение **не** достигло Done |

### Почему Preinh train ломается

Сравнение `FinishTrainingIteration` iter=0:

- **EXP00 (без PSI):** `peakValid=[1,1,1,1]`, `amp≈0.015…`, нормальные `peakRel` / delays → рост дендритов → Done (~5.5 мин).
- **EXP01–03 (PSI):** с iter=0 до конца `-t 160`: `peakValid=[0,0,0,0]`, `amp=[0,0,0,0]`, `lastAbsDt` залип на sentinel `1.501` → **нет** роста длины/R, `IsNeedToTrain` остаётся 1, phase не уходит с 0.

То есть при tip PSI learner **не видит** амплитудные пики сомы на стимулах — структура не строится. Тест на «сырых» L=1 даёт неселективный ранний спайк (1/8).

Частые/близкие FP Phase A (trials 4, 6) **не** изолированы PSI: при несходящемся train все non-target — FP.

Риск плана: Inh tip тоже с PSI — в данном прогоне не отделялся; доминирует полный сбой детекции пиков.

## 6. Conclusion

- Фикс `C=4k/R` и цепочки Storage Preinh реализованы; baseline без PSI воспроизводит **4/8**.
- Включение PSI на tip (`k ∈ {0.5,1,2}`) при неизменном Bio `R` и текущем `NNeuronTimeLearner` **ломает обучение**: пики amp не валидны → нет Done → test 1/8.
- PSI в этом setup **не улучшает** selectivity; лучший (единственный валидный) результат — EXP00 без PSI.
- Дальнейшие гипотезы (вне этого прохода): другой масштаб/порядок включения PSI после роста структуры; PSI только на Exc; адаптация learner к форме EPSP при квадратике; меньший `k` или другой `DissociationTC`.

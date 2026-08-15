## EXP05_preinh_300 — Test (селективность, 8 trials)

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP05_preinh_300/Test`  
**Статус:** экспериментальный конфиг StructTrain / SelectivityPresynapticInhib

### Назначение

Проверяет обученный нейрон на наборе из 8 стимулов (`SelectivityLog/results.csv`).
Веса синхронизируются из Train (`copy_config.sh sync`).

### Параметры нейрона

- **NeuronClassName:** `NSPNeuronGenPreinh3_0`
- **k (PSI):** `3.0`
- **Autothr:** `AutoCalibrateFixedLTZThreshold=1`, mode=`gap_fraction`, fraction=`0.85`, clamp ≈`[0.0115, 0.05]`
- **Cold train (типично):** `IsNeedToTrain=1`, `ResetToUntrainedState=1`, `StructureBuildMode=1`, стартовые L=`[1,1,1,1]`

### Структура модели

```mermaid
flowchart TD
  ds[NDataset / стимул] --> tip[Tip ExcSynapse PSI]
  tip --> cable[Dendrite cable]
  cable --> soma[Soma membranes]
  soma --> ltz[LTZone]
  ltz --> out[Output spike]
  learner[NNeuronTimeLearner] --> tip
  learner --> cable
```

### Эксперимент

1. Обучение структуры на целевом паттерне (sync длин + нормализация амплитуд).
2. `EndOfLearning` → `CalibrateFixedLTZThresholdFromTraining` (`thr = min + 0.85·(max−min)` по last synced LTZ).
3. Тест: 8 trials, метрика `match` в `SelectivityLog/results.csv`.

### Watch-метрики

| Chart | Свойство | Смысл |
|---|---|---|
| Dendrite Amplitudes | `DendriteNeuronAmplitude[i]` | `DendriteN_1.SumPotential` |
| Neuron Sums | `DendriticSumPotential` | avg `SumChannelInput` каналов сомы (`≈/4`) |
| Neuron Sums | `SomaSumPotential` | avg `Output` каналов сомы |

`DendriticSumPotential ≈ mean(DendriteNeuronAmplitude[1..4]) = DendriteNeuronAmplitude[0]/4`.  
Подробнее: [корневой README серии](../../README.md).

### Использование

```bash
# после sync Train→Test:
NeuroModelerConsole -c Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP05_preinh_300/Test/Project.ini -s -t 20 -x
```

Родительский обзор: [`../README.md`](../README.md).

### Связанные материалы

- [`REPORT_k_sweep.md`](../../REPORT_k_sweep.md) — сводка k-sweep
- [`REPORT_gui_autothr.md`](../../REPORT_gui_autothr.md) — GUI/autothr
- Компоненты: `Libraries/Nmsdk-PulseLib/Docs/Components/NNeuronTimeLearner.md`

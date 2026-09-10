# TimeNeuronTimeLearnerBranchTest_PreInh250

Тест селективности после обучения с **PSI k=2.5**
([`TimeNeuronTimeLearnerBranch_PreInh250`](../TimeNeuronTimeLearnerBranch_PreInh250/)).

- `NeuronClassName = NSPNeuronGenPreinh2_5`
- Tip Exc: `NPSynapseBioPreinh2_5` (`UsePresynapticInhibition=1`, `InhibitionCoeff=2.5`)
- `DendriteLength = [97, 50, 25, 1]`, `FixedLTZ ≈ 0.1136`
- Analyzer: `PostPatternWindow=0.5`, `LateResponseWindow=1.5`
- Watch (`Interface.xml` tab_1 верхний): Pattern / Dendritic / Soma / `LTZone.Potential (вход)`

Исследование порога: [`../TimeNeuronTimeLearnerBranch/REPORT_preinh250_threshold.md`](../TimeNeuronTimeLearnerBranch/REPORT_preinh250_threshold.md).

## Прогон

```bash
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranchTest_PreInh250/Project.ini \
  -s -t 20 -x
```

## Sync checklist (обязательно после Train)

Копировать с Train не только Neuron/TipR/FixedLTZ, но и learner-якоря (`MembraneClassName`, PSI, `AttenuationGamma`, …), **Generator→ExcSynapse** на сегменты `L[i]`, Dataset/Analyzer оставить тестовые.

## Метрики (после полного sync)

| | baseline amp-eq | NextSegInh | **PreInh250** |
|--|:---:|:---:|:---:|
| **acc (match)** | 6/8 | 7/8 | **7/8** |
| fn | 0 | 0 | **0** |
| fp | 2 | 1 | **1** (trial 6) |
| late_fp | 2 | 4 | **3** (1, 2, 7) |

| trial | class | fired | late | soma_sum | match | error_class |
|------:|------:|------:|-----:|---------:|------:|:-----------:|
| 0 | 1 | 1 | 0 | 0.1137 | 1 | ok |
| 1 | 0 | 0 | 1 | 0.1136 | 1 | late_fp |
| 2 | 0 | 0 | 1 | 0.1136 | 1 | late_fp |
| 3 | 0 | 0 | 0 | 0.0868 | 1 | ok |
| 4 | 0 | 0 | 0 | 0.1062 | 1 | ok |
| 5 | 0 | 0 | 0 | 0.1047 | 1 | ok |
| 6 | 0 | 1 | 0 | 0.1180 | 0 | fp |
| 7 | 0 | 0 | 1 | 0.1140 | 1 | late_fp |

Target soma ≈ FixedLTZ → детекция есть. Ошибки — fp/late_fp (как у NextSegInh), не FN от «завышенного» thr.

# TimeNeuronTimeLearnerBranchTest_PreInh250

Тест селективности после обучения с **PSI k=2.5**
([`TimeNeuronTimeLearnerBranch_PreInh250`](../TimeNeuronTimeLearnerBranch_PreInh250/)).

- `NeuronClassName = NSPNeuronGenPreinh2_5`
- Tip Exc: `NPSynapseBioPreinh2_5` (`UsePresynapticInhibition=1`, `InhibitionCoeff=2.5`)
- `DendriteLength = [97, 50, 25, 1]`, `FixedLTZ ≈ 0.1136`
- Analyzer: `PostPatternWindow=0.5`, `LateResponseWindow=1.5`

## Прогон

```bash
./Bin/Platform/Linux/NeuroModelerConsole \
  -c Bin/Configs/SpikeSamples/StructTrain/TimeNeuronTimeLearnerBranchTest_PreInh250/Project.ini \
  -s -t 20 -x
```

## Метрики

| | baseline amp-eq | NextSegInh | **PreInh250** |
|--|:---:|:---:|:---:|
| **acc (match)** | 6/8 | 7/8 | **7/8** |
| fn | 0 | 0 | **1** (trial 0) |
| fp | 2 | 1 | **0** |
| late_fp | 2 | 4 | **0** |

| trial | class | fired | late | soma_sum | match | error_class |
|------:|------:|------:|-----:|---------:|------:|:-----------:|
| 0 | 1 | 0 | 0 | 0.0599 | 0 | fn |
| 1 | 0 | 0 | 0 | 0.0568 | 1 | ok |
| 2 | 0 | 0 | 0 | 0.0578 | 1 | ok |
| 3 | 0 | 0 | 0 | 0.0454 | 1 | ok |
| 4 | 0 | 0 | 0 | 0.0559 | 1 | ok |
| 5 | 0 | 0 | 0 | 0.0524 | 1 | ok |
| 6 | 0 | 0 | 0 | 0.0836 | 1 | ok |
| 7 | 0 | 0 | 0 | 0.0785 | 1 | ok |

Target soma (0.060) &lt; FixedLTZ (0.114) → FN; nontargets все ниже порога (в т.ч. trial 6). Late-спайков нет.

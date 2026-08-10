# TimeNeuronTimeLearner

Минимальный пример `NNeuronTimeLearner`: один компонент с `StructureBuildMode=1` сам собирает `Neuron` + `DatasetMatrix` и fan-out `Generator1` на все дендриты.

## Параметры

- `NumInputDendrite = 4`
- `InputPattern` ISI: `0 / 0.01 / 0.01 / 0.01` (первый импульс в t=0 пачки)
- `IterationGap = 0.5` (параметр `t`)
- `Delay = 0.5` (пауза датасета между пачками)
- `SyncTolerance = 1e-6`
- `IsNeedToTrain = 1`, `TrainingLTZThreshold = 100`

Эталон wiring без learner: локальный `Configs/Users/user/TimePatternDetectionTest01` (`PNeuron2` + внешний `DatasetMatrix`; каталог user в `.gitignore`).

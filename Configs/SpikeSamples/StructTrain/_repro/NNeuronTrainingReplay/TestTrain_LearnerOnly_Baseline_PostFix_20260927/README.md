# TestTrain: NNeuronLearner baseline, post-fix replay

Clean clone of `Bin/Configs/Bakhshiev/TestTrain`. It contains only the newer `NNeuronLearner`; `NNeuronTrainer` and its links were removed. `UseAutoPreset=0`, `ProjectAutoSaveModelTimeInterval=10`, `CalculationMode=3`, and `TimeStep=2000`. Model parameters and the starting topology were retained from the source project.

Run from this directory with the Release console, for example:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' -c '.\project.ini' -s -t 120 -x -S
```

## Result

The manually monitored clean run produced a confirmed checkpoint at about 113 model seconds: `DendriteLength=[4,3,2,1]`, `NumSynapse=[169,169,169,1]`, `IsNeedToTrain=1`; the training matrices were still empty. Learning had not converged. The process was stopped after preserving the paired model/parameter snapshot to avoid spending more wall time on the same active trajectory.

The learner adds one synapse per active input at a time while the measured amplitude is below the calibrated one-segment target. This is ongoing structural progress, not evidence of a count/index error or of eventual convergence. See the replay README and `NNeuronStructuralTrainingAudit.md` for the post-fix AutoPreset comparison and constraints on model parameters.

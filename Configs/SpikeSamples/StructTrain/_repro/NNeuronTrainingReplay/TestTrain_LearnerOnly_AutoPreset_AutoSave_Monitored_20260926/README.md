# Monitored AutoPreset NNeuronLearner run (2026-09-26)

Fresh clone of `Bakhshiev/TestTrain` with only `NNeuronLearner`, `UseAutoPreset=1`, and `ProjectAutoSaveModelTimeInterval=10`. The neuron model settings, `TimeStep=2000`, and `CalculationMode=3` match the baseline.

Run in Release:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' -c '.\project.ini' -s -t 240 -x -S *> '.\training-run.log'
```

The console completed 240 model seconds in about four minutes of wall time and logged the final save. Final state: `DendriteLength=[4,3,2,1]`, `NumSynapse=[1,1,1,1]`, `IsNeedToTrain=0`; `TrainingDendIndexes` and `TrainingSynapsisNum` each contain four rows. The estimator changed only the initial dendrite lengths; the synapse counts remained one per input.

The XML files here are the completed result. For a clean rerun, copy `TestTrain_LearnerOnly_AutoSaveFresh` and set `UseAutoPreset=1` in both `Model_00.xml` and `Parameters_00.xml`.

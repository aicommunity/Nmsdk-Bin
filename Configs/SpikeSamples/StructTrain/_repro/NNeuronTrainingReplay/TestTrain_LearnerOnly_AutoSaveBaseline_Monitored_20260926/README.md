# Monitored baseline NNeuronLearner run (2026-09-26)

Clone of `Bakhshiev/TestTrain` with only `NNeuronLearner`; `UseAutoPreset=0`. The neural model settings, original `TimeStep=2000`, and `CalculationMode=3` were retained. `ProjectAutoSaveModelTimeInterval=10`.

Run in Release:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' -c '.\project.ini' -s -t 240 -x -S *> '.\training-run.log'
```

The clean run started at 21:43:54. The console log confirms model-time saves through 101 seconds. At the confirmed 101-second sample, `DendriteLength=[4,3,2,1]`, `NumSynapse=[154,154,154,1]`, and `IsNeedToTrain=1`; the training matrices were empty. Earlier observed checkpoints showed steadily increasing synapse counts while the dendrite lengths remained fixed.

The process was stopped to avoid spending further wall-clock time reproducing an already observed nonconverged baseline. A later paired XML write parsed successfully and contains `NumSynapse=[167,167,167,1]`, `IsNeedToTrain=1`, and `DendriteLength=[4,3,2,1]`; the process was stopped before its matching auto-save completion line, so its exact model time is unknown. Use the earlier clean `TestTrain_Baseline_Fresh120` record for the confirmed 120-second comparison (`[179,179,179,1]`, still active).

The XML files in this directory are the latest captured model and parameter snapshot, not a clean starting point. Restart a fresh run from `TestTrain_LearnerOnly_AutoSaveFresh`.

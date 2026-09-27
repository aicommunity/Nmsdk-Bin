# NClassifier recognition smoke after reset/threshold fix

A fresh clone of `NClassifier_AResetTopologyFix_20260927` with `DataFromFile=1`. The three input rows are `TrainingPatterns` rows 0, 4, and 8 from the original `!OldConfigs/Test_3classes_4ex` project, one stored training example per class. The original configuration was not changed. Run command:

```powershell
NeuroModelerConsole.exe -c Project.ini -s -t 6 -x -S
```

The saved historical classifier state had `IsNeedToTrain=0`, `LTZThreshold=100` on child trainers, `FixedLTZThreshold=0.0035`, and `UseFixedLTZThreshold=0`. Before the first run, these exact stale child thresholds produced `000` for all three inputs; the old file reader also wrote one duplicate row after EOF.

The included `Parameters_00.xml` is reset to that stale child-threshold state so the reset fix can be reproduced. With the repaired Release binary, `NClassifier::AReset()` restores all child trainer thresholds to `0.0035`. The completed replay produced exactly three rows, with no EOF duplicate:

```text
111
111
111
```

The saved model has six class-to-class inhibitory links for three classes. The three exact training examples still activate all three class outputs in the window. Under the documented response rule, all three results are ambiguous; no `argmax` is applied. This is a behavioral failure of this smoke configuration, not evidence that the inhibitory links are missing.

The console wrote the three output rows and saved the model and parameters, then exited with code 1 while reporting a logging-file creation failure.
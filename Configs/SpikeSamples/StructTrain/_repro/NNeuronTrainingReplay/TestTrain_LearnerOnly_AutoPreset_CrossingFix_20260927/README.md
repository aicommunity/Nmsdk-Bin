# Repeat after the convergence fix

Fresh replay clone of `Bakhshiev/TestTrain`, containing only the newer `NNeuronLearner`. `UseAutoPreset=1`; the source model has one synapse per input, and the model/training parameters are unchanged. `TimeStep=2000`, `CalculationMode=3`, autosave every 10 model seconds.

Release run:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' -c '.\project.ini' -s -t 240 -x -S
```

Result: pending.

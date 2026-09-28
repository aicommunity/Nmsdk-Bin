# TestTrain baseline after learner convergence fix

Fresh clone of `Bakhshiev/TestTrain`, containing only `NNeuronLearner`. `UseAutoPreset=0`; all neuron and training parameters are unchanged. `TimeStep=2000`, `CalculationMode=3`, autosave every 10 model seconds.

Release run:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' -c '.\project.ini' -s -t 240 -x -S
```

Result: pending.

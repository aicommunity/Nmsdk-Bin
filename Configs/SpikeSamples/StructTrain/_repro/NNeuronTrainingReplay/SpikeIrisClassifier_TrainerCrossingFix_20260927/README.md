# SpikeIrisClassifier replay after NNeuronTrainer convergence fix

Fresh clone of `Bin/Configs/SpikeSamples/Classifier/SpikeIrisClassifier`. The three source `NNeuronTrainer` components, Iris examples, model parameters, `CalculateMode=4` (current fall-through to mode 6), `TimeStep=2000`, and `SynapseResistanceStep=1e9` are preserved. The only project-level changes are `CalculationMode=3`, `ProjectAutoSaveModelTimeInterval=10`, and the distinct project name.

Release run:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' -c '.\Project.ini' -s -t 240 -x -S
```

Result: pending.

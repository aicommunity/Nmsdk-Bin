# TestTrain: NNeuronLearner with AutoPreset, post-fix replay

Clean clone of `Bin/Configs/Bakhshiev/TestTrain`. The clone contains only the newer `NNeuronLearner`; `NNeuronTrainer` and its links were removed. `UseAutoPreset=1`, `ProjectAutoSaveModelTimeInterval=10`, `CalculationMode=3`, `TimeStep=2000`. Neuron parameters and all training inputs remain from the source project.

Run with the Release console from this directory:

```powershell
& 'E:\Science-Repo\nmsdk-git\Bin\Platform\Win\NeuroModelerConsole.exe' -c '.\project.ini' -s -t 120 -x -S
```

## Result

The run reached the 120 model-second limit and wrote a final pair of model and parameter files. `DendriteLength=[4,3,2,1]`, `InitialSomaPotential` is nonzero for all inputs (approximately `[0.0157814,0.0157814,0.0157814,0.0157814]`), `NumSynapse=[179,179,179,1]`, `IsNeedToTrain=1`; both training result matrices remain empty. The process then logged the known `UEngineControl::PauseChannel` close timeout after saving.

This result is important because the pre-fix AutoPreset runs had reported completion at the original one-synapse structure. The fixed run calibrates the target on the original topology, applies the estimated lengths, evaluates the changed structure, and continues adding synapses. It reaches the same count as the baseline learner at its 120-second checkpoint; on this input AutoPreset does not remove the long amplitude-normalization phase. This is a non-converged checkpoint, not a completed training result.

The estimated lengths were `[4,3,2,1]`; the calibration dendrite remains length 1. No membrane, channel, synapse, threshold, or timing parameter was optimized. The source config was not modified.

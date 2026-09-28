# Type-matched Trainer sweep: medium_spread

Fresh structural training from the exact saved classifier neuron subtree: `NSPNeuron` with `NPulseLTZoneThreshold`. The pattern is the only training/model input varied across this sweep. Neuron and synapse physical parameters and both LTZone thresholds are copied from the seed unchanged. `IsNeedToTrain=1`; the run uses 120 model seconds and 10-second model/parameter autosaves.

InputPattern: `[0.05, 0.09, 0.13, 0.16, 0.2]`

Run from this directory with `NeuroModelerConsole.exe -c Project.ini -s -t 120 -x -S`.

The passive recorder writes `TrainerSpikeProbe/ltz.csv`. At completion, compare `TrainingDendIndexes`, `TrainingSynapsisNum`, `NumDendriteMembranePartsVec`, and the LTZone rising-edge count per 2-second input period.

# NSPNeuron: LTZone threshold diagnostic

Post-training response replay cloned from [the source/potential probe](../NNeuronTrainer_NSPNeuron_SyntheticTTFS_FreshBuild_SourceTrace_20260928/README.md). The structural tree, synapses, input generators, membrane and channel parameters are unchanged. Only the trainer's LTZone detection threshold is set to 0.0025 in this isolated diagnostic clone; it is not used as a model-physics or training recommendation.

The direct trace shows a maximum `Soma1.SumPotential` of about `0.002554` and a maximum integrated `LTZone.OutputPotential` of `0.002078`; at threshold `0.0025` the LTZone emits no fronts. The output potential is the signal actually compared by this `NPLTZone`, so the soma sum must not be substituted for it.

Run for 1.4 model seconds at 0.5 ms steps. This clone is diagnostic only; the threshold change is not a production recommendation.

Run from this directory with Release: `NeuroModelerConsole.exe -c Project.ini -s -t 1.4 -x -S`. Trace: `TrainerSpikeProbe/dynamics.csv`.

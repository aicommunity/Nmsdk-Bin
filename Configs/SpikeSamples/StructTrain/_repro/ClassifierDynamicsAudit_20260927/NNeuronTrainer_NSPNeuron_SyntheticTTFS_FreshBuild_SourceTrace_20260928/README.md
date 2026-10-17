# NSPNeuron Trainer source and potential trace

Post-training replay of [NNeuronTrainer_NSPNeuron_SyntheticTTFS_FreshBuild_20260927](../NNeuronTrainer_NSPNeuron_SyntheticTTFS_FreshBuild_20260927/README.md). The trained tree, parameters, input periods and neuron class are copied unchanged; `IsNeedToTrain` remains false. The sole addition is a passive recorder for the three source outputs, the terminal excitatory synapse output on each branch, soma `SumPotential`, and LTZone. This checks whether the zero-LTZ trace from the fresh-built NSPNeuron experiment reflects absent source pulses, weak synaptic drive, or a failure to spike.

The project runs for 1.4 model seconds at 0.5 ms steps, enough to observe two generator cycles. It does not retrain or alter neuron physics.

Measured source fronts are at `0.110/0.130/0.1505` s and repeat near `0.7765/0.7965/0.817` s. Each terminal synapse reaches `7.5e-10`; `Soma1.SumPotential` peaks near `0.002554`. LTZone remains zero in both periods. The paired threshold probes additionally record `LTZone.OutputPotential` directly.

Run from this directory with Release: `NeuroModelerConsole.exe -c Project.ini -s -t 1.4 -x -S`.

Trace: `TrainerSpikeProbe/dynamics.csv`.

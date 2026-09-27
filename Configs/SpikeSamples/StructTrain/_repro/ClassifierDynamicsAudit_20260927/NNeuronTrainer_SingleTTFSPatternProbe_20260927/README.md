# NNeuronTrainer single TTFS response probe

Clone of the final post-fix TestTrain Trainer model. The Learner is disabled. A passive one-column recorder samples NeuronTrainer.Neuron.LTZone.Output every 0.5 ms. SpikesFrequency=0.5 Hz gives a 2 s input period; the 1.2 s project window contains one presentation of the saved TTFS vector and its response. The output file counts every rising LTZone edge; this distinguishes multiple neuron spikes from repeated input presentations.

The neuron class remains NSPNeuronGen, the trained topology and neuron/synapse parameters come from the completed Trainer replay, and no structural training runs in this probe. The input pulse rate is changed only to isolate one presentation.

Run with the existing Release console:
NeuroModelerConsole.exe -c Project.ini -s -t 1.2 -x -S

Trace: TrainerSpikeProbe/ltz.csv.
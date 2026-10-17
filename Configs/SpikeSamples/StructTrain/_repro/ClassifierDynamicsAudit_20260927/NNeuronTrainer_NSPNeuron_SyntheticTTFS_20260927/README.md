# NNeuronTrainer with the classifier neuron type

Fresh clone of the legacy single-trainer SpikeTrainer sample. It uses NSPNeuron, the exact neuron class serialized by the structural classifiers, and mode 6. The synthetic TTFS input has three deterministic delays [0.01, 0.03, 0.05] seconds, SpikesFrequency=1.5 Hz, and the existing neuron/model parameters are retained. IsNeedToTrain is enabled.

A passive one-column recorder samples NeuronTrainer.Neuron.LTZone every 0.5 ms. The project stops at 80 model seconds and saves checkpoints every 10 model seconds. Rising LTZone edges are analyzed relative to the 0.6667 s input period; this separates within-response bursts from responses to later presentations.

Run with the proven Release console:
NeuroModelerConsole.exe -c Project.ini -s -t 80 -x -S

Trace: TrainerSpikeProbe/ltz.csv. Model and Parameters XML contain the final structure and trainer status.
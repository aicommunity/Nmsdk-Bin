# NNeuronTrainer with the exact classifier neuron subtree

The top-level object is NNeuronTrainer, but its saved neuron, LTZone, membranes, synapses and internal links are copied from the real synthetic NSpikeClassifier Trainer1. This keeps the classifier's serialized NSPNeuron + NPulseLTZoneThreshold subtree instead of substituting the NSPNeuron default NPLTZone preset. Its original five-input TTFS vector and neuron physics are retained; IsNeedToTrain is enabled and CalculateMode is set to 6. Internal transit sources are made autonomous after detaching the outer classifier generator links.

The passive one-column recorder samples the Trainer's LTZone every 0.5 ms. The run stops at 120 model seconds with 10-second model/parameter autosaves.

Run with the proven Release console:
NeuroModelerConsole.exe -c Project.ini -s -t 120 -x -S

Trace: TrainerSpikeProbe/ltz.csv.
# NNeuronTrainer with the classifier neuron type — fresh build

Fresh structural build from the legacy SpikeTrainer component template. Embedded sources and neuron were removed from the clone so the NNeuronTrainer builder creates them using the configured NSPNeuron class and the three-entry synthetic TTFS vector [0.01, 0.03, 0.05]. CalculateMode=6, IsNeedToTrain=1, SpikesFrequency=1.5 Hz; all neuron and synapse defaults come from the original SpikeTrainer NSPNeuron component. The original config is unchanged.

A passive one-column recorder samples NeuronTrainer.Neuron.LTZone every 0.5 ms. Project maximum time is 80 model seconds and autosaves model/parameters every 10 model seconds. Analyze LTZone rising edges relative to the 0.6667 s response period to distinguish repeated responses from within-pattern bursts.

Run with the proven Release console:
NeuroModelerConsole.exe -c Project.ini -s -t 80 -x -S

Trace: TrainerSpikeProbe/ltz.csv.
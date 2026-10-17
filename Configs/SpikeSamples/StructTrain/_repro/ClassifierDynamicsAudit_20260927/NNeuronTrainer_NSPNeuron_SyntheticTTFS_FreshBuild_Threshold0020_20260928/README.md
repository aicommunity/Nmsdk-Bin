# NSPNeuron: LTZone threshold diagnostic at 0.002

Post-training replay from the same fresh-built `NSPNeuron`/`NPLTZone` synthetic TTFS experiment. The trained topology, source pulses, synapses, membranes and channels are retained. In this diagnostic clone only the trainer's current and fixed LTZone thresholds are set to 0.002; no neuron-physics property is changed and no training runs. The recorder captures input generator outputs, terminal synaptic outputs, soma sum potential, LTZone integrated output potential and LTZone pulses.

This checks whether the measured single integrated-potential lobe crosses the LTZone threshold once per input period. The trace has two LTZone rising edges, at `0.165` and `0.8315` s, one per input period. The threshold is an isolated diagnostic, not a proposed production value.

Run: `NeuroModelerConsole.exe -c Project.ini -s -t 1.4 -x -S`. Trace: `TrainerSpikeProbe/dynamics.csv`.

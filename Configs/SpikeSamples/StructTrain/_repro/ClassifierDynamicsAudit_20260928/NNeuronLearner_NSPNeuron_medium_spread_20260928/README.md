# Type-matched NNeuronLearner incremental training

This clone starts from a fully recorded `NSPNeuron` structure produced by the matching type-matched Trainer run. It uses the same membrane, channel, synapse, and input connectivity tree, then enables `NNeuronLearner` on a new synthetic five-input temporal pattern `[0.05, 0.09, 0.13, 0.16, 0.2]`. The synapse counts and dendrite lengths in the Learner config are copied from the actual input segments, preserving a valid starting graph. Training uses threshold 100 and switches to fixed threshold 0.0047 at convergence. Neuron model parameters are copied unchanged; project autosaves every 10 model seconds.

Run from this directory with `NeuroModelerConsole.exe -c Project.ini -s -t 120 -x -S`.

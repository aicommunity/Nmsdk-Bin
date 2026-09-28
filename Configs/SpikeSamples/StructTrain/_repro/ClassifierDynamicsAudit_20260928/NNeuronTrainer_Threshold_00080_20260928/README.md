# Trainer fixed-structure threshold probe (0.008)

This is a post-training replay of the wide-spread synthetic run. The trained structure and all membrane/synapse parameters are copied unchanged. Only the fixed `LTZone.Threshold` and matching Trainer threshold fields are varied; `IsNeedToTrain=0`, so no structural training runs. The neuron remains `NSPNeuron` with `NPulseLTZoneThreshold`.

Run: `NeuroModelerConsole.exe -c Project.ini -s -t 10.5 -x -S`. The recorder captures both LTZone pulses and `OutputPotential` for threshold crossing analysis.

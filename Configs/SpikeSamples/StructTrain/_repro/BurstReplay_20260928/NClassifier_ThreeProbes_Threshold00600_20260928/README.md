# NClassifier_ThreeProbes_Threshold00600_20260928

Fixed-structure recognition replay cloned from `NClassifier_WorkingThresholdReplay_20260927`. The only neural parameter changed is the LTZone threshold (0.006); trained synapse/dendrite structures and physical neuron parameters remain as saved. A passive recorder samples the named LTZone outputs every 0.5 ms so each response window can be checked for zero, one, or multiple rising edges.

Run from this directory: `NeuroModelerConsole.exe -c Project.ini -s -t 6 -x -S`.

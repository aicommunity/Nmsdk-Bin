# NSpikeClassifier_Iris3Prototypes_Threshold00047_20260928

Fixed-structure recognition replay cloned from `NSpikeClassifier_TrainerPointerFix_IrisReplay_20260927`. The only neural parameter changed is the LTZone threshold (0.0047); trained synapse/dendrite structures and physical neuron parameters remain as saved. A passive recorder samples the named LTZone outputs every 0.5 ms so each response window can be checked for zero, one, or multiple rising edges. After EOF the classifier saves DataFromFile=0; prepare a fresh clone before repeating the file replay.

Run from this directory: `NeuroModelerConsole.exe -c Project.ini -s -t 7 -x -S`.

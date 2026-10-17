# NSpikeDendriteLength_Long_D17_On_Threshold00085_20260928

Clone of `NSpikeClassifier_Class2_long_D17_On_Threshold00085_20260928` with the same already-trained network and lateral-inhibition setting. All LTZone thresholds were set to 0.0085; structures and physical parameters were not changed. The recorder was rebuilt to connect only the three class-neuron LTZone outputs, leaving all classifier input and neuron links intact. After EOF DataFromFile is saved as 0; create a fresh clone before repeating the replay.

Run: `NeuroModelerConsole.exe -c Project.ini -s -t 8.1 -x -S`.

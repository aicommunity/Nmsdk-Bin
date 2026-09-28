# NSpikeClassifier synthetic replay: lateral inhibition On, threshold 0.009

Clone of [NSpikeClassifier_Synthetic_OutputsOn_20260927](../ClassifierDynamicsAudit_20260927/NSpikeClassifier_Synthetic_OutputsOn_20260927/README.md). The four synthetic input rows and the three trained neuron structures are copied unchanged. All three `NSPNeuron` + `NPulseLTZoneThreshold` units receive the same fixed threshold through both the classifier wrapper and nested Trainer properties; training is disabled. Only LTZone threshold values, run name, and recorder filename differ from the source. Lateral inhibition setting and classifier wiring remain as in the source pair.

Run: `NeuroModelerConsole.exe -c Project.ini -s -t 8.01 -x -S`. Compare `output_data.txt` to `expected_classes.csv`, and count every rising edge in the three LTZone columns in `ClassifierDynamics/`.

# NClassifier_Synthetic_InhibitionOn_PostFix

Paired synthetic dynamics replay for `NClassifier`. This clone uses stored class training rows as pure temporal prototypes and their class-1/class-2 midpoint as an intentionally ambiguous probe. `UseLateralInhibition=1` is the only classifier-topology difference in the pair. The saved trained neuron structures and physical parameters are preserved. The recorder captures inhibitory synapse `OutInCopy` inputs separately from outputs, for every input dendrite.

Run from this directory with the Release console: `NeuroModelerConsole.exe -c Project.ini -s -t 6 -x -S`. The recorder writes signed signals every 0.5 ms to `ClassifierDynamics/signals.csv`; `expected_classes.csv` labels the three pure prototypes and the midpoint (0).


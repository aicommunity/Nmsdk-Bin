# NSpikeClassifier_Class2_D17_Syn12_On_20260928

Fixed-topology class-2 replay from the ON competition control. Branch 2 remains length 17; its active excitatory synapse count is reduced from 37 to 12. Retained synapses keep their saved physical parameters and remain connected to the same `Source2` input. Other dendrites, classifier parameters, input file and lateral-inhibition setting are unchanged. Training is disabled.

Run: `NeuroModelerConsole.exe -c Project.ini -s -t 8.1 -x -S`.

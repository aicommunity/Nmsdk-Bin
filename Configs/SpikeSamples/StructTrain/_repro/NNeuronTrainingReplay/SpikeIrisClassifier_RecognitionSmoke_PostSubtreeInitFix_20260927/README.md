# Iris recognition smoke test

This clone uses the trained Model_00.xml and Parameters_00.xml saved at model time 121 s in SpikeIrisClassifier_PostSubtreeInitFix_240_20260927. Training is disabled and DataFromFile is enabled. input_data.txt contains the three saved NSpikeClassifier training prototypes, one per classifier. The output rows are the active bits from the three neurons; expected output is one-hot for the corresponding prototype.

Run: NeuroModelerConsole.exe -c Project.ini -s -t 10 -x -S.


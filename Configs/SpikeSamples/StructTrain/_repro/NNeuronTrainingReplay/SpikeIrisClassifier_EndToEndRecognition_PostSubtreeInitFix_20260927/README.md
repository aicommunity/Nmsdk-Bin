# Iris end-to-end training and recognition replay

Fresh clone from SpikeIrisClassifier_PostTrainerInitFix_240_20260927_Seed. The three training prototypes remain in `TrainingPatterns`; after the three `NNeuronTrainer` instances finish, `NSpikeClassifier` reads the ten normalized test patterns in `input_data.txt`. Training mode and neuron parameters are unchanged. Recognition runs in the same process because runtime snapshots are not guaranteed to be resumable.

Run: NeuroModelerConsole.exe -c Project.ini -s -t 140 -x -S.

The run reached model time 140 and wrote ten rows to `output_data.txt`. The test IDs, in order, are 22, 37, 45, 60, 64, 84, 90, 111, 129, and 134. The output rows were `110, 110, 110, 011, 111, 111, 111, 111, 111, 111` (one bit per class neuron). The bit for the expected Iris class was present in all ten rows, but every row was multi-hot; this is not an exclusive one-winner result. `NSpikeClassifier::TreatDataFromFile()` accumulates a `1` if a neuron is active at any point during the test window, so these rows record all responders during the window rather than a single winner. Use them as a same-process smoke test and do not report them as a 10/10 exclusive-classification accuracy score.


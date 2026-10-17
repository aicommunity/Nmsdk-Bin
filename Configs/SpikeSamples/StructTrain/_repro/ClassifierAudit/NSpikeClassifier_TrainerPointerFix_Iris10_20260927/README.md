# Iris end-to-end training and recognition replay

Fresh clone from SpikeIrisClassifier_PostTrainerInitFix_240_20260927_Seed. The three training prototypes remain in `TrainingPatterns`; after the three `NNeuronTrainer` instances finish, `NSpikeClassifier` reads the ten normalized test patterns in `input_data.txt`. Training mode and neuron parameters are unchanged. Recognition runs in the same process because runtime snapshots are not guaranteed to be resumable.

Run: NeuroModelerConsole.exe -c Project.ini -s -t 140 -x -S.

The run reached model time 140 and wrote ten rows to `output_data.txt`. The test IDs, in order, are 22, 37, 45, 60, 64, 84, 90, 111, 129, and 134. The output rows were `110, 110, 110, 011, 111, 111, 111, 111, 111, 111` (one bit per class neuron). The expected class neuron was active in all ten rows, but every row was multi-hot.

In C++, the intended class competition is implemented with lateral inhibition: after training, each neuron's LTZone output is linked to inhibitory synapses on the other neurons' somas. `TreatDataFromFile()` does not expose a winner or compare activities; it accumulates a flag whenever each LTZone output exceeds `1e-5` during the sample window and writes all flags. Therefore multi-hot rows are ambiguous, not a winner that can be recovered by `argmax` from this file.

Evaluate the recorded output with the semantics above:

```powershell
python ..\evaluate_iris_classifier_output.py --project-dir .
```

The evaluator reports the expected-neuron hit rate separately from strict single-response accuracy and exits with code 2 if any row has zero, multiple, or incorrect active class neurons. For this run it reports expected-neuron active `10/10`, unique correct response `0/10`, and ambiguous multi-neuron response `10`.


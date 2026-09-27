# NSpikeClassifier Iris inhibition trace

Release replay of a clone of the saved, trained Iris classifier. Only the clone's `DataFromFile` flag and project name were changed; trained structures and neuron physical parameters were kept as loaded. Run command:

```powershell
NeuroModelerConsole.exe -c Project.ini -s -t 22 -x -S
```

`output_data.txt` contains ten rows for IDs 22, 37, 45, 60, 64, 84, 90, 111, 129, and 134:

```text
110
110
110
011
011
111
011
111
111
111
```

The response contract records a class bit if its LTZone output exceeds `1e-5` at any time in the sample window. All ten rows are therefore ambiguous. No winner or `argmax` is inferred.

`classifier_dynamics.tsv` is a temporary diagnostic trace sampled every 0.5 ms. It contains the three LTZone outputs and, for `Soma1` of each class neuron, the outputs of its lateral inhibitory synapses and inhibitory channel. The trace insertion was removed from C++ after this run, so reproducing this diagnostic requires adding temporary per-step instrumentation; ordinary classifier output is unchanged.

Observed LTZone rising-edge counts by test row were:

| IDs | Pulses by class `[1,2,3]` | Recorded bits |
|---|---:|---:|
| 22, 37, 45 | `[4,1,0]` | `110` |
| 60, 64 | `[0,4,1]` | `011` |
| 84 | `[1,3,2]` | `111` |
| 90 | `[0,4,2]` | `011` |
| 111, 129, 134 | `[1,3,2]` | `111` |

The lateral paths were present after reset: 30 external class-to-competitor connections and 30 inhibitory-synapse-to-channel connections. A class-2 pulse at model time `0.224` reached class 1's inhibitory synapse at `0.2245` (`5e-9`); by class 1's first later pulse at `0.293`, that synapse output had decayed to about `7e-12`. This trace shows signal transfer and a timing gap; it does not by itself quantify inhibition against a no-inhibition control.

The console wrote the full trace and ten output rows, then exited with code 1 while reporting failure to create a logging file. The result files are complete.
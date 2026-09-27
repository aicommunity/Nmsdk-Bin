# Historical arbitrary-structure replay: relearning_2

Cloned from the archived 2022 experiment. The archived InputPattern in Parameters_00.xml contained invalid tiny values; this clone replaces only that vector with the first complete five-value pattern from the accompanying historical input_data.txt (0.0444 0.1417 0.0169 0.0250 0.2000). Existing dendrite lengths and synapse counts are preserved. CalculateMode is set to 0 so the current learner can stop itself on convergence; UseAutoPreset stays disabled (default). Model and synapse parameters are unchanged.

Run with the Release console: NeuroModelerConsole.exe -c project.ini -s -t 120 -x -S.



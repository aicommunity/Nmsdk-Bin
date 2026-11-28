# TimeLearner tools migration

The Branch dynamics analyzer and its tests have moved to the root repository.
Run from the root checkout:

```text
python -m Scripts.StructTrain.TimeLearner analyze /path/TimeLearnerTrainingDynamics.log --format branch-dynamics --time-step-hz 2000 --output NEW-summary.json
```

No executable wrapper remains in Bin. This is descriptive schema-1 Branch
telemetry analysis; it proves neither complete experiment observations nor
classification, and its local gain estimate is not a whole-model stability proof.
Use the actual model frequency and envelope. Existing outputs are not replaced.

[Migration sources, checks and limits](../../../../../Docs/StructTrain/TimeLearner/BranchDynamicsMigration.ru.md).
The remaining tools in this directory still require separate migration/review.

Four historical AsymRm leaf tools were retired on23.11.2026: `compare_l_target.py`,
`done_fingerprint.py`, `verify_pattern_span.py`, `verify_element_params.py`.
Their original sources are in Bin commit `8cb6dba07b30432272984c8ce3136b48ad06f064`,
under `Configs/SpikeSamples/StructTrain/SelectivityAsymRm/scripts/`.
No wrapper is retained. Models, configurations, measurements and historical
criteria are unchanged. The remaining eleven AsymRm Python tools and the
shared matrix/analysis tools still require migration; this is not full acceptance.

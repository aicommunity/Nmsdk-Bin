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

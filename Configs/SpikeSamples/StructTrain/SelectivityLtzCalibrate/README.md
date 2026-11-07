# Historical LTZ campaign: launcher retirement

Sixteen campaign setup/run/reset helpers and the regression verifier are retired
from the current tree. Their exact sources remain in Bin commit
`fc67a3b0958e8becdfbe1cd3f0e4e054d966d54f`; the root
`Docs/StructTrain/TimeLearner/script_migration.json` records every path/blob.
Configurations, models, primary data and old scientific observations are retained.

New experiments use the root `Scripts/StructTrain/TimeLearner` package with
capability preflight and native model transport. This does not claim a drop-in
scientific equivalent of every old LTZ scenario. The shared `copy_config.sh` /
`copy_config_branch.sh` still have historical external callers and remain pending
with the other Python analysis tools. This is a partial migration.


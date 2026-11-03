# Historical SoftCold/OpenGaps/T2/T4 launchers

The eleven historical shell launchers listed below were retired without wrappers.
Configurations, models, trial data and scientific reports remain preserved.
New jobs use the root Scripts/StructTrain/TimeLearner package and explicit job/runtime manifests.
This does not resume historical Series D or assert runtime parity with its mutable queues.

Retrieval snapshot Bin: `39d811e5e0798eecf124f32356c9fc6edbe4538a`. The root
Docs/StructTrain/TimeLearner/script_migration.json records full commits, blobs,
SHA256, sizes and git-show commands. This snapshot identifies script contents,
not the code combination of an old experiment.

| Retired path | Historical function |
|---|---|
| `Configs/SpikeSamples/StructTrain/scripts/open_gaps_remain6_waiter.sh` | Historical OpenGaps six-case waiter; pattern-based process intervention and fixed old RCS/queue paths. |
| `Configs/SpikeSamples/StructTrain/scripts/open_gaps_w0_diag.sh` | Historical OpenGaps W0 subset; old posttune_verify, shared logs, RCS and case manifest. |
| `Configs/SpikeSamples/StructTrain/scripts/run_canon_soft.sh` | Historical Branch/FastSpan two-repeat cold harness and implicit old registry commits. |
| `Configs/SpikeSamples/StructTrain/scripts/run_invest_ab.sh` | Historical fixed A1/A2/B1/B2 investigation harness and shared status files/commits. |
| `Configs/SpikeSamples/StructTrain/scripts/softcold_c_batch.sh` | Historical C1/C2 fixed case list using old posttune_verify and shared runtime. |
| `Configs/SpikeSamples/StructTrain/scripts/softcold_full49_status_snapshot.sh` | Historical full49 status from old RCS/log/process names; rc0 is not modern scientific PASS. |
| `Configs/SpikeSamples/StructTrain/scripts/softcold_full_matrix.sh` | Historical serial full49 queue and legacy registry updates; shared workspace/runtime. |
| `Configs/SpikeSamples/StructTrain/scripts/softcold_full_matrix_parallel.sh` | Historical full49 xargs queue/shared RCS; labels rc0 as PASS, not a training certificate. |
| `Configs/SpikeSamples/StructTrain/scripts/softcold_w4_status_snapshot.sh` | Historical W4 full49 status tied to old logs/RCS and process names. |
| `Configs/SpikeSamples/StructTrain/_repro/runs/T2_control_batch.sh` | Historical T2 three-case Branch/Asym control batch; old shared Console and posttune harness. |
| `Configs/SpikeSamples/StructTrain/_repro/runs/T4_cold_matrix.sh` | Historical September D4/T4 fixed six-case matrix; old shared runtime and historical audit outputs. |

Example: `git show 39d811e5e0798eecf124f32356c9fc6edbe4538a:Configs/SpikeSamples/StructTrain/scripts/open_gaps_remain6_waiter.sh`.

Remaining generic legacy runners, analyzers and campaign tools require separate migration.

# Post-train tuning in the teacher module

[Russian contract and property table](POST_TRAIN_TUNING.ru.md) · [Review](../../../../Docs/Audit/TimeLearner-2026-09-24-review/README.md)

Checked against PulseLib d4149190 / Bin 9733281, 2026-09-24. Both learners use phase 0 for joint synchronization/normalization and phase 2 for Done. TL PostTune is phase 3; Branch PostTune is phase 4, with legacy calibration in phase 3 when PostTune is off. Best-effort termination does not certify selectivity.

Defaults: EnablePostTrainTuning=true, AutoScaleIterationGap=true. Tip modes: Off, CanonRmin, FlatLastR, KeepDone, SearchSynthetic. Both learners now reprobe selected BestTips; failure to set up the final Search free-run is explicit, and rejected metrics are invalidated after fallback.

Inference calibrates on the current Test Matrix with sample 0 as target, then evaluates that matrix. This is the accepted A07 contract. Held-out generalization is a separate optional objective.

Finite helper checks and the global-maximum foil gap are fixed. Both finalizers protect a bad landscape with a silent threshold; Branch Search Train remains silent for a subsequent Test calibration. TL Search can retain a valid mid computed during Train; that is not a fresh Test calibration. However, an unvisited foil is still represented as zero, live NaN can disappear during peak aggregation, and timeout can still commit a threshold. PostTuneResult codes (0 None, 1 Success, 2 NonSeparable, 3 SetupFailure, 4 Timeout, 5 InvalidMetrics) are not reset for every new attempt; Complete/Result alone do not certify valid calibration.

Branch Auto uses the shared soma, TL Auto uses LTZ. Explicit Branch LTZ is still contaminated by an unconditional soma accumulator. TL Soma iteration reads the terminal sum while free-run measures the peak sum. These paths need a common collector.

Timing is gap=span+settle+slack and dataset delay=settle+slack. AutoScale=0 restores max(configured,physical); disabling PostTune alone does not reproduce an older binary. The 85/90 s wall measurements imply about 1.06×, while 6× is only the gap ratio.

The [developer result summary](_repro/POSTTUNE_VERIFY_RESULT.md) reports two PASS among seven cold cases. Complete fresh run artifacts are unavailable here. The improved verifier still permits stale Test calibration and some incomplete Train/Search paths. A reverted Search PASS would establish fallback quality, not a search improvement. See the review and [verification contract](POST_TRAIN_VERIFY.ru.md). A12 remains deferred under the small-step assumption.

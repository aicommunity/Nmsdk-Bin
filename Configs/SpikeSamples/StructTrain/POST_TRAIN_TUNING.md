# Post-train tuning in the teacher module

[Russian contract and property table](POST_TRAIN_TUNING.ru.md) · [Current implementation audit](AUDIT_2026-09-22.md)

Checked against PulseLib 9a6cee0b / Bin 2d1d0214 and reconciled working-tree documentation, 2026-09-23. Both learners perform joint synchronization and amplitude normalization in phase 0. Phase 1 is unused, Done is 2; PostTune is 3 for TimeLearner and 4 for Branch. Branch phase 3 is legacy CalibrateLtz with PostTune disabled. Best-effort exits mean Done is not a selectivity certificate.

Defaults: EnablePostTrainTuning=true, AutoScaleIterationGap=true. Old XML inherits these defaults. Disabling PostTune alone does not reproduce an older binary's behavior.

Tip modes: 0 Off; 1 CanonRmin (2e7 for first N−1 tips, 8.6e7 last); 2 FlatLastR (8.6e7 all); 3 KeepDone; 4 SearchSynthetic. Branch search still calls ScaleTipR for its fallback snapshot. Branch now starts a fresh free-run for selected BestTips, reverting to its KeepDone/ScaleTipR snapshot on failure. With mid enabled, Search Train keeps a silent threshold and marks inference-mid done to prevent a second calibration in that process. Ordinary TimeLearner still has the old candidate/metric mismatch. Branch setup failure can still finalize zero metrics, and fallback flags can pair snapshot weights with rejected-candidate metrics.

Timing: gap=span+settle+slack; dataset delay=settle+slack. AutoScale=1 ignores the XML floor; AutoScale=0 takes max(configured, physical). See [timing](docs/TIMING_AND_GAP.ru.md).

Inference-mid probes the current Test Matrix, treating sample 0 as target regardless of MatrixClasses, then evaluates the same matrix. This is the accepted current algorithm contract (A07), not a defect. Its measurements describe calibration-set quality; held-out generalization would be a separate research objective.

Ordinary TimeLearner inference may still commit a threshold for an invalid landscape. Branch now keeps the silent threshold for bad finite metrics, but NaN bypasses validation (target .5, foil NaN yields mid .495). Complete/InferenceMidDone remain true after a failed finite calibration. Branch Auto/Soma means shared soma (CSV soma_amp_sum); explicit LTZ selection is still ignored by free-run.

The [saved verification table](_repro/POSTTUNE_VERIFY_RESULT.md) separates the new 16:47:46Z one-case br100_search report from the old 11:33:05Z smoke rows. It does not demonstrate all cold-training cases in the [verification plan](POST_TRAIN_VERIFY.ru.md). The verifier does not currently enforce every declared fires/TipR expectation or reject all stale child-run results.

The phase8/phase9 --skip-tipr-mid gates use C++ mid and may run Test twice when the initial threshold is silent. Record all overrides and data provenance; retain same-matrix calibration as the current contract; a held-out assessment is optional separate research.

Timing rollback: AutoScaleIterationGap=0 restores max(configured, physical); changing kMinSettle is separate. The reported 85/90 s wall measurements imply about 1.06x, whereas 6x is only the simulation-gap ratio, not an established end-to-end speedup.

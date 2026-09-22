Clone of Branch100 packA gen for C++ PostTune **SearchSynthetic** (mode=4).

**Pin:** `PostTrainTipSearchIters=12`, `AutoScaleIterationGap=1` (physics gap ≪ XML 1.5). BestTips only if `landscape_ok`; expect Test fires `10000000`.

**Validation:** full soft-cold **Train** with `PostTrainTipResistanceMode=4` (not Test-only / `--skip-train` smoke). After Train, TipR must differ from the keep clone **or** `posttune_complete.flag` must contain `search_reverted=1`. Then Test C++ inference mid + gate.

Gate: `phase8_tiprmin_gate.py --skip-tipr-mid`.  
Orchestrator: `scripts/posttune_verify.py --case br100_search`.

Keep clone (mode=3 TipR reference): [`../EXP_br_span100_packA_gen_C1e9_posttune_keep`](../EXP_br_span100_packA_gen_C1e9_posttune_keep).

See [`POST_TRAIN_TUNING.ru.md`](../../POST_TRAIN_TUNING.ru.md), [`docs/TIMING_AND_GAP.ru.md`](../../docs/TIMING_AND_GAP.ru.md), [`POST_TRAIN_VERIFY.ru.md`](../../POST_TRAIN_VERIFY.ru.md) §V5b.

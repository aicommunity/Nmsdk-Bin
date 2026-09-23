# EXP_br_span25_packA_gen_C1e9

PHASE8 Branch short-span packA **gen** @25 ms, neuron `NSPNeuronGenAsymRmD001C1e9`, GTS=20000.

| Field | Value |
|-------|-------|
| Status | **PASS** `ok_audit=1` (S1) |
| Train L | `13 11 7 1` (`IsNeedToTrain=0`) |
| TipR@Rmin | `2e7 2e7 2e7 8.6e7` |
| Mid thr | `0.07179975` (`soma_amp_sum`) |
| Gate | fires `10000000`, `late_fp=0`, `ok_single`, `t_rel=0.1128` ≥ 0.8·pattern_end |
| CSV | [`Test/SelectivityLog/results.csv`](Test/SelectivityLog/results.csv) |

Hygiene: overlay Train Neuron tree into Test; Generator tips `Dendrite1_{13,11,7,1}`; Parameters Matrix from AsymRm packA; Model SB Learner=1 / Neuron=2.

Parent: [`../PHASE8_SHORTSPAN.md`](../PHASE8_SHORTSPAN.md).

> Working soft_cold clone for posttune_verify (calibration-quality). Not PHASE12 VALIDATED_CLONE.
Gold: `EXP_br_span25_packA_gen_C1e9`. Soft_cold via `scripts/posttune_verify.py`.

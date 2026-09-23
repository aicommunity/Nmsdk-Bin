# PostTune verify result

Generated: 2026-09-23T23:03:59Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| br100_search | done_search_reverted | 0 | search | `7.42148e+07 8.9215e+07 1.33473e+08 5.2067e+08` | 0.00714187 | 0.007181835 | `10000000` | cpp | same_reverted | 1 | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |

## Calibration-quality follow-up 2026-09-23

Generated: 2026-09-23T23:04:49Z
Console: `Bin/Platform/Linux/NeuroModelerConsole` SHA `1b719f6f140e82a0da3999ab02c7fce0d183a0c34b5e7521b623c730ec48720f`
quality_class=`calibration-quality` (A07 same-Matrix). Not PHASE12 VALIDATED / not held-out.

| case | verdict | train_status | tipr_class | mid_source | fires | run |
|------|---------|--------------|------------|------------|-------|-----|
| br25_on | FAIL | done_gate_FAIL_gate_rc=1 | canon | missing | `0` | 20260923T144228Z |
| br25_off | FAIL | exited | other | missing | `11110000` | 20260923T144521Z |
| asym25 | FAIL | done_gate_FAIL_gate_rc=1 | flat | missing | `` | 20260923T122748Z |
| asym50 | PASS | done | canon | cpp | `10000000` | 20260923T123001Z |
| br100_keep | FAIL | done_gate_FAIL_gate_rc=1 | keep | missing | `0` | 20260923T124019Z |
| phase6_480 | FAIL | exited_gate_FAIL_gate_rc=1 | canon | missing | `` | 20260923T190804Z |
| br100_search | PASS | done_search_reverted | search | cpp | `10000000` | 20260923T215645Z |

### Notes
- A01: Branch DatasetMatrix bind + legacy `IsPatternComplete>=4`; Test `stim_count=4`.
- soft_cold: force `FixedLTZThreshold=1` (tiprmin mid leak stalled Phase6).
- Gold Branch Test still PASS on new Console (inherited weights, mid≈0.0718).
- **PASS:** `asym50`, `br100_search` (`search_reverted`, mid_source=cpp, fires=10000000).
- **FAIL:** Branch soft_cold retrain NonSeparable / wrong fires (`br25_on/off`, `br100_keep`); `asym25`; `phase6_480` gate.
- A12 Euler diagnostic remains FAIL (deferred).


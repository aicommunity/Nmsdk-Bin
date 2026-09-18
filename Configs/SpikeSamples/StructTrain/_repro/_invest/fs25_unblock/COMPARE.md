# PHASE12 compare EXP_span25ms_fast_C1e9

Generated: 2026-09-18T09:15:03Z

| role | L | TipR | thr | fires | acc | mode | ok_audit | last_pulse | Need |
|------|---|------|-----|-------|-----|------|----------|------------|------|
| gold | `6 5 4 1` | `20000000 20000000 20000000 86000000` | 0.0328372 | `10000000` | 8 | selective | 1 | 1 | 0 |
| r1 | `6 5 4 1` | `86000000 86000000 86000000 86000000` | 0.0328372 | `` |  |  |  | 0 | 1 |
| r2 | `` | `` |  | `` |  |  |  |  |  |

**verdict:** `incomplete`


## Rootcause note (W3a)

Need never reached 0 after soft-cold + 180×3 windows. L recovered to gold `6 5 4 1` on extend#1 but IsNeedToTrain stayed 1. Gold TipR tiprmin not applied (train incomplete). PulseLib unchanged (`780ffc7`).

# PostTune verify result

Generated: 2026-10-03T00:21:47Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| ltz100_gen | done_flag_flush_gate_FAIL_gate_rc=1 | 0 | canon | `2e07 2e07 2e07 8.6e07` | 1 | 0.006681 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `ltz100_gen` — fires_missing.

**FAIL**: `ltz100_gen` — gate_fail.

**FAIL**: `ltz100_gen` — gate_rc=1.

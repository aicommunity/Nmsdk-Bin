# PostTune verify result

Generated: 2026-10-01T23:21:39Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| pa01_ltz_sweep | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 100000000000 86000000` | 1 | 0.0135 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `pa01_ltz_sweep` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `pa01_ltz_sweep` — Need=1.

**FAIL**: `pa01_ltz_sweep` — fires_missing.

**FAIL**: `pa01_ltz_sweep` — gate_fail.

**FAIL**: `pa01_ltz_sweep` — tipr_class=other expect=canon.

**FAIL**: `pa01_ltz_sweep` — gate_rc=1.

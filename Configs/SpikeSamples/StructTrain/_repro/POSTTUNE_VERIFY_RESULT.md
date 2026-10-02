# PostTune verify result

Generated: 2026-10-02T10:24:04Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| br480_tiprmin | exited_gate_FAIL_gate_rc=1 | 1 | other | `86000000 21120661,787493013 20000000 86000000` | 1 | 0.05149 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `br480_tiprmin` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `br480_tiprmin` — Need=1.

**FAIL**: `br480_tiprmin` — fires_missing.

**FAIL**: `br480_tiprmin` — gate_fail.

**FAIL**: `br480_tiprmin` — tipr_class=other expect=canon.

**FAIL**: `br480_tiprmin` — gate_rc=1.

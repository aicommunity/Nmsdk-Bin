# PostTune verify result

Generated: 2026-10-02T08:14:19Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| br480_nextseg | exited_gate_FAIL_gate_rc=1 | 1 | other | `86000000 20000000 20000000 86000000` | 1 | 0.036298 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `br480_nextseg` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `br480_nextseg` — Need=1.

**FAIL**: `br480_nextseg` — fires_missing.

**FAIL**: `br480_nextseg` — gate_fail.

**FAIL**: `br480_nextseg` — tipr_class=other expect=canon.

**FAIL**: `br480_nextseg` — gate_rc=1.

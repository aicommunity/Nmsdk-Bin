# PostTune verify result

Generated: 2026-10-02T14:00:49Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| br100_nextseg | exited_gate_FAIL_gate_rc=1 | 1 | flat | `86000000 86000000 86000000 86000000` | 1 | 0.014432775 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `br100_nextseg` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `br100_nextseg` — Need=1.

**FAIL**: `br100_nextseg` — fires_missing.

**FAIL**: `br100_nextseg` — gate_fail.

**FAIL**: `br100_nextseg` — tipr_class=flat expect=canon.

**FAIL**: `br100_nextseg` — gate_rc=1.

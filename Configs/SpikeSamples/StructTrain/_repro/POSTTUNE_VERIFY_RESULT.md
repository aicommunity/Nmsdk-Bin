# PostTune verify result

Generated: 2026-10-02T16:51:41Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| br50_nextseg | exited_gate_FAIL_gate_rc=1 | 1 | flat | `86000000 86000000 86000000 86000000` | 1 | 0.0412798 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `br50_nextseg` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `br50_nextseg` — Need=1.

**FAIL**: `br50_nextseg` — fires_missing.

**FAIL**: `br50_nextseg` — gate_fail.

**FAIL**: `br50_nextseg` — tipr_class=flat expect=canon.

**FAIL**: `br50_nextseg` — gate_rc=1.

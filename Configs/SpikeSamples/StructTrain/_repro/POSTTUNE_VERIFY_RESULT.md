# PostTune verify result

Generated: 2026-10-03T10:08:58Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| phase6_480 | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 100000000000 86000000` | 1 | 0.016894 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `phase6_480` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `phase6_480` — Need=1.

**FAIL**: `phase6_480` — fires_missing.

**FAIL**: `phase6_480` — gate_fail.

**FAIL**: `phase6_480` — tipr_class=other expect=canon.

**FAIL**: `phase6_480` — mid_source=missing.

**FAIL**: `phase6_480` — gate_rc=1.

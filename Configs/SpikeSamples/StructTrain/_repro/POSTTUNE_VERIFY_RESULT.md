# PostTune verify result

Generated: 2026-10-01T23:57:07Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| pa02_ltzone_avg | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 100000000000 86000000` | 1 | 0.0115 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `pa02_ltzone_avg` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `pa02_ltzone_avg` — Need=1.

**FAIL**: `pa02_ltzone_avg` — fires_missing.

**FAIL**: `pa02_ltzone_avg` — gate_fail.

**FAIL**: `pa02_ltzone_avg` — tipr_class=other expect=canon.

**FAIL**: `pa02_ltzone_avg` — gate_rc=1.

# PostTune verify result

Generated: 2026-10-03T02:43:39Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| ltz100_preinh | exited_gate_FAIL_gate_rc=1 | 1 | other | `20000000 2214365280,8328686 23200009835,585091 8` | 1 | 0.006681015 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `ltz100_preinh` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `ltz100_preinh` — Need=1.

**FAIL**: `ltz100_preinh` — fires_missing.

**FAIL**: `ltz100_preinh` — gate_fail.

**FAIL**: `ltz100_preinh` — tipr_class=other expect=canon.

**FAIL**: `ltz100_preinh` — gate_rc=1.

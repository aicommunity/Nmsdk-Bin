# PostTune verify result

Generated: 2026-10-03T08:26:24Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| tn_classic | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 100000000000 86000000` | 1 | 0.0115 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `tn_classic` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `tn_classic` — Need=1.

**FAIL**: `tn_classic` — fires_missing.

**FAIL**: `tn_classic` — gate_fail.

**FAIL**: `tn_classic` — tipr_class=other expect=canon.

**FAIL**: `tn_classic` — gate_rc=1.

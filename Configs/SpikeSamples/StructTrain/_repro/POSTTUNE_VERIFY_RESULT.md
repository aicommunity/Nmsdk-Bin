# PostTune verify result

Generated: 2026-10-02T00:14:41Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| pa06_ltzone_int | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 100000000000 86000000` | 1 | 0.012 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `pa06_ltzone_int` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `pa06_ltzone_int` — Need=1.

**FAIL**: `pa06_ltzone_int` — fires_missing.

**FAIL**: `pa06_ltzone_int` — gate_fail.

**FAIL**: `pa06_ltzone_int` — tipr_class=other expect=canon.

**FAIL**: `pa06_ltzone_int` — gate_rc=1.

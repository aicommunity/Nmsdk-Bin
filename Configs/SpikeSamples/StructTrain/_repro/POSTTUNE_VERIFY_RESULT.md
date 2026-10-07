# PostTune verify result

Generated: 2026-10-06T11:46:43Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| pa00_baseline | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 49486853,68223004 8600` | 1 | 0.0115 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `pa00_baseline` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `pa00_baseline` — Need=1.

**FAIL**: `pa00_baseline` — fires_missing.

**FAIL**: `pa00_baseline` — gate_fail.

**FAIL**: `pa00_baseline` — tipr_class=other expect=canon.

**FAIL**: `pa00_baseline` — gate_rc=1.

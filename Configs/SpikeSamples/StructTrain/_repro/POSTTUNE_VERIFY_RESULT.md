# PostTune verify result

Generated: 2026-10-03T06:58:09Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| phase6_ltzcal_twin | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 24933198,870636258 860` | 1 | 0.0115 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `phase6_ltzcal_twin` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `phase6_ltzcal_twin` — Need=1.

**FAIL**: `phase6_ltzcal_twin` — fires_missing.

**FAIL**: `phase6_ltzcal_twin` — gate_fail.

**FAIL**: `phase6_ltzcal_twin` — tipr_class=other expect=canon.

**FAIL**: `phase6_ltzcal_twin` — gate_rc=1.

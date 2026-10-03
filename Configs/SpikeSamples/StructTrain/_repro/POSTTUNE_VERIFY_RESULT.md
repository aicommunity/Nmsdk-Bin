# PostTune verify result

Generated: 2026-10-03T08:09:10Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| phase6_preinh250 | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 100000000000 86000000` | 1 | 0.038722 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `phase6_preinh250` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `phase6_preinh250` — Need=1.

**FAIL**: `phase6_preinh250` — fires_missing.

**FAIL**: `phase6_preinh250` — gate_fail.

**FAIL**: `phase6_preinh250` — tipr_class=other expect=canon.

**FAIL**: `phase6_preinh250` — gate_rc=1.

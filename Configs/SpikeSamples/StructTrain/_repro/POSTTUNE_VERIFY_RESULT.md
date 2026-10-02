# PostTune verify result

Generated: 2026-10-02T02:08:03Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| psi31_200 | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 100000000000 86000000` | 1 | 0.026530975419262328 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `psi31_200` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `psi31_200` — Need=1.

**FAIL**: `psi31_200` — fires_missing.

**FAIL**: `psi31_200` — gate_fail.

**FAIL**: `psi31_200` — tipr_class=other expect=canon.

**FAIL**: `psi31_200` — gate_rc=1.

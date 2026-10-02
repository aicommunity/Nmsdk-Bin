# PostTune verify result

Generated: 2026-10-02T01:22:50Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| psi21_100 | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 20000000 100000000000 86000000` | 1 | 0.032068136638248895 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `psi21_100` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `psi21_100` — Need=1.

**FAIL**: `psi21_100` — fires_missing.

**FAIL**: `psi21_100` — gate_fail.

**FAIL**: `psi21_100` — tipr_class=other expect=canon.

**FAIL**: `psi21_100` — gate_rc=1.

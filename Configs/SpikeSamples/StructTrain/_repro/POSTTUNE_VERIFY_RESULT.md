# PostTune verify result

Generated: 2026-10-01T23:39:43Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| psi01_050 | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 100000000000 86000000` | 1 | 0.019783117337822249 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `psi01_050` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `psi01_050` — Need=1.

**FAIL**: `psi01_050` — fires_missing.

**FAIL**: `psi01_050` — gate_fail.

**FAIL**: `psi01_050` — tipr_class=other expect=canon.

**FAIL**: `psi01_050` — gate_rc=1.

# PostTune verify result

Generated: 2026-10-02T00:51:29Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| psi15_270 | exited_gate_FAIL_gate_rc=1 | 1 | other | `20000000 100000000000 100000000000 86000000` | 1 | 0.029941307767947452 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `psi15_270` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `psi15_270` — Need=1.

**FAIL**: `psi15_270` — fires_missing.

**FAIL**: `psi15_270` — gate_fail.

**FAIL**: `psi15_270` — tipr_class=other expect=canon.

**FAIL**: `psi15_270` — gate_rc=1.

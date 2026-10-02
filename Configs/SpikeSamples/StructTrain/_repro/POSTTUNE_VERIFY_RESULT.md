# PostTune verify result

Generated: 2026-10-02T00:32:50Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| psi14_260 | exited_gate_FAIL_gate_rc=1 | 1 | other | `20000000 100000000000 100000000000 86000000` | 1 | 0.030192631385274865 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `psi14_260` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `psi14_260` — Need=1.

**FAIL**: `psi14_260` — fires_missing.

**FAIL**: `psi14_260` — gate_fail.

**FAIL**: `psi14_260` — tipr_class=other expect=canon.

**FAIL**: `psi14_260` — gate_rc=1.

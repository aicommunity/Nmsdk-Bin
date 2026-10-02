# PostTune verify result

Generated: 2026-10-02T05:29:36Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| psi34_400 | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 100000000000 86000000` | 1 | 0.013324476537935281 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `psi34_400` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `psi34_400` — Need=1.

**FAIL**: `psi34_400` — fires_missing.

**FAIL**: `psi34_400` — gate_fail.

**FAIL**: `psi34_400` — tipr_class=other expect=canon.

**FAIL**: `psi34_400` — gate_rc=1.

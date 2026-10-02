# PostTune verify result

Generated: 2026-10-02T07:03:09Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| psi35_400 | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 100000000000 86000000` | 1 | 0.030470579914581682 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `psi35_400` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `psi35_400` — Need=1.

**FAIL**: `psi35_400` — fires_missing.

**FAIL**: `psi35_400` — gate_fail.

**FAIL**: `psi35_400` — tipr_class=other expect=canon.

**FAIL**: `psi35_400` — gate_rc=1.

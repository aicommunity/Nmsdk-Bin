# PostTune verify result

Generated: 2026-10-02T03:59:09Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| psi33_300 | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 56964097477,309082 860` | 1 | 0.030180398266633643 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `psi33_300` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `psi33_300` — Need=1.

**FAIL**: `psi33_300` — fires_missing.

**FAIL**: `psi33_300` — gate_fail.

**FAIL**: `psi33_300` — tipr_class=other expect=canon.

**FAIL**: `psi33_300` — gate_rc=1.

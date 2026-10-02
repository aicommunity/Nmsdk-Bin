# PostTune verify result

Generated: 2026-10-02T03:03:06Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| psi32_300 | exited_gate_FAIL_gate_rc=1 | 1 | other | `16273090608,359373 100000000000 100000000000 860` | 1 | 0.013138779500447591 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `psi32_300` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `psi32_300` — Need=1.

**FAIL**: `psi32_300` — fires_missing.

**FAIL**: `psi32_300` — gate_fail.

**FAIL**: `psi32_300` — tipr_class=other expect=canon.

**FAIL**: `psi32_300` — gate_rc=1.

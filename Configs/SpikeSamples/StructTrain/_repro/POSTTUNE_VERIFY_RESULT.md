# PostTune verify result

Generated: 2026-10-03T05:51:49Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| ltz50_preinh | exited_gate_FAIL_gate_rc=1 | 1 | other | `3637644293,4453001 32723828847,89056 20000000 86` | 1 | 0.011759 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `ltz50_preinh` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `ltz50_preinh` — Need=1.

**FAIL**: `ltz50_preinh` — fires_missing.

**FAIL**: `ltz50_preinh` — gate_fail.

**FAIL**: `ltz50_preinh` — tipr_class=other expect=canon.

**FAIL**: `ltz50_preinh` — gate_rc=1.

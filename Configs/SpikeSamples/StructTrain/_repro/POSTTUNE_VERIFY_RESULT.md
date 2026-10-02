# PostTune verify result

Generated: 2026-10-02T09:18:19Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| br480_preinh | exited_gate_FAIL_gate_rc=1 | 1 | other | `86000000 100000000000 20000000 86000000` | 1 | 0.111136 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `br480_preinh` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `br480_preinh` — Need=1.

**FAIL**: `br480_preinh` — fires_missing.

**FAIL**: `br480_preinh` — gate_fail.

**FAIL**: `br480_preinh` — tipr_class=other expect=canon.

**FAIL**: `br480_preinh` — gate_rc=1.

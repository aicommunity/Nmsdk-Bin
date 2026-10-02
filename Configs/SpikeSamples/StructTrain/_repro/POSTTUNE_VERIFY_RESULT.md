# PostTune verify result

Generated: 2026-10-02T23:18:18Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| fs100_preinh | exited_gate_FAIL_gate_rc=1 | 1 | other | `20000000 20000000 312493826,55794299 86000000` | 1 | 0.00708053 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `fs100_preinh` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `fs100_preinh` — Need=1.

**FAIL**: `fs100_preinh` — fires_missing.

**FAIL**: `fs100_preinh` — gate_fail.

**FAIL**: `fs100_preinh` — tipr_class=other expect=canon.

**FAIL**: `fs100_preinh` — gate_rc=1.

# PostTune verify result

Generated: 2026-10-02T20:13:44Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| fs100_gen | exited_gate_FAIL_gate_rc=1 | 1 | other | `20000000 20000000 82624552,650614992 86000000` | 1 | 0.01568185 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `fs100_gen` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `fs100_gen` — Need=1.

**FAIL**: `fs100_gen` — fires_missing.

**FAIL**: `fs100_gen` — gate_fail.

**FAIL**: `fs100_gen` — tipr_class=other expect=canon.

**FAIL**: `fs100_gen` — gate_rc=1.

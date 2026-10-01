# PostTune verify result

Generated: 2026-10-01T19:22:33Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| phase6_thr_only | exited_gate_FAIL_gate_rc=1 | 1 | other | `100000000000 100000000000 24933198,870636258 860` | 1 | 0.014386 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `phase6_thr_only` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `phase6_thr_only` — Need=1.

**FAIL**: `phase6_thr_only` — fires_missing.

**FAIL**: `phase6_thr_only` — gate_fail.

**FAIL**: `phase6_thr_only` — tipr_class=other expect=canon.

**FAIL**: `phase6_thr_only` — gate_rc=1.

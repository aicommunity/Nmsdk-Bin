# PostTune verify result

Generated: 2026-10-01T20:45:02Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| fs50_preinh | exited_gate_FAIL_gate_rc=1 | 1 | canon | `20000000 20000000 20000000 86000000` | 1 | 0.0112976 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `fs50_preinh` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `fs50_preinh` — Need=1.

**FAIL**: `fs50_preinh` — fires_missing.

**FAIL**: `fs50_preinh` — gate_fail.

**FAIL**: `fs50_preinh` — gate_rc=1.

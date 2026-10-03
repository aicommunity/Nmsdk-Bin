# PostTune verify result

Generated: 2026-10-03T03:59:03Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| ltz25_preinh | exited_gate_FAIL_gate_rc=1 | 1 | other | `41981446,205920309 169247208,02092496 274973703,` | 1 | 0.0179375 | `` | missing | — | 0 | gate_rc=1 |

**FAIL**: `ltz25_preinh` — train_incomplete:exited_gate_FAIL_gate_rc=1.

**FAIL**: `ltz25_preinh` — Need=1.

**FAIL**: `ltz25_preinh` — fires_missing.

**FAIL**: `ltz25_preinh` — gate_fail.

**FAIL**: `ltz25_preinh` — tipr_class=other expect=canon.

**FAIL**: `ltz25_preinh` — gate_rc=1.

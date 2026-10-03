# PostTune verify result

Generated: 2026-10-03T03:29:39Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| fs25_preinh | exited | 1 | other | `20000000 20000000 39619746,134807132 86000000` | 0.00984632 | 0.01563085 | `10000000` | cpp | — | 0 | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |

**FAIL**: `fs25_preinh` — train_incomplete:exited.

**FAIL**: `fs25_preinh` — Need=1.

**FAIL**: `fs25_preinh` — tipr_class=other expect=canon.

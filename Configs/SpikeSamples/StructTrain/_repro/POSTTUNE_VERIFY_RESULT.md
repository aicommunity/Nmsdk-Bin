# PostTune verify result

Generated: 2026-10-02T15:52:28Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| br25_preinh | exited | 1 | other | `20000000 20000000 67614650,093354195 86000000` | 0.0235098 | 0.05171075 | `10000000` | cpp | — | 0 | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |

**FAIL**: `br25_preinh` — train_incomplete:exited.

**FAIL**: `br25_preinh` — Need=1.

**FAIL**: `br25_preinh` — tipr_class=other expect=canon.

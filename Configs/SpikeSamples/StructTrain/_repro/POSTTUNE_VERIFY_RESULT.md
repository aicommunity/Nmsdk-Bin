# PostTune verify result

Generated: 2026-09-30T13:24:21Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| fs25_gen | exited | 1 | other | `20000000 20000000 34199674,88820222 86000000` | 0.0277604 | 0.0328372 | `10000000` | cpp | — | 0 | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |

**FAIL**: `fs25_gen` — train_incomplete:exited.

**FAIL**: `fs25_gen` — Need=1.

**FAIL**: `fs25_gen` — tipr_class=other expect=canon.

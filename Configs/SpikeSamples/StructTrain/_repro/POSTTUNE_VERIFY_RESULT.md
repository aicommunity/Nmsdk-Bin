# PostTune verify result

Generated: 2026-10-01T21:26:11Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| br25_off | done | 0 | other | `50724706,262322553 91917588,815203518 204553870,` | 0.108833 | 0.07179975 | `10110000` | missing | — | 0 | ok=1 n=8 acc=6 target_hit=1 fire_all=0 mode=selective fires=10110000 matches=110 |

**FAIL**: `br25_off` — fires=10110000 expect=10000000.

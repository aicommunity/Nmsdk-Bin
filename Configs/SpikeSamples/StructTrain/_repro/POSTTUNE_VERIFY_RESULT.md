# PostTune verify result

Generated: 2026-09-22T16:47:46Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

**Wall / gap:** br25 mid Auto `gapEff=0.25` vs legacy `1.5` (~6× sim); Search@12 ~4050 s train wall (flag@poll#135) + Test mid.  
**V5b:** Train silent mid + `search_reverted=1`; Test cpp mid≈0.00714; fires `10000000`.

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_keep | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|--------------|---------|
| br100_search | done_search_diff | 0 | search | `7.42148e+07 8.9215e+07 1.33473e+08 5.2067e+08` | 0.00714187 | 0.007181835 | `10000000` | cpp | diff | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |

# PostTune verify result

Generated: 2026-09-22T11:33:05Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_keep | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|--------------|---------|
| br25_on | skip_train | 0 | canon | `20000000 20000000 20000000 86000000` | 0.0717851 | 0.07179975 | `10000000` | cpp_train | — | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |
| asym25 | skip_train | 0 | flat | `86000000 86000000 86000000 86000000` | 0.037589 | 0.03758895 | `10000000` | cpp_train | — | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |
| br100_search | done_search_diff | 0 | search | `7.42148e+07 8.9215e+07 1.33473e+08 5.2067e+08` | 0.00714187 | 0.007181835 | `10000000` | cpp | diff | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |

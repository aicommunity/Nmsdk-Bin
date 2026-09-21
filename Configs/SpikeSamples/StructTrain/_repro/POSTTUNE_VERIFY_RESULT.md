# PostTune verify result

Generated: 2026-09-21T09:21:31Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | metrics |
|------|-------|------|------------|------|----------|----------|-------|---------|
| br25_on | done | 0 | canon | `20000000 20000000 20000000 86000000` | 0.0718001 | 0.07179975 | `10000000` | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |
| br25_off | done | 0 | other | `50724706.846699201 91917589.874117598 97357703.2` | 0.07177215 | 0.07179975 | `10000000` | ok=0 n=9 acc=9 target_hit=1 fire_all=0 mode=selective fires=100000000 matches=11 |
| asym25 | done | 0 | flat | `86000000 86000000 86000000 86000000` | 0.037589 | 0.03758895 | `10000000` | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |
| br100_keep | done | 0 | keep | `73992204.405776784 88934568.014846012 133361944.` | 0.00718182 | 0.007181835 | `10000000` | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |
| br100_search | done | 0 | search | `73992204.405776784 88934568.014846012 133361944.` | 0.00718182 | 0.007181835 | `10000000` | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |
| asym50 | done_cold_tipr_gold_mid | 0 | canon | `20000000 20000000 20000000 86000000` | 0.011759 | 0.011759 | `10000000` | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |
| phase6_480 | done_canon_gold_mid | 0 | canon | `20000000 20000000 20000000 86000000` | 0.016894 | 0.016894 | `10000010` | ok=1 n=8 acc=7 target_hit=1 fire_all=0 mode=selective fires=10000010 matches=111 |

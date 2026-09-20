# PostTune verify result

Generated: 2026-09-20T16:35:57Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | metrics |
|------|-------|------|------------|------|----------|----------|-------|---------|
| br25_on | done | 0 | canon | `20000000 20000000 20000000 86000000` | 0.0718001 | 0.07179975 | `10000000` | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |
| br25_off | done_calibrate_flush | 0 | other | `50724706.846699201 91917589.874117598 97357703.2` | 0.0163298 | 0.07179975 | `10000000` | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 |
| asym25 | skip_train_infer_mid | 0 | flat | `86000000 86000000 86000000 86000000` | 0.037589 | 0.03758895 | `10000000` | ok=1 n=8 acc=8 target_hit=1 fire_all=0 mode=selective fires=10000000 matches=111 |

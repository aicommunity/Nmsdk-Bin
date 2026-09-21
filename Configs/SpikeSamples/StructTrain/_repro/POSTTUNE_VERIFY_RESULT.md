# PostTune verify result

Generated: 2026-09-21T21:56:00Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_keep | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|--------------|---------|
| asym50 | done_cold | 0 | canon | `20000000 20000000 20000000 86000000` | 0.0116458 | 0.011759 | `10000000` | cpp | — | ok=1 n=8 acc=8 fires=10000000 |
| phase6_480 | done_canon | 0 | canon | `20000000 20000000 20000000 86000000` | 0.0168963 | 0.016894 | `10000010` | cpp | — | ok=1 n=8 acc=7 fires=10000010 |
| br100_search | done_search_diff | 0 | search | `2e+07 2e+07 2e+07 4.3e+07` | 0.0370581 | 0.007181835 | `10000010` | cpp | diff | ok=1 n=8 acc=7 target_hit=1 fires=10000010 |

## Notes

- **No `*_gold_mid` statuses.** V4/V6 mid from C++ inference (`inference=1`).
- **V5b SearchSynthetic:** soft-cold Train `mode=4` (`PostTrainTipSearchIters=3` wall-clock; path identical to 12). EventsLog `phase -> PostTune mode=4`. TipR after apply_best ≠ keep Done vector (`tipr_vs_keep=diff`, `search_reverted=0`). Flag carries `tipr=…`. Test cpp mid + gate fires `10000010` (one inverted foil under Search BestTips; keep clone remains 8/8).
- Harness: slog prune + TipR live snap; span-aware `run_nm` deadlines; overlay MidThreshold/StructureBuildMode.

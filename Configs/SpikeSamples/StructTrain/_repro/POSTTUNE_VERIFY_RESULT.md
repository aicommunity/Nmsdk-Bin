# PostTune verify result

Generated: 2026-09-25T02:39:40Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| br100_search | done_search_reverted | 0 | other | `7.39922e07 8.89346e07 1.33362e08 5.17286e08` | 0.0021371 | 0.007181835 | `00000000` | cpp | same_reverted | 1 | ok=0 n=8 acc=7 target_hit=0 fire_all=0 mode=silent fires=00000000 matches=011111 |

**FAIL**: `br100_search` — fires=00000000 expect=10000000.

## T4 cold matrix 20260924T204259Z

| case | run_id | train_status | tipr | mid | gate | tipr_vs | params_source | rc |
|---|---|---|---|---|---|---|---|---|
| `br25_off` | `br25_off_20260924T204259Z` | done | other | missing | True |  | nm_save | 1 |
| `asym25` | `asym25_20260924T214120Z` | done_flag_flush_gate_FAIL_gate_rc=1 | flat | missing | False |  | flag_flush | 1 |
| `asym50` | `asym50_20260924T214908Z` | exited | canon | cpp | True |  | nm_save | 1 |
| `br100_keep` | `br100_keep_20260924T234016Z` | done_flag_flush_gate_FAIL_gate_rc=1 | other | missing | False | same_FAIL | flag_flush | 1 |
| `phase6_480` | `phase6_480_20260924T234719Z` | exited_gate_FAIL_gate_rc=1 | other | missing | False |  | nm_save | 1 |
| `br100_search` | `br100_search_20260925T015547Z` | done_search_reverted | other | cpp | True | same_reverted | flag_flush | 1 |

- phase6 harness expect_fires=`10000010`; strict reference=`10000000` (separate verdict — not claimed PASS here)
- summary: `/home/user/Nmsdk/Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/D4_matrix_summary.json`
- **seven_pass_claim=false** (0/6 matrix PASS; gold br25_on skip-train remains separate T2 PASS)


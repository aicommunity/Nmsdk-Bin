# PostTune verify result

Generated: 2026-10-02T12:30:39Z
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | tipr_vs_snapshot | search_reverted | metrics |
|------|-------|------|------------|------|----------|----------|-------|------------|------------------|-----------------|---------|
| br100_search | search_diff_after_revert_FAIL_no_cpp_mid_gate_FAIL_gate_rc=1 | 0 | other | `73992204,084160432 88934567,628280818 133361944,` | 1 | 0.007181835 | `` | missing | diff_after_revert | 1 | gate_rc=1 |

**FAIL**: `br100_search` — train_incomplete:search_diff_after_revert_FAIL_no_cpp_mid_gate_FAIL_gate_rc=1.

**FAIL**: `br100_search` — fires_missing.

**FAIL**: `br100_search` — search_tipr:diff_after_revert.

**FAIL**: `br100_search` — search_mid:missing.

**FAIL**: `br100_search` — gate_fail.

**FAIL**: `br100_search` — mid_source=missing.

**FAIL**: `br100_search` — gate_rc=1.

# PostTune verify result — T2 control runs (tails)

Generated: 2026-09-24T18:39:45Z  
Console: `/home/user/Nmsdk/Bin/Platform/Linux/NeuroModelerConsole`  
SHA256: `5e7829bf9beb1901336ed15b7595786d5708c40d0dd9c9f2f1329bff3c3a1b63`  
Batch: `_repro/T2_control_batch_20260924T165948Z.log`  
Evidence: `Docs/Audit/TimeLearner-2026-09-24-review/evidence/tails/T2_summary.json`

| case | train | Need | TipR class | TipR | FixedLTZ | gold thr | fires | mid_source | notes |
|------|-------|------|------------|------|----------|----------|-------|------------|-------|
| br25_on gold `--skip-train` | skip_train | 0 | canon | `20000000×3+86000000` | 0.0718001 | 0.07179975 | `10000000` | cpp | **PASS** |
| br25_on soft_cold | done_gate_FAIL | 1 | flat | `86000000×4` | 1 | 0.07179975 | `` | missing | **FAIL** NonSeparable; flag tipr=canon |
| asym50 cold | exited | 1 | canon | `20000000×3+86000000` | 0.0100962 | 0.011759 | `10000000` | cpp | **FAIL** Need=1; mid≠archive `.0116458` |

**R06:** Asym50 archive Test mid `.0116458` did not enter the clean workdir result (fresh mid `.0100962`).

**Morphogenesis:** soft_cold FAIL after R01–R07 measurement fixes → P2 opened (H1 Canon vs Keep: Keep also NonSeparable).

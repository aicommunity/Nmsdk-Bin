# Scale deferred / notes (2026-09-05)

## Disk cleanup (2026-09-05)

Freed ~320 GB by deleting `StatisticLog/*` timestamp dirs under:

- `SelectivityAsymRm/` (~245 GB)
- `SelectivityPresynapticInhib/` StatisticLogs
- `SelectivityLtzCalibrate/AsymRmLtzCal/` StatisticLogs
- `TimeNeuronTimeLearnerBranchTest_savedcheck*` StatisticLogs

Kept Parameters/Models and `archives/statisticlog/*.tar.gz`. Disk now ~27% used.

## Accidental full-grid cold reset

`reset_asymrm_cold.sh EXP_…` previously treated empty `PILOT_EXPS` as **all EXP**. Fixed: requires `PILOT_EXPS` or positional EXP args (`Refuse full-grid cold reset`).

Pack A span25/50 Done restored from `Bin` git `HEAD` (`9c45613` / `a3b8b6d`). Pack A span100 + Pack B/C need retrain (Done was never committed).

## Waves

| Phase | Status |
|-------|--------|
| Pack A span25/50 | **Done** (git restore) |
| Remaining 14 EXP | `scale_remaining.log`, `MAX_JOBS=6` |
| Pack B/C span100 | included in remaining batch |

```bash
# Do NOT cold-reset without PILOT_EXPS=
PILOT_EXPS='EXP_span50ms_packC_preinh' bash scripts/reset_asymrm_cold.sh

MAX_JOBS=6 bash scripts/run_scale_bc_span25.sh
MAX_JOBS=6 bash scripts/run_scale_bc_span50.sh
MAX_JOBS=6 bash scripts/run_scale_bc_span100.sh
SKIP_COLD_RESET=1 MAX_JOBS=6 bash scripts/run_pilot_span100.sh
```

Global NeuroModelerConsole budget: **≤6**.

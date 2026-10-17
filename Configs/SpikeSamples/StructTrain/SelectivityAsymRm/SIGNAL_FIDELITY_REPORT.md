# Signal Fidelity Report

Generated during pilot v4 infrastructure setup.

## Reference (LtzCal Done)

Source: `AsymRmLtzCal/EXP_span25ms_packA_gen`  
Config: `signal_reference_span25.json`

- L: `6 5 4 1`
- `all_non_ref_sync_ok`: true
- `IsNeedToTrain`: 0

## Preinh integrity (phase 4a)

Verdict: **CORRUPT** — см. `PREINH_INTEGRITY_REPORT.md`

- Sentinel `last_abs_dt=1.501` на всех дендритах
- `peak_valid=false`, traces повреждены (disk-full era)
- **Рекомендация:** cold reset + `run_pilot_v4_preinh.sh`

## Интеграция

- `analyze_signal_fidelity.py` — метрики и gate vs reference JSON
- `run_asymrm.sh` — snapshot после length steps, gate перед amp

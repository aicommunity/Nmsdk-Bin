# Phase 4 — отложенное масштабирование

**Gate:** ≥2/3 pilot EXP с `IsNeedToTrain=0` + `--require-sync-ok`.

## Запуск после pilot v3

```bash
cd Bin/Configs/SpikeSamples/StructTrain/SelectivityAsymRm
bash scripts/scale_asymrm.sh
```

Скрипт [`scripts/scale_asymrm.sh`](scripts/scale_asymrm.sh):
1. Проверяет gate (default ≥2/3 pilot Done)
2. `sweep_asymrm_amp.sh` — 8 cases (включая tol_x125/x150)
3. Pack A оставшиеся 3 EXP (`PACK_A_EXPS=1`)
4. При ≥4/6 Pack A Done — полный run 18 EXP
5. `grid_summary.csv` + обновить `REPORT.md`

## Текущий статус

Pilot v3 запущен (`pilot_v3.log`). До завершения обучения gate **не проверяется**.

## Pack A EXP (6)

| EXP | pilot v3 |
|-----|----------|
| span25 gen | да |
| span25 preinh | да |
| span100 preinh | да |
| span50 gen | phase 4.2 |
| span50 preinh | phase 4.2 |
| span100 gen | phase 4.2 |

## C++ fallback

Только при `INFEASIBLE` после 4.1–4.4 — см. [`CPP_FALLBACK.md`](CPP_FALLBACK.md).

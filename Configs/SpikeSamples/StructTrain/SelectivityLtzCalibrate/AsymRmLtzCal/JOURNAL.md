# AsymRmLtzCal — JOURNAL

## 2026-08-27 — setup + classic grid TRAIN_T=160

- Setup 6 EXP Pack A, GTS=10000, AutoCalibrate peak 0.99, span verify 12/12 PASS.
- Train wave ~60 min (3 parallel @ GTS=10000). Все 6 EXP: L вырос (напр. span100 → `21 17 11 1`), но `IsNeedToTrain=1`, `FixedLTZ=0.0115`, `Calibrated` отсутствует.
- `verify_train_done.py --require-calibrated` → **abort** до sync/test (fail-hard).
- Пилот span25 TRAIN_T=320 отменён (L уже на плато, FastSpan historical: 320/480 не помогает classic Done).

## Сравнение с baseline

- `SelectivityAsymRm` TRAIN_T=80: train OK, 18/18 fire_all @ 0.0115.
- Offline sweep baseline span100 preinh: thr≈0.0205, fp=3 (acc 5/8) при target_hit=1.

## Branch fallback

- `AsymRmLtzCalBranch/` setup + run TRAIN_T=160/480 @ GTS=10000 и GTS=2000 — stall 6/6.
- Контроль `BranchFastSpan` D002 span25 @ GTS=2000: Done, FixedLTZ≈0.029.

## 2026-08-28 — план ремонта

- Оформлен «Главный вывод» в REPORT; детальный план: [`PROTOCOL_REPAIR.md`](PROTOCOL_REPAIR.md).
- **A–C выполнены:** parity `setup_asymrm_ltzcal.sh`, `reset_asymrm_ltzcal_cold.sh`, `run` TRAIN_T=80 default.
- **Cold reset** 6 EXP: L=`1 1 1 1`, AutoCalibrate=1, inject_analyzer на Test — OK.

### Cold retrain TRAIN_T=80 (repair protocol)

- 6/6 stall @ ~60 min: span100/50 → L=`9 1 1 1`, span25 → L=`6 5 1 1`; FixedLTZ=0.0115, NeedTrain=1.
- Post-train Parameters **идентичны baseline** AsymRm (кроме AutoCalibrate=1, mode=1, frac=0.99).

### Continue TRAIN_T=160 (+80t на тех же EXP)

- ~50 min, 6/6 stall. L прогресс: span100/50 → `9 9 1 1`, span25 → `6 5 4 1`; FixedLTZ=0.0115, NeedTrain=1.

### Continue TRAIN_T=320

- ~120 min. L: span100 gen `9 17 1 1`→`9 17 9 1`, span100 preinh `9 19 9 1`, span50 `9 9 7/6 1`, span25 `6 5 4 1`.
- **EXP_span25ms_packA_gen: Done** — NeedTrain=0, FixedLTZ=**0.0885**; verify PASS.
- Sync+test span25 gen: **acc 6/8**, mode=selective, **gate PASS** (target_hit, fp=2).

### §4 fallback (5 stall EXP, без cold reset)

- Phase1 AutoCalibrate=0, train 80t → Phase2 AutoCalibrate=1, train 40t.
- **5/5 stall** — без эффекта.

### Итог repair

- **1/6** Done+calibrated+test gate PASS (`span25 gen`).
- **5/6** stall: EndOfLearning не достигнут (amp-нормализация); offline sweep baseline по-прежнему релевантен.

# Pilot retrain — Pack A (3 EXP)

Протокол: GTS=20000, Dissoc/Secr=0.001, AutoCalibrate on, adaptive TRAIN_T 80→160→320→640 (cumulative T=1200).

## Результаты train

| EXP | L (до) | L (после) | L_target | NeedTrain | FixedLTZ | blocker |
|-----|--------|-----------|----------|-----------|----------|---------|
| span25 gen | 6 5 1 1 | **6 5 4 1** | 6 5 3 1 | 1 | 0.0115 | AMP_PENDING / LENGTH_STALL |
| span25 preinh | 6 5 1 1 | **6 5 4 1** | 6 5 3 1 | 1 | 0.0115 | AMP_PENDING |
| span100 preinh | 9 1 1 1 | **9 17 12 1** | 9 8 5 1 | 1 | 0.0115 | LENGTH_STALL |

**Прогресс:** adaptive TRAIN_T снял TIME_BUDGET на span25 (length-sync всех non-ref). span100 preinh — сильный рост L на dend1–2.

**Блокер:** amp-norm + AutoCalibrate не сработали (NeedTrain=1, FixedLTZ cold). Test: fire_all 3/3.

## Вывод

Пилот **не достиг Done** (0/3). Масштабирование на 18 EXP по плану **не запускалось** (нужно ≥4/6 Done Pack A).

Следующий шаг: amp-norm диагностика по `ResistanceStatusTrace` на span25 (L=6 5 4 1) или C++ tuning EstDelayPerSeg — только при доказанном INFEASIBLE.

# TIMING_RANGES.md — SelectivityAsymRm

Ретроспективный аудит (фаза 0.5) на 18 EXP @ GTS=10000, TRAIN_T=80, без AutoCalibrate.  
Источники: `stall_summary.csv`, `timing_feasibility.csv`.

## Сводка stall (18/18 NeedTrain=1, FixedLTZ=0.0115)

| blocker | count | типичный паттерн |
|---------|-------|------------------|
| LENGTH_STALL + NEEDS_MORE_TIME | 12 | L=`9 1 1 1` — dend0 burst, dend1–2 не дошли (TIME_BUDGET) |
| LENGTH_STALL + TIMING_MISMATCH | 6 | L близко к target, но off-by-1 (preinh span25) |

**Вывод:** 12/18 — явный **TIME_BUDGET** (iter_budget 7–10 при ~53 iter @ TRAIN_T=80). 6/18 — length почти сошлась, stall на amp-norm / off-by-one сегмент.

## L_target per (pack, span) @ EstDelayPerSeg post

EstDelayPerSeg оценён из фактического L (post-mode), не default 0.005.

| pack | span | L_target (cold/post est) | L_actual (типично) | iter_budget |
|------|------|--------------------------|--------------------|-------------|
| A | 100 | 9 8 5 1 | 9 1 1 1 | 10 |
| A | 50 | 9 8 5 1 | 9 1 1 1 | 10 |
| A | 25 | 6 5 3 1 | 6 5 1 1 | 7 |
| B | 100 | 9 8 5 1 / 20 17 11 1 (preinh) | 9 1 1 1 / 20 17 10 1 | 10 / 19 |
| B | 50 | 9 8 5 1 | 9 1 1 1 | 10 |
| B | 25 | 6 5 3 1 | 6 1 1 1 / 6 5 4 1 | 7 |
| C | 100/50 | 9 8 5 1 | 9 1 1 1 | 10 |
| C | 25 | 6 5 3 1 | 6 1 1 1 / 6 5 4 1 | 7 |

**Якорь span25 Pack A:** L≈`6 5 4 1` достижимо (Pack B/C preinh); target по формуле — `6 5 3 1` при est≈0.0052.

## GTS sweep (пилот 3 EXP, TRAIN_T=80, без adaptive)

| GTS | span25 gen | span25 preinh | span100 preinh | вывод |
|-----|------------|---------------|----------------|-------|
| 10000 | L=6 5 1 1, LENGTH_STALL | L=6 5 1 1, LENGTH_STALL | L=9 1 1 1, NEEDS_MORE_TIME | без изменений vs baseline |
| 15000 | L=6 5 1 1 | L=6 5 1 1 | L=9 1 1 1 | без изменений |
| 20000 | L=6 5 1 1 | L=6 5 1 1 | L=9 1 1 1 | без изменений @ TRAIN_T=80 |

**Вывод GTS:** при фиксированном TRAIN_T=80 смена GTS **не сдвигает** L_actual — узкое место TIME_BUDGET, не settle. **Рекомендация:** GTS=20000 (AsymRmSettle parity) + **adaptive TRAIN_T** 80→640.

## Dissoc×Secr sweep @ GTS=20000 (TRAIN_T=80)

| Dissoc | Secr | span25 gen | span25 preinh | span100 preinh |
|--------|------|------------|---------------|----------------|
| 0.0005 | 0.0005 | 6 5 1 1 | 6 5 1 1 | 9 1 1 1 |
| 0.001 | 0.001 | 6 5 1 1 | 6 5 1 1 | 9 1 1 1 |
| 0.002 | 0.002 | 6 5 1 1 | 6 5 1 1 | 9 1 1 1 |

**Вывод:** при TRAIN_T=80 timing params не меняют stall-класс. Dissoc/Secr=0.001 остаётся locked.

## Рекомендуемые defaults (после sweep)

- **GTS:** 20000
- **Dissoc/Secr:** 0.001
- **TRAIN_T:** старт 80, **adaptive continue** 160→320→640 при TIME_BUDGET/LENGTH_STALL
- **AutoCalibrate:** обязателен (`patch_ltz_calibrate_train.py`)

## Команды диагностики

```bash
python3 scripts/analyze_train_stall.py --meta grid_cells.tsv --grid . -o stall_summary.csv
python3 scripts/check_timing_feasibility.py --post --meta grid_cells.tsv --grid . -o timing_feasibility.csv
```

# C++ fallback (фаза E) — не требуется

**Verdict:** `INFEASIBLE_NOT_REACHED`

## Обоснование

1. **LtzCal Done** (`EXP_span25ms_packA_gen`): `IsNeedToTrain=0`, `FixedLTZ≈0.0885`, L=`6 5 4 1`, все non-ref `sync_ok` — `EndOfLearning` достижим без C++ diff.
2. **Peak-sync audit:** `PEAK_PREFERS_L_ACTUAL` — L_actual=6 5 4 1 корректнее formula L_target=6 5 3 1.
3. Pilot stall — **протокольный** (partial length-sync + amp@Rmin до all sync_ok), не несовместимость cable/EstDelayPerSeg.

## Условия для повторного рассмотрения C++

- 3-phase протокол + amp sweep исчерпаны
- `all_sync_ok` достижим, но `AllSynapsesNormalized` невозможен при TipR∈[Rmin,Rmax]
- Доказательство traces: `ResistanceStatus=1` бесконечно при length_ok

## Кандидаты (если понадобится)

- Export `EstDelayPerSeg` в Parameters
- `kMaxLengthStep` 4 для span25
- Ослабление `kNoImproveResistanceLimit` (только с evidence)

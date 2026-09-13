# Recipe coverage — TipR@Rmin + C1e9 + silent mid-thr

Рецепт = `TipSynapseResistance` TipR@Rmin `2e7 2e7 2e7 8.6e7` + `ResistanceMin=2e7` + silent mid-thr + clean Test.  
Для short-span дополнительно **C1e9** neuron + cold Train (Test-only tiprmin на Branch short-span — FAIL).

Критерии кода не меняются — [`SUCCESSFUL_EXPERIMENTS.md`](SUCCESSFUL_EXPERIMENTS.md) §«Слои ворот».

## Covered

| Семья | Конфиги | Журнал |
|-------|---------|--------|
| AsymRm A gen+preinh, B/C gen @25/50/100 | `SelectivityAsymRm/EXP_span{25,50,100}ms_pack{A,B,C}_gen` (+ A_preinh) | [`PHASE5_SPAN50_100.md`](SelectivityAsymRm/PHASE5_SPAN50_100.md) |
| AsymRmLtzCal twin gen @25/50/100 | `SelectivityLtzCalibrate/AsymRmLtzCal/EXP_span*_packA_gen` | PHASE5 Wave1 |
| Branch @480 tiprmin / nextseginh | `SelectivityBranch/EXP_br480_tiprmin`, `…_nextseginh_tiprmin` | [`PHASE7_BRANCH_QUALITY.md`](SelectivityBranch/PHASE7_BRANCH_QUALITY.md) |
| **Branch short-span packA gen+preinh** @25/50/100 | `SelectivityBranch/EXP_br_span{25,50,100}_packA_{gen,preinh}_C1e9` | [`PHASE8_SHORTSPAN.md`](SelectivityBranch/PHASE8_SHORTSPAN.md) (span100 gen: Done TipR fallback) |

## Partial

| Семья | Acc | Конфиг | Пробел |
|-------|-----|--------|--------|
| Phase6 TimeLearner @480 | 7/8 | `SelectivityPhaseA/Phase6/EXP_480_*` | foil trial6; pack B/C deferred — [`PHASE6_480_RECIPE.md`](SelectivityPhaseA/PHASE6_480_RECIPE.md) |
| Branch preinh250 tiprmin | 7/8 | `SelectivityBranch/EXP_br480_preinh250_tiprmin` | 1 FP (trial4) |

## Gap (не покрыто новым подбором)

| Семья | Пути | Почему | Действие |
|-------|------|--------|----------|
| **Branch short-span pack B/C** | — | deferred S4 | follow-up |
| AsymRmLtzCalBranch ×6 | `SelectivityLtzCalibrate/AsymRmLtzCalBranch/EXP_*` | NeedTrain=1, C25e12 stall | Не overwrite; PHASE8 packA = замена |
| AsymRm **preinh B/C** | `SelectivityAsymRm/EXP_span*_pack{B,C}_preinh` | PHASE5 deferred | Только эта строка; **вне PHASE8** (отдельная волна) |
| AsymRmLtzCal preinh twins | `AsymRmLtzCal/EXP_*_preinh` | silent / n≠8 | Вне PHASE8 |
| PSI mid-k / short | `SelectivityPresynapticInhib/EXP0*`, EXP20–27 | нет tiprmin-кампании | Orphan docs only |
| FastSpan / FastResponse | `SelectivityFastSpan/*`, `SelectivityFastResponse/*` | до-PHASE5 FAIL | Orphan |
| PhaseA EXP03–05 | `SelectivityPhaseA/EXP03_*`… | fail / n≠8 | Orphan |
| Branch канон trio | `TimeNeuronTimeLearnerBranch*` | demoted эталон | Не cold-reset |

## Вне scope текущих волн

- Tiprmin-кампания AsymRm preinh B/C (только эта карта).
- Полный retrain PSI / FastResponse / PhaseA EXP03–05.
- NextSegInh на short-span (follow-up после PHASE8 gen PASS).
- `UProperty EstDelayPerSeg` для Branch (отдельный PulseLib PR).

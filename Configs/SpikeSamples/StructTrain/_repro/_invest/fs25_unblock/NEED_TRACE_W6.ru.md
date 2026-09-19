# FS25 Need-trace Wave6 (W6.1) — RU

**EN:** [`NEED_TRACE_W6.md`](NEED_TRACE_W6.md)

Pin: `780ffc7`. Gold: L=`6 5 4 1` Need=0 thr≈0.0328372.  
W3a soft-cold: L→`6 5 4 1` Need=1 после 180×3; TipR остался cold.

## Путь в коде (classic `NNeuronTimeLearner.cpp`)

`EndOfLearning` (~3471) сбрасывает Need только если:

1. `AllDendritesSynced()` (~3334) — PeakValid + |DendLastAbsDt|≤SyncTol (или best_effort / dead_tip)
2. `AllSynapsesNormalized()` (~3372) — parametric: `|InitialSomaPotential[i]−MaxIterSomaAmp[i]| ≤ kAmpNormEps` (1e-5)  
   escapes: at_r_min+dt_positive, dead_tip+peak_attempted, oscillation_ok, no_improve_done

## Решение W6.1

**Pin PulseLib в Wave6 не меняли.**

Причины:
1. Runtime-дамп amp/synced требует debug-сборки + soft-cold wall ≥30–60 мин до EndOfLearning при L≡gold.
2. Нескоупленный `kAmpNormEps` / Need clear рискует thr AsymRm25 + Phase6 TimeLearner (blast-radius, W5).
3. Кандидаты патчей — в [`QUALITY_BACKLOG_PROPOSALS.ru.md`](../../../QUALITY_BACKLOG_PROPOSALS.ru.md) §A (предпочтителен FS-only guard).

**Статус:** оставить `FAIL_ROOTCAUSE`. Siblings — `ARTIFACT_KEEP` (W6.2).

## Предлагаемый C++ (не применён)

| ID | Изменение | Scope |
|----|-----------|-------|
| A | Лог once/N: synced, normalized, |ampDt|, ResistanceStatus | EnableDebug |
| B | Plateau Need clear: synced && L неизменен M эпох && max|ampDt|<2e-5 | classic only + FS guard |
| C | Guard по классу нейрона / EstDelay для B | мин. blast-radius |

Регресс перед merge: Branch25 packA gen EXACT/QUALITY; AsymRm25 packA gen acc≥7; FS25 Need=0+acc≥7.

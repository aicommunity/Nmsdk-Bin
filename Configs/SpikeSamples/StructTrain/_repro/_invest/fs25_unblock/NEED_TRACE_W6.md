# FS25 Need-trace Wave6 (W6.1)

> **RU:** [`NEED_TRACE_W6.ru.md`](NEED_TRACE_W6.ru.md)

Pin: `780ffc7`. Gold: L=`6 5 4 1` Need=0 thr≈0.0328372.
W3a soft-cold: L→`6 5 4 1` Need=1 after 180×3; TipR stayed cold.

## Code path (classic `NNeuronTimeLearner.cpp`)

`EndOfLearning` (~3471) clears Need only when:

1. `AllDendritesSynced()` (~3334) — PeakValid + |DendLastAbsDt|≤SyncTol (or best_effort / dead_tip)
2. `AllSynapsesNormalized()` (~3372) — parametric path: `|InitialSomaPotential[i]-MaxIterSomaAmp[i]| ≤ kAmpNormEps` (1e-5)
   - escapes: at_r_min+dt_positive, dead_tip+peak_attempted, oscillation_ok, no_improve_done

## W6.1 decision

**No PulseLib pin change in Wave6 execution window.**

Reasons:
1. Runtime amp/synced dump requires debug rebuild + soft-cold wall ≥30–60 min before EndOfLearning is even reachable at L≡gold.
2. Unscoped change to `kAmpNormEps` / Need clear risks AsymRm25 + Phase6 TimeLearner VALIDATED/registry thr (blast-radius documented W5).
3. Candidate patches deferred to `QUALITY_BACKLOG_PROPOSALS.md` §A with risk table (FS-only guard preferred).

**Status:** keep `FAIL_ROOTCAUSE`. Siblings stay `ARTIFACT_KEEP` (W6.2).

## Proposed C++ (for backlog doc — not applied)

| ID | Change | Scope |
|----|--------|-------|
| A | Log once/N: synced, normalized, per-dend |ampDt|, ResistanceStatus | EnableDebug |
| B | Plateau Need clear: synced && L unchanged M epochs && max|ampDt|<2e-5 | classic only |
| C | Neuron class / EstDelay FastSpan guard for B | min blast-radius |

Regress required before merge: Branch25 packA gen EXACT/QUALITY; AsymRm25 packA gen acc≥7; FS25 Need=0+acc≥7.

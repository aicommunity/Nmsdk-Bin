# FS25 Need-trace (W5.3)

> **RU:** [`NEED_TRACE.ru.md`](NEED_TRACE.ru.md)

## Evidence (W3a + REPRO_COLD)

| Fact | Value |
|------|-------|
| Gold L / Need | `6 5 4 1` / 0 |
| Soft r1 after 180×3 | L=`6 5 4 1` / **Need=1** |
| TipR on fail | stayed cold `86e6×4` (hygiene never ran) |
| PulseLib pin | `780ffc7` |
| Soft ≡ strip | Need stuck in both (REPRO_COLD_INVESTIGATION) |

## Code look-fors (`NNeuronTimeLearner.cpp`)

- `EndOfLearning` (~3471): requires `AllDendritesSynced() && AllSynapsesNormalized()` then `SetIsNeedToTrain(false)`.
- `AllSynapsesNormalized` (~3372): `kAmpNormEps=1e-5` — amp stall below eps blocks Need clear.
- dend0 `peak_synced` L-hold/grow (~3048–3159): soft often prefers L=`7 5 4 1` vs gold `6 5 4 1`.

## W5.3 decision

**No PulseLib patch** this wave: scoped Need/L-policy change on classic TL has blast-radius on AsymRm25 + Phase6 TimeLearner family; regress would require soft-cold Branch25 + AsymRm25 (hours) with high risk of thrifting VALIDATED golds.

**Close:** keep `FAIL_ROOTCAUSE` on FS25 (already §8-terminal). Siblings `BLOCKED_FS` → `ARTIFACT_KEEP` notes=`parent FAIL_ROOTCAUSE closed; no C++ patch W5`.

Re-open only with explicit approve + Need debug build + FS-only guard.

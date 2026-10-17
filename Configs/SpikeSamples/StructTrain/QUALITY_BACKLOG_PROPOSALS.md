# PHASE12 Quality backlog — proposals after Wave6

> **Русская версия (основная для чтения):** [`QUALITY_BACKLOG_PROPOSALS.ru.md`](QUALITY_BACKLOG_PROPOSALS.ru.md)

**Date:** 2026-09-19 · PulseLib pin **`780ffc7`** (unchanged) · SoT: [`PHASE12_VALIDATION.md`](PHASE12_VALIDATION.md)

Wave6 exhausted soft/strip/overlay invests for quality tails left as `ARTIFACT_KEEP` / `FAIL_ROOTCAUSE` after §8 Wave5. This document lists **concrete repair proposals** (config / scripts / **C++**) and **risk analysis** vs already VALIDATED gold (Branch W1–W2, AsymRm25, LtzCal25).

**Do not:** marathon br480/nextseg; overwrite VALIDATED gold; unscoped `kAmpNormEps` / TipR path without regress.

---

## Coverage checklist (31 IDs)

| Verdict | Count | Notes |
|---------|-------|-------|
| `CLOSED_VALIDATED` | 0 in W6 | No new VALIDATED* this wave |
| `EXHAUSTED_KEEP` | 31 | All quality backlog below |

---

## A. FastSpan Need stuck — FS25 + siblings×4

### IDs
- `SelectivityFastSpan/EXP_span25ms_fast_C1e9` — **FAIL_ROOTCAUSE**
- `EXP_span25ms_fast_preinh_C1e9`, `EXP_span50ms_fast_preinh_C1e9`, `EXP_span100ms_fast_C1e9`, `EXP_span100ms_fast_preinh_C1e9` — **ARTIFACT_KEEP** (`SKIPPED_WITH_REASON`: parent)

### Wave6 facts
- Code analysis: `_repro/_invest/fs25_unblock/NEED_TRACE_W6.md`
- W3a: soft-cold L≡gold `6 5 4 1`, Need=1 @180×3
- **No PulseLib pin change** (blast-radius; full regress Branch25+AsymRm25 not run)

### Root hypothesis
`EndOfLearning` blocked by `AllSynapsesNormalized()` amp stall (`kAmpNormEps=1e-5`) and/or dend0 `peak_synced` L-policy, while length vector already matches gold.

### Proposals
1. **Config/protocol:** soft-cold with `EnableDebug=1` on FS25 Train; capture logger ampDt/synced dumps to `_repro/_invest/fs25_unblock/`.
2. **Scripts:** one-shot `run-fs --exp …` after pin bump; auto-regress hook Branch25+AsymRm25.
3. **C++** ([`NNeuronTimeLearner.cpp`](../../../../Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearner.cpp)):
   - **A1 (P0):** In `EndOfLearning` (~3471), when `EnableDebug`, log `AllDendritesSynced`, `AllSynapsesNormalized`, per-dend `|Initial-MaxAmp|`, `ResistanceStatus`.
   - **A2 (P0):** Plateau Need-clear: if `AllDendritesSynced()` and L unchanged for M epochs and `max_i|ampDt|<2e-5`, call `SetIsNeedToTrain(false)` — **guard** with FastSpan / EstDelay / neuron-class flag (not global).
   - **A3 (P1):** Do **not** raise global `kAmpNormEps` without AsymRm25 thr regress.
   - **A4 (P2):** dend0 hold-L tweak in `ChangeDendriteStatus` (~3121) only if logs show 7↔6 thrashing.

### Risk vs VALIDATED*

| Change | Hits | Detect | Mitigate |
|--------|------|--------|----------|
| Global Need clear / eps | AsymRm25, Phase6 TL family | soft-cold AsymRm25 acc/thr | FS-only guard |
| dend0 L-policy | AsymRm25 L vector | compare L to gold | `num==0 && EstDelay` scope |
| Branch.cpp | Branch W1–W2 EXACT | stamp Branch25 | **do not patch Branch** for FS |

**Priority:** P0 · Effort: PulseLib+regress (~½–1 day wall)

---

## B. AsymRm span50/100 midflat + clones + LtzCal50/100

### IDs
- AsymRm packA 50/100 gen+preinh ×4 — **ARTIFACT_KEEP**
- AsymRm B/C ×8 — **ARTIFACT_KEEP** (parent)
- LtzCal 50/100 ×4 — **ARTIFACT_KEEP** (parent)

### Wave6 facts
- Soft Need=0 L≡gold; ltz≈0.0379 flat (W3 tiprmin+86e6)
- **W6.3 overlay** tiprmin on soft weights (no retrain): still flat — `_repro/_invest/asym_midflat/ROOTCAUSE.md`
- `soma_amp_sum`=0 on gold and soft

### Root hypothesis
Soft-cold produces wrong amp/weight hierarchy for span≥50; TipR recipe insufficient. Span25 TipR86e6 VALIDATED — span-dependent InitSoma / TipR settle / ampDt.

### Proposals
1. **Config:** Diff gold vs soft Train InitSoma, tip Exc, Pattern scale, MatrixData → `_repro/_invest/asym_midflat/diff_params.md`; try warm TipR schedule during train (not only post).
2. **Scripts:** optional post-train InitSoma overlay from gold before phase9 (QUALITY path).
3. **C++:**
   - **B1 (P1):** TipR path (~686+) — ensure ampDt settle does not flatten LTZ peaks for longer spans; log TipR ampDt per dend.
   - **B2 (P1):** After soft-cold Done, optional re-init tip Exc from gold recipe under feature flag.
   - **B3 (P2):** Do not switch gate to `soma_amp_sum` (always 0 here).

### Risk vs VALIDATED*

| Change | Hits | Detect | Mitigate |
|--------|------|--------|----------|
| TipR ampDt | AsymRm25 TipR86e6 mid | phase9 acc=8 | span≥50-only / flag |
| InitSoma overlay protocol | AsymRm25 EXACT thr | thr drift | QUALITY allowlist only |

**Priority:** P1 · Effort: invest+protocol day; C+++regress 1–2 days

---

## C. Phase6 @480 — L stuck soft+strip

### IDs
`SelectivityPhaseA/Phase6/EXP_480_{gen_tiprmin,gen_thr_only,preinh250_tiprmin,ltzcal_twin_gen}` — **ARTIFACT_KEEP**

### Wave6 facts
- AutoCal inject OK (=0), Reset=1
- Soft+strip probe `-t`120, wall≤320s: L stayed `1 1 1 1` Need=1 — `_repro/_invest/phase6_w6/COMPARE.md`
- Matches W5.1 abort

### Root hypothesis
Classic TimeLearner never enters length-growth for 480ms pattern under soft/strip cold (dataset/Reset/GTS/learner mode), not TipR.

### Proposals
1. **Config:** Compare gold vs cold Pattern/GTS/CalculateMode/TrainingPhase; try gold warm-start (copy gold L TipR then Reset=0 probe — diagnostic only).
2. **Scripts:** assert `EnableNextSegmentInhibition` N/A; dump first-impulse DetectNewImpulse in debug.
3. **C++ (classic TL):**
   - **C1 (P1):** Same EnableDebug EndOfLearning / ChangeDendriteStatus logs as A1 during Phase6.
   - **C2 (P1):** If `DetectNewImpulseCount()==0` for N seconds while Need=1, log generator/link failure (config more likely than C++).
   - **C3 (P2):** Shared with FS Need-clear only if impulse path proven OK.

### Risk vs VALIDATED*
Same classic TL table as §A — Phase6 shares neuron family with FS/AsymRm. Prefer diagnostics before any Need-clear.

**Priority:** P1 · Effort: config forensics ½ day; C++ only after impulse proven

---

## D. Branch nextseg100 packA+B/C

### IDs
- `EXP_br_span100_packA_nextseginh_C1e9` — **ARTIFACT_KEEP**
- packB/C — **ARTIFACT_KEEP** (parent)

### Wave6 facts
- Soft+strip `-t`200, wall≤180s: L=`1 1 1 1` — `_repro/_invest/nextseg100/COMPARE.md`
- Tag present: `EnableNextSegmentInhibition=1` (W1 FAIL history)

### Root hypothesis
NextSegInh @span100 blocks length growth under cold reset (Branch short nextseg25/50 VALIDATED). Possibly Branch-specific L-policy / pattern coupling.

### Proposals
1. **Config:** soft `-t`640 with train-extend (one controlled attempt); compare MatrixData to nextseg50 VALIDATED; toggle NextSeg 1→0 diagnostic clone (not promote).
2. **Scripts:** assert `EnableNextSegmentInhibition` in prepare; full phase8 only after Need=0.
3. **C++** ([`NNeuronTimeLearnerBranch.cpp`](../../../../Libraries/Nmsdk-PulseLib/Core/NNeuronTimeLearnerBranch.cpp)) — **only after config exhaust**:
   - **D1 (P1):** Log NextSeg interaction with `ChangeDendriteStatus` / length grow when EnableNextSegmentInhibition.
   - **D2 (P2):** Scoped exception for span≥100 NextSeg cold start — high risk to Branch VALIDATED.

### Risk vs VALIDATED*

| Change | Hits | Detect | Mitigate |
|--------|------|--------|----------|
| Branch.cpp L-policy | Branch25/50 EXACT | soft-cold Branch25 gen+nextseg25 | never ship without Branch25+nextseg50 regress |
| NextSeg disable | product semantics | manual | diagnostic only |

**Priority:** P1 config / P2 C++ · Effort: 1 day config; C+++regress 1–2 days

---

## E. Branch br480 ×3

### IDs
`EXP_br480_{tiprmin,nextseginh_tiprmin,preinh250_tiprmin}` — **ARTIFACT_KEEP**

### Wave6 facts
- Soft+strip pilot tiprmin `-t`180: L stuck — `_repro/_invest/br480_w6/COMPARE.md`
- W2: Need≠0 @4×600; gold 7/8 registry kept

### Root hypothesis
Same class as Phase6/nextseg: cold L never leaves `1 1 1 1` at 480ms Branch (short Branch VALIDATED). Not TipR@Rmin primary.

### Proposals
1. **Config:** done_tipr keep + phase8 mid-only stamp from gold (QUALITY documentation path — not false VALIDATED cold).
2. **Scripts:** `run-br480` max_extensions=0 for probes; forbid 4×600 in CLI guard.
3. **C++ Branch:** same D1 diagnostics; **E1 (P2):** Epoch/GTS scaling for long patterns — only with Branch25 regress.

### Risk vs VALIDATED*
Branch.cpp changes hit all Branch VALIDATED*. Prefer leave ARTIFACT_KEEP + gold registry unless product requires cold @480.

**Priority:** P2 · Effort: docs/stamp path ½ day; C++ expensive

---

## Cross-cutting recommendations (Wave7)

| P | Item | Why |
|---|------|-----|
| P0 | FS25 EnableDebug EndOfLearning dump + FS-only Need plateau clear | Unblocks FS family; AsymRm25/LtzCal25 already VAL |
| P1 | AsymRm50 midflat InitSoma/TipR train-schedule protocol | Overlay proved TipR post-hoc insufficient |
| P1 | Phase6 / nextseg / br480 impulse+NextSeg config forensics | L never grows — likely before TL amp policy |
| P2 | Branch.cpp NextSeg@100 / br480 | High blast-radius on W1–W2 EXACT |

### Mandatory regress set before any PulseLib pin bump
1. `EXP_br_span25_packA_gen_C1e9` soft-cold or stamp EXACT/QUALITY  
2. `SelectivityAsymRm/EXP_span25ms_packA_gen` phase9 acc≥7  
3. Target EXP Need=0 + gate acc≥7  

Pin note in PHASE12 + Bin commit; StatisticLog never in git; 1 NM.

---

## History pointers
- W1–W5: [`PHASE12_VALIDATION.md`](PHASE12_VALIDATION.md) Wave map + run logs  
- FS: `_repro/_invest/fs25_unblock/`, `REPRO_COLD_INVESTIGATION.md`  
- AsymRm: `_repro/_invest/asym_midflat/`  
- Phase6: `_repro/_invest/phase6_w6/`, `_repro/_invest/phase6_w5/`  
- nextseg / br480: `_repro/_invest/nextseg100/`, `_repro/_invest/br480_w6/`

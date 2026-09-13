# PHASE8 — Branch short-span C1e9 @25/50/100

Cold Train `NNeuronTimeLearnerBranch` на сжатых спанах (pack A gen + preinh) с рецептом PHASE5/7: C1e9 + TipR@Rmin + mid thr по **`soma_amp_sum`**.

Критерии кода **не** меняем — [`../SUCCESSFUL_EXPERIMENTS.md`](../SUCCESSFUL_EXPERIMENTS.md) §«Слои ворот».  
Процедурная цель: **8/8** selective + last-pulse (`t_rel ≥ 0.8·pattern_end`) + `ok_single`.

Предшественники: [`PHASE7_BRANCH_QUALITY.md`](PHASE7_BRANCH_QUALITY.md) Wave4 FAIL (`EXP_br_span25_tiprmin` Test-only tiprmin), [`../SelectivityAsymRm/PHASE5_SPAN50_100.md`](../SelectivityAsymRm/PHASE5_SPAN50_100.md), [`../RECIPE_COVERAGE.md`](../RECIPE_COVERAGE.md).

## Принципы

- Новые клоны под `SelectivityBranch/EXP_br_span*_packA_*_C1e9` — **не** cold-reset канона Branch / PHASE7 PASS / AsymRm PHASE5.
- Branch: один дендрит; tip `Dendrite1_{L[i]}`; silent thr ≈ **1.0**; mid из `soma_amp_sum` (не `ltz_potential_max`).
- `EstDelayPerSeg` у Branch **не** XML (runtime default 0.005) — не копировать AsymRm L-bands как seed Done.
- GTS=**20000**; neuron C1e9 (не BranchFastSpan C25e11 / LtzCalBranch C25e12).
- Конфиги не удаляем; FAIL оставляем со ссылками.

## Матрица EXP

| EXP | Span | kind | Status |
|-----|------|------|--------|
| [`EXP_br_span25_packA_gen_C1e9`](EXP_br_span25_packA_gen_C1e9/) | 25 | gen | **PASS** S1 — L=`13 11 7 1`, TipR@Rmin, mid≈0.0718, fires `10000000` |
| [`EXP_br_span25_packA_preinh_C1e9`](EXP_br_span25_packA_preinh_C1e9/) | 25 | preinh | **PASS** S3 — L=`7 6 4 1`, TipR@Rmin, mid≈0.0517 |
| [`EXP_br_span50_packA_gen_C1e9`](EXP_br_span50_packA_gen_C1e9/) | 50 | gen | **PASS** S2 — L=`13 11 6 1`, TipR@Rmin, mid≈0.0644, fires `10000000` |
| [`EXP_br_span50_packA_preinh_C1e9`](EXP_br_span50_packA_preinh_C1e9/) | 50 | preinh | **PASS** S3 — L=`13 11 6 1`, TipR@Rmin, mid≈0.0301 |
| [`EXP_br_span100_packA_gen_C1e9`](EXP_br_span100_packA_gen_C1e9/) | 100 | gen | **PASS** S2 — L=`25 21 11 1`, **Done TipR** (Rmin foil>target), mid≈0.00718, fires `10000000` |
| [`EXP_br_span100_packA_preinh_C1e9`](EXP_br_span100_packA_preinh_C1e9/) | 100 | preinh | **PASS** S3 — L=`22 18 11 1`, TipR@Rmin, mid≈0.0203 |

## S1 notes (span25 gen)

- Train: `NeedTrain=0`, L=`13 11 7 1` (не ждать Ideal TipR / amp-Done).
- Test hygiene: **overlay Train `<Neuron>`** в Test (шаблон Branch держит tips `85/46/25/1`); Generator → `Dendrite1_{13,11,7,1}`; TipR@Rmin property + tip Exc R; Parameters Matrix/Classes из AsymRm packA @25; Model DatasetMatrix 1-sample; Learner SB Params=`0` / Model=`1`, Neuron SB=`2`.
- Mid из `soma_amp_sum` при silent thr=1.0; gap мал (~1.2e-4) но mid режет foils.
- Helper: [`scripts/phase8_tiprmin_gate.py`](scripts/phase8_tiprmin_gate.py).

## S2 notes (span50/100 gen)

- span50: тот же TipR@Rmin рецепт; L=`13 11 6 1`; mid≈0.0644.
- span100: TipR@Rmin → soma foil trial6 > target (7/8 FP). **Done TipR** + mid → 8/8. Зафиксировать fallback в helper/README.
- Learner SB на Model: первый `StructureBuildMode` **до** `<Neuron>` =`1` (тег `NNeuronTimeLearnerBranch` в Model часто отсутствует).

## S3 notes (preinh A)

- Cold Train `NSPNeuronGenPreinh2_5AsymRmD001C1e9` @25/50/100; per-exp mid thr.
- Все три **PASS** TipR@Rmin + mid (`ok_audit=1`, fires `10000000`).
- span25 preinh: после extend Need=0, L=`7 6 4 1` (короче первого band `16 13 3 1`).

## S4 notes (pack B/C)

- **Deferred**: pack B/C short-span Branch не клонировались в этой волне (фокус — packA gen+preinh). Строка в SUCCESSFUL §Отложено / RECIPE_COVERAGE.

## Waves

| Wave | Content |
|------|---------|
| S0 | Scaffold 6 EXP: C1e9 neuron, InputPattern, GTS=20000, cold TipR/Rmin, L=`1 1 1 1`, Test hygiene |
| S1 | Train + TipR@Rmin + mid-thr gate span25 gen |
| S2 | span50 / span100 packA gen |
| S3 | preinh A @25/50/100 (отдельный cold; per-exp mid) |
| S4 | pack B/C clone **или** explicit defer; SUCCESSFUL / RECIPE_COVERAGE |

## Seed (Train cold)

| Поле | Значение |
|------|----------|
| Class | `NNeuronTimeLearnerBranch` |
| Neuron gen | `NSPNeuronGenAsymRmD001C1e9` |
| Neuron preinh | `NSPNeuronGenPreinh2_5AsymRmD001C1e9` |
| `IsNeedToTrain` | `1` |
| `DendriteLength` | `1 1 1 1` |
| TipR (cold) | `8.6e7×4` |
| `ResistanceMin` | `2e7` |
| GTS | `20000` |
| TipR@Rmin (post) | `2e7 2e7 2e7 8.6e7` |

## Антирегрессия

- Не cold-reset: `TimeNeuronTimeLearnerBranch*`, `EXP_br480_tiprmin`, AsymRm PHASE5 PASS, `AsymRmLtzCalBranch/**`.
- Не считать Test-only tiprmin решениемшением short-span (уже FAIL: `EXP_br_span25_tiprmin`).
- Pack B/C / NextSegInh short-span — только после gen A PASS или defer.

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
| [`EXP_br_span25_packA_gen_C1e9`](EXP_br_span25_packA_gen_C1e9/) | 25 | gen | scaffolded (S0) |
| [`EXP_br_span25_packA_preinh_C1e9`](EXP_br_span25_packA_preinh_C1e9/) | 25 | preinh | scaffolded (S0) |
| [`EXP_br_span50_packA_gen_C1e9`](EXP_br_span50_packA_gen_C1e9/) | 50 | gen | scaffolded (S0) |
| [`EXP_br_span50_packA_preinh_C1e9`](EXP_br_span50_packA_preinh_C1e9/) | 50 | preinh | scaffolded (S0) |
| [`EXP_br_span100_packA_gen_C1e9`](EXP_br_span100_packA_gen_C1e9/) | 100 | gen | scaffolded (S0) |
| [`EXP_br_span100_packA_preinh_C1e9`](EXP_br_span100_packA_preinh_C1e9/) | 100 | preinh | scaffolded (S0) |

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

# FS25 Need-trace (W5.3) — RU

**EN:** [`NEED_TRACE.md`](NEED_TRACE.md)

## Evidence (W3a + REPRO_COLD)

| Факт | Значение |
|------|----------|
| Gold L / Need | `6 5 4 1` / 0 |
| Soft r1 после 180×3 | L=`6 5 4 1` / **Need=1** |
| TipR при fail | остался cold `86e6×4` (hygiene не вызывалась) |
| PulseLib pin | `780ffc7` |
| Soft ≡ strip | Need stuck в обоих (REPRO_COLD_INVESTIGATION) |

## Куда смотреть в коде (`NNeuronTimeLearner.cpp`)

- `EndOfLearning` (~3471): нужны `AllDendritesSynced() && AllSynapsesNormalized()`, затем `SetIsNeedToTrain(false)`.
- `AllSynapsesNormalized` / `kAmpNormEps=1e-5` — amp stall блокирует clear Need.
- dend0 `peak_synced` hold/grow L (~3048–3159).

## Решение W5.3 / W6

Без патча PulseLib в этих волнах (blast-radius). Статус `FAIL_ROOTCAUSE`. Предложения: [`QUALITY_BACKLOG_PROPOSALS.ru.md`](../../../QUALITY_BACKLOG_PROPOSALS.ru.md) §A; детали W6: [`NEED_TRACE_W6.ru.md`](NEED_TRACE_W6.ru.md).

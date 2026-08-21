# SynapseBioTcSweep — REPORT R1

Одиночный `NPSynapseBio`, `GlobalTimeStep=2000`, SecretionTC=0.001, pulse 1 мс @ Delay=0.05, Frequency=2 Hz, SIM_T=3 с.

## Метрики (первый пик)

| cell | Dissoc | steps/τ | FWHM (мс) | t_tail10 (мс) | peak (Output) | gate FWHM≤2.1 мс |
|------|--------|---------|-----------|---------------|---------------|------------------|
| D005 | 0.005 | 10 | **4.5** | 11.0 | ~8.7e-9 | FAIL |
| D002 | 0.002 | 4 | **2.5** | 4.5 | ~8.7e-9 | FAIL |
| D001 | 0.001 | 2 | **2.0** | 2.0 | ~8.7e-9 | **PASS** (на грани steps) |
| D0005 | 0.0005 | 1 | **1.5** | 0.5 | ~8.7e-9 | PASS FWHM / **FAIL steps** (VDissoc=1) |

Тренд: меньше DissociationTC → уже FWHM. Bio 5 мс **не** совместим с ISI(25 мс)≈4.2 мс.

## Рекомендация

Рабочий ориентир синапса: **DissociationTC = 0.001 с** (1 мс). D=0.0005 не использовать при TimeStep=2000.

R2 не требуется для FWHM-gate; опционально `D001_ts10k` при нестабильности на TipEps.

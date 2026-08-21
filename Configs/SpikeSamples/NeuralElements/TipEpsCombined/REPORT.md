# TipEpsCombined — REPORT R1

Два режима: (1) dual-pulse на `NPSynapseBio`; (2) канал (справочно).

## Synapse dual-pulse (Frequency=1/ISI, Delay=0.05)

Gate: sep ≥ 0.30 между соседними пиками Output.

| cell | D | ISI | sep | gate |
|------|---|-----|-----|------|
| D005_ISI100 | 0.005 | 16.7 мс | 0.96 | PASS |
| D005_ISI50 | 0.005 | 8.3 мс | 0.77 | PASS |
| D005_ISI25 | 0.005 | 4.2 мс | **0.47** | PASS (на грани) |
| D002_ISI25 | 0.002 | 4.2 мс | 0.82 | PASS |
| D001_ISI25 | 0.001 | 4.2 мс | **0.98** | PASS |

На уровне **синапса** Bio D=5 мс ещё проходит ISI25, но с малым запасом. D=0.001–0.002 дают комфортный sep.

## Channel dual-pulse

Standalone `NPExcChannelBio` без мембраны-owner: доминирует релаксация −1→0; детект sep по детренду ненадёжен. Опора на τ из ChannelRcSweep: C≤2.5e-10.

## Рабочая пара для StructTrain

**DissociationTC=0.002, Capacity=2.5e-10** → класс `NSPNeuronGenD002C25e11`  
(альтернатива D=0.001: `NSPNeuronGenD001C25e11`).

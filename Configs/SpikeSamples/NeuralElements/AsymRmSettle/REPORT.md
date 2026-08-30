# AsymRmSettle — REPORT

Exc-only: `NPGenerator` → `NPSynapseBio` → `NPExcChannelBio` (без Inh, gen нейрона off).  
Каталог: `Bin/Configs/SpikeSamples/NeuralElements/AsymRmSettle/`.

## Протокол

| Параметр | Значение |
|----------|----------|
| Dissoc / Secr | **0.001** |
| `FBResistance` = `Resistance` = Exc Rm | (standalone → ветка FB) |
| Метрика | τ / settle5% по decay после Reset (как ChannelRcSweep) |
| Gate ISI25 | settle5% **< 4.17 мс**, без осцилляции |
| `GlobalTimeStep` | **20000** (обязательно: при GTS=2000 и C≤2.5e-11 Ti·TS≲0.5 → ±1 осцилляция) |

## Сетка и результаты

| cell | C | Rm | Rsyn | τ_th (мс) | τ_fit | settle5% | ok25 |
|------|---|----|------|-----------|-------|----------|------|
| `A_C25e12_R1e7_S86e6` | 2.5e-11 | 1e7 | 8.6e7 | 0.25 | **0.25** | **0.70** | PASS |
| `B_C1e11_R1e7_S5e7` | 1e-11 | 1e7 | 5e7 | 0.10 | **0.10** | **0.25** | PASS |
| `sweep_C25e12_R5e6_S86e6` | 2.5e-11 | 5e6 | 8.6e7 | 0.125 | **0.10** | **0.30** | PASS |
| `C_C5e12_R5e6_S4e7` | 5e-12 | 5e6 | 4e7 | 0.025 | — | — | FAIL osc |
| `ctrl_C25e11_R1e7_S86e6` | 2.5e-10 | 1e7 | 8.6e7 | 2.5 | 2.5 | 7.45 | FAIL (>ISI25) |

## Locked Packs (StructTrain)

| Pack | C | ExcRm | ExcRsyn | InhRm (=10×) | InhRsyn (=10×) | Secr/Dissoc | UploadClass gen | UploadClass preinh |
|------|---|-------|---------|--------------|----------------|-------------|-----------------|-------------------|
| **A** | 2.5e-11 | 1e7 | 8.6e7 | 1e8 | 8.6e8 | 0.001 | `NSPNeuronGenAsymRmD001C25e12` | `NSPNeuronGenPreinh2_5AsymRmD001C25e12` |
| **B** | 1e-11 | 1e7 | 5e7 | 1e8 | 5e8 | 0.001 | `NSPNeuronGenAsymRmD001C1e11` | `NSPNeuronGenPreinh2_5AsymRmD001C1e11` |
| **C** | 2.5e-11 | 5e6 | 8.6e7 | 5e7 | 8.6e8 | 0.001 | `NSPNeuronGenAsymRmD001C25e12Rm5e6` | `NSPNeuronGenPreinh2_5AsymRmD001C25e12Rm5e6` |

Pack C = пониженный Exc Rm (не C=5e-12 — нестабилен при GTS=20000).

## Заметки

- EPSP dual-pulse на standalone-канале слабо виден в логе (как TipEps CH); опора на reset-decay τ.
- StructTrain AsymRm: **GlobalTimeStep=20000**.

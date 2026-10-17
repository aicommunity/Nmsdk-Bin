## EXP_span25ms_fast_preinh_ts10k — Test

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityFastSpan/EXP_span25ms_fast_preinh_ts10k/Test`

### Параметры

- **NeuronClassName:** `NSPNeuronGenPreinh2_5D002C25e11`
- **kind:** preinh_ts10k
- **span (target):** 25 ms
- **GlobalTimeStep:** 10000
- **Element defaults:** DissociationTC=0.002, MembraneCapacity=2.5e-10 (UseElementDefaults via UploadClass)
- **InputPattern (s):** `0.000520833, 0.00416667, 0.00833333, 0.0125`
- **Learner span:** 25.000 ms
- **FixedLTZThreshold:** 0.04

### Использование

```bash
NeuroModelerConsole -c Project.ini -s -t 160 -x -S   # Train
NeuroModelerConsole -c Project.ini -s -t 20 -x       # Test
```

Родитель: [`../../REPORT.md`](../../REPORT.md).

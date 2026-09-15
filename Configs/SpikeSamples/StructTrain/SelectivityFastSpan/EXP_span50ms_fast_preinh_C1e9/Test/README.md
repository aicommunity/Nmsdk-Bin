## EXP_span50ms_fast_preinh — Test

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityFastSpan/EXP_span50ms_fast_preinh/Test`

### Параметры

- **NeuronClassName:** `NSPNeuronGenPreinh2_5D002C25e11`
- **kind:** preinh
- **span (target):** 50 ms
- **GlobalTimeStep:** 2000
- **Element defaults:** DissociationTC=0.002, MembraneCapacity=2.5e-10 (UseElementDefaults via UploadClass)
- **InputPattern (s):** `0.00104167, 0.00833333, 0.0166667, 0.025`
- **Learner span:** 50.000 ms

### Использование

```bash
NeuroModelerConsole -c Project.ini -s -t 160 -x -S   # Train
NeuroModelerConsole -c Project.ini -s -t 20 -x       # Test
```

Родитель: [`../../REPORT.md`](../../REPORT.md).

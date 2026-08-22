## EXP_span25ms_fast_preinh — Train

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityFastSpan/EXP_span25ms_fast_preinh/Train`

### Параметры

- **NeuronClassName:** `NSPNeuronGenPreinh2_5D002C25e11`
- **kind:** preinh
- **span:** 25 мс
- **GlobalTimeStep:** 2000
- **Element defaults:** DissociationTC=0.002, MembraneCapacity=2.5e-10 (UseElementDefaults via UploadClass)

### Использование

```bash
NeuroModelerConsole -c Project.ini -s -t 160 -x -S   # Train
NeuroModelerConsole -c Project.ini -s -t 20 -x       # Test
```

Родитель: [`../../REPORT.md`](../../REPORT.md).

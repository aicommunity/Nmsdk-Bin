## EXP_span25ms_fast — Train

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityFastSpan/EXP_span25ms_fast/Train`

### Параметры

- **NeuronClassName:** `NSPNeuronGenD002C25e11`
- **kind:** fast
- **span:** 25 мс
- **GlobalTimeStep:** 2000
- **Element defaults:** DissociationTC=0.002, MembraneCapacity=2.5e-10 (UseElementDefaults via UploadClass)

### Использование

```bash
NeuroModelerConsole -c Project.ini -s -t 160 -x -S   # Train
NeuroModelerConsole -c Project.ini -s -t 20 -x       # Test
```

Родитель: [`../../REPORT.md`](../../REPORT.md).

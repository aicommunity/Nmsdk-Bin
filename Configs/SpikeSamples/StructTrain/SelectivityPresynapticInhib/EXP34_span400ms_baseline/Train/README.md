## EXP34_span400ms_baseline — Train

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP34_span400ms_baseline/Train`  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib (time-expand)

### Параметры

- **NeuronClassName:** `NSPNeuronGen`
- **span:** 400 мс (α=0.833333)
- **SyncTolerance / PeakMeasureMargin / DelayAgreeMarginMin:** 0.0166667 / 0.0233333 / 0.0233333

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP34_span400ms_baseline/Train/Project.ini -s -t 90 -x -S
```

Родитель: [`../README.md`](../README.md) · [`../../REPORT_time_expand.md`](../../REPORT_time_expand.md).

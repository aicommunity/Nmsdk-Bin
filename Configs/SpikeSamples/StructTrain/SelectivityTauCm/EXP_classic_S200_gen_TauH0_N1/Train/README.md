## EXP30_span200ms_baseline — Train

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP30_span200ms_baseline/Train`  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib (time-expand)

### Параметры

- **NeuronClassName:** `NSPNeuronGen`
- **span:** 200 мс (α=0.416667)
- **SyncTolerance / PeakMeasureMargin / DelayAgreeMarginMin:** 0.00833333 / 0.0116667 / 0.0116667

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP30_span200ms_baseline/Train/Project.ini -s -t 90 -x -S
```

Родитель: [`../README.md`](../README.md) · [`../../REPORT_time_expand.md`](../../REPORT_time_expand.md).

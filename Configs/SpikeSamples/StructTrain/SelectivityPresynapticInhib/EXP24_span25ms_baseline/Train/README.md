## EXP24_span25ms_baseline — Train

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP24_span25ms_baseline/Train`  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib (time-compress)

### Параметры

- **NeuronClassName:** `NSPNeuronGen`
- **span:** 25 мс (α=0.0520833)
- **SyncTolerance / PeakMeasureMargin / DelayAgreeMarginMin:** 0.0015 / 0.002 / 0.002

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP24_span25ms_baseline/Train/Project.ini -s -t 90 -x -S
```

Родитель: [`../README.md`](../README.md) · [`../../REPORT_time_compress.md`](../../REPORT_time_compress.md).

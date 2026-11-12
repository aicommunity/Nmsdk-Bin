## EXP25_span25ms_preinh250 — Train

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP25_span25ms_preinh250/Train`  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib (time-compress)

### Параметры

- **NeuronClassName:** `NSPNeuronGenPreinh2_5`
- **span:** 25 мс (α=0.0520833)
- **SyncTolerance / PeakMeasureMargin / DelayAgreeMarginMin:** 0.0015 / 0.002 / 0.002

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP25_span25ms_preinh250/Train/Project.ini -s -t 90 -x -S
```

Родитель: [`../README.md`](../README.md) · [`../../REPORT_time_compress.md`](../../REPORT_time_compress.md).

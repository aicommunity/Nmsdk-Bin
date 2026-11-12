## EXP23_span50ms_preinh250 — Train

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP23_span50ms_preinh250/Train`  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib (time-compress)

### Параметры

- **NeuronClassName:** `NSPNeuronGenPreinh2_5`
- **span:** 50 мс (α=0.104167)
- **SyncTolerance / PeakMeasureMargin / DelayAgreeMarginMin:** 0.00208333 / 0.00291667 / 0.00291667

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP23_span50ms_preinh250/Train/Project.ini -s -t 90 -x -S
```

Родитель: [`../README.md`](../README.md) · [`../../REPORT_time_compress.md`](../../REPORT_time_compress.md).

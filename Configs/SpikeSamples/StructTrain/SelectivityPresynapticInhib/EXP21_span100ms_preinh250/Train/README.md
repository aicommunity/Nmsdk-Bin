## EXP21_span100ms_preinh250 — Train

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Train`  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib (time-compress)

### Параметры

- **NeuronClassName:** `NSPNeuronGenPreinh2_5`
- **span:** 100 мс (α=0.208333)
- **SyncTolerance / PeakMeasureMargin / DelayAgreeMarginMin:** 0.00416667 / 0.00583333 / 0.00583333

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP21_span100ms_preinh250/Train/Project.ini -s -t 90 -x -S
```

Родитель: [`../README.md`](../README.md) · [`../../REPORT_time_compress.md`](../../REPORT_time_compress.md).

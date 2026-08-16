## EXP32_span300ms_baseline — Test

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test`  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib (time-expand)

### Параметры

- **NeuronClassName:** `NSPNeuronGen`
- **span:** 300 мс (α=0.625)
- **SyncTolerance / PeakMeasureMargin / DelayAgreeMarginMin:** 0.0125 / 0.0175 / 0.0175

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test/Project.ini -s -t 20 -x
```

Родитель: [`../README.md`](../README.md) · [`../../REPORT_time_expand.md`](../../REPORT_time_expand.md).

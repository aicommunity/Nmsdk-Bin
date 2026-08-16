## EXP33_span300ms_preinh250 — Train

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Train`  
**Статус:** экспериментальный конфиг SelectivityPresynapticInhib (time-expand)

### Параметры

- **NeuronClassName:** `NSPNeuronGenPreinh2_5`
- **span:** 300 мс (α=0.625)
- **SyncTolerance / PeakMeasureMargin / DelayAgreeMarginMin:** 0.0125 / 0.0175 / 0.0175

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP33_span300ms_preinh250/Train/Project.ini -s -t 90 -x -S
```

Родитель: [`../README.md`](../README.md) · [`../../REPORT_time_expand.md`](../../REPORT_time_expand.md).

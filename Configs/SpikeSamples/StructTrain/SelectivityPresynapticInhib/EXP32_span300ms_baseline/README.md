## EXP32_span300ms_baseline — PSI time-expand

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP32_span300ms_baseline`  
**Статус:** экспериментальный конфиг StructTrain / SelectivityPresynapticInhib

### Назначение

Расширенный паттерн first→last ≈ **300 мс** (α=0.625 vs эталон 0.48 с), baseline vs PSI k=2.5.

### Параметры

- **NeuronClassName:** `NSPNeuronGen`
- **k (PSI):** `—`
- **SyncTolerance₀:** `0.0125`
- **PeakMeasureMargin₀:** `0.0175`
- **DelayAgreeMarginMin₀:** `0.0175`
- **IterationGap:** `1.5` (не масштабируется)
- **ISI floor:** `1.5 мс`
- **Autothr:** `gap_fraction=0.85`

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP32_span300ms_baseline/Train/Project.ini -s -t 90 -x -S
# sync Train→Test, затем:
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP32_span300ms_baseline/Test/Project.ini -s -t 20 -x
```

Серия: [`../README.md`](../README.md) · отчёт: [`../REPORT_time_expand.md`](../REPORT_time_expand.md).

## EXP26_span10ms_baseline — PSI time-compress

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP26_span10ms_baseline`  
**Статус:** экспериментальный конфиг StructTrain / SelectivityPresynapticInhib

### Назначение

Сжатый паттерн first→last ≈ **10 мс** (α=0.0208333), baseline vs PSI.

### Параметры

- **NeuronClassName:** `NSPNeuronGen`
- **k (PSI):** `—`
- **SyncTolerance₀:** `0.0015`
- **PeakMeasureMargin₀:** `0.002`
- **DelayAgreeMarginMin₀:** `0.002`
- **IterationGap:** `1.5` (не масштабируется)
- **ISI floor:** `1.5 мс`
- **Autothr:** `gap_fraction=0.85`

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP26_span10ms_baseline/Train/Project.ini -s -t 90 -x -S
# sync Train→Test, затем:
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP26_span10ms_baseline/Test/Project.ini -s -t 20 -x
```

Серия: [`../README.md`](../README.md) · отчёт: [`../REPORT_time_compress.md`](../REPORT_time_compress.md).

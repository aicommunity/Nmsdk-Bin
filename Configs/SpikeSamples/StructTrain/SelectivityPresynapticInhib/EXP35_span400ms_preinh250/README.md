## EXP35_span400ms_preinh250 — PSI time-expand

**Путь:** `Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP35_span400ms_preinh250`  
**Статус:** экспериментальный конфиг StructTrain / SelectivityPresynapticInhib

### Назначение

Расширенный паттерн first→last ≈ **400 мс** (α=0.833333 vs эталон 0.48 с), baseline vs PSI k=2.5.

### Параметры

- **NeuronClassName:** `NSPNeuronGenPreinh2_5`
- **k (PSI):** `2.5`
- **SyncTolerance₀:** `0.0166667`
- **PeakMeasureMargin₀:** `0.0233333`
- **DelayAgreeMarginMin₀:** `0.0233333`
- **IterationGap:** `1.5` (не масштабируется)
- **ISI floor:** `1.5 мс`
- **Autothr:** `gap_fraction=0.85`

### Использование

```bash
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Train/Project.ini -s -t 90 -x -S
# sync Train→Test, затем:
NeuroModelerConsole -c /home/user/Nmsdk/Bin/Configs/SpikeSamples/StructTrain/SelectivityPresynapticInhib/EXP35_span400ms_preinh250/Test/Project.ini -s -t 20 -x
```

Серия: [`../README.md`](../README.md) · отчёт: [`../REPORT_time_expand.md`](../REPORT_time_expand.md).

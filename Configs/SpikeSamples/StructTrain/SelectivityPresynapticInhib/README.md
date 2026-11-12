# SelectivityPresynapticInhib

Исследование детекции паттерна при пресинаптическом торможении tip-синапсов (`UsePresynapticInhibition`).

Прототипы Storage: `NSPNeuronGen` / `NSPNeuronGenPreinh*` (k = 0.5…10 и окрестность 2.1–2.7).

Формула: `Output = C*(1-k*PreOutput)*PreOutput`, `C=4k/R` (пик = `1/R`).  
Отчёты: [REPORT.md](REPORT.md), [REPORT_autothr.md](REPORT_autothr.md), [REPORT_gui_autothr.md](REPORT_gui_autothr.md), [REPORT_k_sweep.md](REPORT_k_sweep.md), [REPORT_time_compress.md](REPORT_time_compress.md) (выводы Acc пересмотрены — Erratum; повтор quality-tune).

**Протокол:** cold train `NeuroModelerConsole -t 90 -x -S` → sync Train→Test → test `-t 20 -x`.  
Autothr: `AutoCalibrateFixedLTZThreshold=1`, mode `gap_fraction`, fraction `0.85`.

**Description в GUI:** `Project.ini` указывает на `README.md` (приоритет над legacy `Description.rtf`). Подробности — в `EXP*/Train/README.md` и `EXP*/Test/README.md`.

| EXP | NeuronClassName | k | L | Calibrated thr | Test |
|-----|-----------------|--:|---|---------------:|:----:|
| EXP00_baseline_autothr | NSPNeuronGen | — | `[49,41,25,1]` | 0.01254 | 4/8 |
| EXP01_preinh_050 | NSPNeuronGenPreinh0_5 | 0.5 | `[49,41,25,1]` | 0.01978 | 4/8 |
| EXP02_preinh_100 | NSPNeuronGenPreinh | 1.0 | `[49,44,25,1]` | 0.03015 | 4/8 |
| EXP03_preinh_200 | NSPNeuronGenPreinh2_0 | 2.0 | `[49,41,25,1]` | 0.02996 | 5/8 |
| EXP04_preinh_250 | NSPNeuronGenPreinh2_5 | 2.5 | `[51,43,25,1]` | 0.03017 | **6/8** |
| EXP05–09, 10, 13, 15 | Preinh* | 1.8…10 | см. отчёт | ~0.03 | 5/8 |
| EXP11, 12, 14 | Preinh2_1 / 2_2 / 2_6 | 2.1–2.6 | `[51,43,25,1]` | ~0.030 | **6/8** |

Полная таблица — в [REPORT_k_sweep.md](REPORT_k_sweep.md).

## Watch: дендриты vs `DendriticSumPotential`

| ChartTitle | Источник | Смысл |
|---|---|---|
| Dendrite Amplitudes | `NeuronTimeLearner.DendriteNeuronAmplitude[i]` | `DendriteN_1.SumPotential` (проксимальный сегмент у сомы) |
| Neuron Sums | `Neuron.DendriticSumPotential` | avg `SumChannelInput` по каналам сомы |
| Neuron Sums | `Neuron.SomaSumPotential` | avg `Output` каналов сомы |

`DendriticSumPotential` в `NPulseNeuron::ACalculate` — сумма `SumChannelInput` всех каналов сомы, делённая на `div_coeff = full_ch_counter / NumChannelsInGroup`. В этих конфигах 4 сомы × Exc/Inh, `NumChannelsInGroup=2` → **`div_coeff = 4`**.

Цепь: tip `DendriteN_L` → … → `DendriteN_1` → `SomaN`. На сому заведены `DendriteN_1.Exc/Inh.Output` → `SomaN.Exc/Inh.ChannelInputs`, поэтому:

```text
DendriticSumPotential
  ≈ mean(DendriteNeuronAmplitude[1..4])
  = DendriteNeuronAmplitude[0] / 4
```

Индекс `[0]` у learner — **сумма** по четырём дендритам; `DendriticSumPotential` — уже **среднее**. На одном графике кривые расходятся ~×4, хотя это одна величина с разным масштабом. Сравнивайте со средним `[1..4]` или с `[0]/4`, не с сырой суммой `[0]`. Аналогично: `SomaSumPotential ≈ SomaNeuronAmplitude[0] / 4`.

```bash
# GUI: File → Open → .../EXP04_preinh_250/Train/Project.ini → Start
./scripts/setup_k_sweep.sh       # k-sweep; не трогает EXP00–03
./scripts/setup_time_compress.sh # EXP20–27 сжатие ISI; не трогает EXP00–15
NeuroModelerConsole --check-config EXP04_preinh_250/Train/Project.ini
```

# SelectivityPresynapticInhib

Исследование детекции паттерна при пресинаптическом торможении tip-синапсов (`UsePresynapticInhibition`).

Прототипы Storage (без правок learner): `NSPNeuronGen` / `NSPNeuronGenPreinh0_5` / `NSPNeuronGenPreinh` / `NSPNeuronGenPreinh2_0`.

Формула: `Output = C*(1-k*PreOutput)*PreOutput`, `C=4k/R` (пик = `1/R`). См. [REPORT.md](REPORT.md), autothr: [REPORT_autothr.md](REPORT_autothr.md), GUI-train: [REPORT_gui_autothr.md](REPORT_gui_autothr.md).

**GUI / console train (PSI):** EXP01–03 `Train/` сохранены после Done+autothr (`IsNeedToTrain=0`, выросшие L). Повторный cold start: `./scripts/setup_experiments.sh` (затирает веса).

| EXP | NeuronClassName | k | L | Calibrated thr | Test |
|-----|-----------------|--:|---|---------------:|:----:|
| EXP00_baseline_autothr | NSPNeuronGen | — | `[49,41,25,1]` | 0.01254 | 4/8 |
| EXP01_preinh_050 | NSPNeuronGenPreinh0_5 | 0.5 | `[49,41,25,1]` | 0.01978 | 4/8 |
| EXP02_preinh_100 | NSPNeuronGenPreinh | 1.0 | `[49,44,25,1]` | 0.03015 | 4/8 |
| EXP03_preinh_200 | NSPNeuronGenPreinh2_0 | 2.0 | `[49,41,25,1]` | 0.02996 | 5/8 |

```bash
# GUI: File → Open → .../EXP02_preinh_100/Train/Project.ini → Start
./scripts/setup_experiments.sh && ./scripts/run_experiments.sh
./scripts/setup_autothr_experiments.sh && ./scripts/run_autothr_experiments.sh
```

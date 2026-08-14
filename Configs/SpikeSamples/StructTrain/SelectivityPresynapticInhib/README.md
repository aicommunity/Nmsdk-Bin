# SelectivityPresynapticInhib

Исследование детекции паттерна при пресинаптическом торможении tip-синапсов (`UsePresynapticInhibition`).

Прототипы Storage (без правок learner): `NSPNeuronGen` / `NSPNeuronGenPreinh0_5` / `NSPNeuronGenPreinh` / `NSPNeuronGenPreinh2_0`.

Формула: `Output = C*(1-k*PreOutput)*PreOutput`, `C=4k/R` (пик = `1/R`). См. [REPORT.md](REPORT.md), autothr: [REPORT_autothr.md](REPORT_autothr.md).

| EXP | NeuronClassName | k | Fixed thr | Autothr | Accuracy |
|-----|-----------------|--:|-----------|:-------:|:--------:|
| EXP00_baseline | NSPNeuronGen | — | 0.0115 | off | 4/8 |
| EXP00_baseline_autothr | NSPNeuronGen | — | →0.01254 | on | 4/8 |
| EXP01_preinh_050 | NSPNeuronGenPreinh0_5 | 0.5 | 0.0115 | off | 1/8* |
| EXP01_preinh_050_autothr | … | 0.5 | 0.0115† | on | 1/8* |
| EXP02_preinh_100 | NSPNeuronGenPreinh | 1.0 | 0.0115 | off | 1/8‡ |
| EXP02_preinh_100_autothr | … | 1.0 | 0.0115† | on | 1/8* |
| EXP03_preinh_200 | NSPNeuronGenPreinh2_0 | 2.0 | 0.0115 | off | 1/8* |
| EXP03_preinh_200_autothr | … | 2.0 | 0.0115† | on | 1/8* |

\* Console cold-train PSI не сошёлся (L=`[1,1,1,1]`).  
† Autothr не сработал (нет LTZ snapshot).  
‡ GUI-train OK, L=`[49,44,25,1]`.

```bash
./scripts/setup_experiments.sh && ./scripts/run_experiments.sh
./scripts/setup_autothr_experiments.sh && ./scripts/run_autothr_experiments.sh
```

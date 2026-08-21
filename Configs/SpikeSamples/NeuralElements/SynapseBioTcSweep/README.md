# SynapseBioTcSweep

Одиночный `NPSynapseBio`: импульс генератора → Output. Сетка `DissociationTC`.

## R1

| cell | DissociationTC |
|------|----------------|
| D005 | 0.005 |
| D002 | 0.002 |
| D001 | 0.001 |
| D0005 | 0.0005 |

`GlobalTimeStep=2000`, SecretionTC=0.001.

## Запуск

```bash
../scripts/run_parallel.sh cells 3
python3 ../scripts/extract_metrics.py --batch cells --out metrics_r1.csv --meta meta_r1.json
```

Gate (цель 25 мс): FWHM ≤ 2.1 мс и steps_per_tau ≥ 2.

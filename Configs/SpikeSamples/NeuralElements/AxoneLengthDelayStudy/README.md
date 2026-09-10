# AxoneLengthDelayStudy

Зависимость **first-spike lag** от «длины» для `NAxoneDelay`, `NAxoneChain`, `NAxoneChainAndDelay`.

## Быстрый старт

```bash
cd Bin/Configs/SpikeSamples/NeuralElements/AxoneLengthDelayStudy
./scripts/setup_cells.sh          # templates → 15 cells + Watch + structural -S
MAX_JOBS=4 ./scripts/run_study.sh # parallel Console, metrics.csv, plots/
```

GUI: NeuroModeler → открыть `cells/<cell>/project.ini` → Reset → Start → Watch (`PGenerator` + `AxoneUnderTest`).

## Содержимое

| Путь | Назначение |
|------|------------|
| `templates/{delay,chain,chain_and_delay}/` | эталоны Model/Parameters/Interface |
| `cells/*/` | 15 ячеек сетки |
| `grid_cells.tsv` | метаданные сетки |
| `metrics.csv` | first-spike lag |
| `plots/*.png` | графики |
| `REPORT.md` | результаты |
| `scripts/` | setup / run / extract / plot / ensure_watch |

Протокол: `DefaultTimeStep=2000`, `Frequency=10`, `PulseLength=0.001`, `LTZone.Threshold=0.03`, `SIM_T=0.5`, `MAX_JOBS≤4`.

`NumSegments`/`NumNodes=1` обязан содержать `Segment1` в XML (шаблоны chain/cad поднимают его через 2→1 + prune). Смена длины в GUI: property + Reset.

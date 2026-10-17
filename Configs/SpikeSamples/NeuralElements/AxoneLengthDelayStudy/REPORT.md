# AxoneLengthDelayStudy — REPORT

Каталог: `Bin/Configs/SpikeSamples/NeuralElements/AxoneLengthDelayStudy/`.  
Метрика: **first-spike lag** = \(t_\text{first}(\texttt{AxoneUnderTest.Output}>0.5) - t_\text{first}(\texttt{PGenerator.Output}>0.5)\).

## Протокол

| Параметр | Значение |
|----------|----------|
| TimeStep | 2000 (dt = 0.5 ms) |
| PGenerator | Frequency=10, PulseLength=0.001, Amplitude=1, Delay=0 |
| LTZone.Threshold | 0.03 (регенеративные сегменты) |
| InternodeDelayTime (cad) | 0.002 s |
| SIM_T | 0.5 s |
| MAX_JOBS | 4 |
| Watch | schemaVersion=2, серии PGenerator + AxoneUnderTest |

## Каталог ячеек

| cell | model | length |
|------|-------|--------|
| delay_t1ms … delay_t20ms | NAxoneDelay | DelayTime 1/2/5/10/20 ms |
| chain_n1 … chain_n7 | NAxoneChain | NumSegments 1/2/3/5/7 |
| cad_n1 … cad_n5 | NAxoneChainAndDelay | NumNodes 1…5 |

## Результаты (`metrics.csv`)

| cell | length | lag_ms | ok |
|------|--------|--------|-----|
| delay_t1ms | 0.001 s | 1.5 | 1 |
| delay_t2ms | 0.002 s | 2.5 | 1 |
| delay_t5ms | 0.005 s | 5.5 | 1 |
| delay_t10ms | 0.01 s | 10.5 | 1 |
| delay_t20ms | 0.02 s | 20.5 | 1 |
| chain_n1 | 1 | 0.5 | 1 |
| chain_n2 | 2 | 1.0 | 1 |
| chain_n3 | 3 | 1.5 | 1 |
| chain_n5 | 5 | 2.5 | 1 |
| chain_n7 | 7 | 3.5 | 1 |
| cad_n1 | 1 | 0.5 | 1 |
| cad_n2 | 2 | 3.5 | 1 |
| cad_n3 | 3 | 6.5 | 1 |
| cad_n4 | 4 | 9.5 | 1 |
| cad_n5 | 5 | 12.5 | 1 |

Все 15 ячеек: `ok=1`.

## Графики

- [plots/delay_vs_DelayTime.png](plots/delay_vs_DelayTime.png) — lag ≈ DelayTime + 0.5 ms (один шаг дискретизации)
- [plots/delay_vs_NumSegments.png](plots/delay_vs_NumSegments.png) — линейный рост ≈ 0.5 ms × NumSegments
- [plots/delay_vs_NumNodes.png](plots/delay_vs_NumNodes.png) — lag ≈ 0.5 + (NumNodes−1)×3.0 ms (регенерация узлов + InternodeDelay 2 ms + доп. ~1 ms/узел)

## Выводы

1. **NAxoneDelay:** феноменологическая задержка совпадает с `DelayTime` с погрешностью ±0.5…1.0 ms (буфер шагов TimeStep).
2. **NAxoneChain:** каждый регенеративный сегмент добавляет ≈0.5 ms (при Threshold=0.03); лаг строго монотонен по NumSegments.
3. **NAxoneChainAndDelay:** при NumNodes=1 совпадает с одним сегментом (0.5 ms); каждый следующий узел добавляет InternodeDelay (2 ms) плюс регенерацию (~1–1.5 ms суммарно с дискретизацией) → шаг ≈3 ms на узел.

## Watch

Каждая ячейка и каждый template: `Interface.xml` → `UGEngineControllWidget.UWatch.tab_1`, `schemaVersion=2`, `SerieYComponent` = `PGenerator` / `AxoneUnderTest`. После Console `-S` Watch восстанавливается через `scripts/ensure_watch.py`.

## Воспроизведение

```bash
cd Bin/Configs/SpikeSamples/NeuralElements/AxoneLengthDelayStudy
./scripts/setup_cells.sh
MAX_JOBS=4 SIM_T=0.5 ./scripts/run_study.sh
# или по отдельности:
# ../scripts/run_parallel.sh cells 0.5
# python3 scripts/extract_latency.py --batch cells --grid grid_cells.tsv --out metrics.csv
# python3 scripts/plot_latency.py --metrics metrics.csv --outdir plots
```

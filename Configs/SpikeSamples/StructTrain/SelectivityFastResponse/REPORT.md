# SelectivityFastResponse — отчёт (этап 1)

Сетка **DissociationTC × MembraneCapacity** для ускорения EPSP у `NNeuronTimeLearner` без смены Rm/Rsyn.

## API

На `NPulseNeuron` (opt-in, default off):

| Свойство | Default | Смысл |
|----------|---------|--------|
| `UseElementDefaults` | `false` | Включить override дочерних C/TC |
| `MembraneCapacity` | `0` (≤0 = не трогать) | Capacity Exc/Inh каналов Soma+Dendrite |
| `SynapseDissociationTC` | `0` (≤0 = не трогать) | DissociationTC Exc/Inh синапсов |

`ApplyElementDefaults()` вызывается в конце `NPulseNeuron::ABuild` (после `Common::ABuild`, когда TimeStep уже задан). `NSPNeuronGen` без флага — поведение старых моделей не меняется.

UploadClass: `NSPNeuronGenD005C5e10` … `NSPNeuronGenD001C25e11` (имена без `_`).

## Cold Train (важно)

В `Model_00.xml` шаблона есть встроенный `NeuronClassName=NSPNeuronGen`. Если его не переписать, первый `BuildStructure` собирает Gen, затем класс меняется — tip-links ломаются (`amp=0`).  
`setup_grid.sh` патчит и Parameters, и Model: `Neuron Class`, `NeuronClassName`, L=1, TipR=86e6×4.

## Сводка (`grid_summary.csv`)

Train `-t 160 -S`, Test `-t 20`. Gate: `train_ok` = trial0 target `neuron_fired==1`.

| exp | D | C | train_ok | acc | fn/fp | t_peak | Δt vs ctrl |
|-----|---|---|----------|-----|-------|--------|------------|
| EXP00CtrlExp04 | 0.005 | 1e-9 | 1 | 1/8 | 0/7 | 0.089 | 0 |
| EXPD005C5e10 | 0.005 | 5e-10 | 1 | 1/8 | 0/7 | 0.065 | −0.024 |
| EXPD005C25e11 | 0.005 | 2.5e-10 | 1 | 1/8 | 0/7 | 0.065 | −0.024 |
| EXPD002C1e9 | 0.002 | 1e-9 | **0** | 7/8 | 1/0 | — | брак |
| EXPD002C5e10 | 0.002 | 5e-10 | 1 | 1/8 | 0/7 | 0.0785 | −0.0105 |
| EXPD002C25e11 | 0.002 | 2.5e-10 | 1 | 1/8 | 0/7 | **0.0295** | **−0.0595** |
| EXPD001C1e9 | 0.001 | 1e-9 | **0** | 7/8 | 1/0 | — | брак |
| EXPD001C5e10 | 0.001 | 5e-10 | 1 | 1/8 | 0/7 | 0.076 | −0.013 |
| EXPD001C25e11 | 0.001 | 2.5e-10 | 1 | 1/8 | 0/7 | 0.0345 | −0.0545 |

## Выводы

1. **Меньше C ускоряет ответ** при том же D: ctrl 0.089 → C=5e-10 ≈0.065; C=2.5e-10 ещё быстрее на части ячеек.
2. **Лучшие по (train_ok, ↓t_peak):** `EXPD002C25e11` (0.0295) и `EXPD001C25e11` (0.0345).
3. **Брак:** D↓ при C=1e-9 (`EXPD002C1e9`, `EXPD001C1e9`) — target не стреляет (`train_ok=0`); одного снижения DissociationTC без снижения C недостаточно / вредно на cold TipR.
4. **Селективность:** у всех `train_ok=1` ячеек acc=1/8 при fp=7 (перестрел nontarget). Этап 1 измерял latency/gate fire; калибровка SyncTol/порога — отдельно (как PhaseA EXP04 фон уже 0.01).

## Рекомендации (этап 1)

- Для ускорения: **C ≈ 2.5e-10…5e-10** при D ∈ {0.002, 0.005}; ориентир `NSPNeuronGenD002C25e11`.
- Не ставить D=0.001/0.002 при C=1e-9 без доп. калибровки.
- Rm/Rsyn не трогать независимо (этап 1).

## Сноска Exc/Inh

Асимметрия возбуждения/торможения (GABAA vs AMPA, Cm у PV+) в этапе 1 не моделировалась: Exc и Inh получают одинаковые C и DissociationTC. Возможный следующий шаг — раздельные overrides.

## Команды

```bash
./scripts/setup_grid.sh
./scripts/run_grid.sh          # TRAIN_T=240 при необходимости
```

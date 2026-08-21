# SelectivityFastSpan — REPORT

Проверка сжатых span **100 / 50 / 25 мс** с быстрыми элементами `(DissociationTC=0.002, Capacity=2.5e-10)` = `NSPNeuronGenD002C25e11` и Preinh2_5 + те же overrides.

## Элементный пререквизит (NeuralElements)

| Бенч | Вывод |
|------|--------|
| SynapseBioTcSweep | FWHM gate 2.1 мс: D≤0.001; D=0.002 OK с запасом |
| ChannelRcSweep | τ≈C·1e7; C≤2.5e-10 для τ≲2.5 мс |
| TipEps dual-pulse | sep≥0.30 на ISI25 для D∈{0.005…0.001}; D=0.001 лучший |

## R1 FastSpan (GlobalTimeStep=2000)

| EXP | Acc | mode | gate | L |
|-----|-----|------|------|---|
| span100 fast | 1/8 | fire_all | FAIL | 4 3 2 1 |
| span100 preinh+fast | 1/8 | fire_all | FAIL | 5 4 4 1 |
| span50 fast | 1/8 | fire_all | FAIL | 3 3 2 1 |
| span50 preinh+fast | 1/8 | fire_all | FAIL | 4 4 4 1 |
| span25 fast | 1/8 | fire_all | FAIL | 1 1 1 1 |
| span25 preinh+fast | 1/8 | fire_all | FAIL | 4 1 4 1 |

Target hit есть, но nontarget тоже стреляет (fp=7).

## Эскалация

1. **Peak floor** (`NNeuronTimeLearner`): XML PeakMeasureMargin теперь может быть уже cable floor; `kDelayPerSegDefault` 10→5 мс. Rebuild Console. Повтор 25/50: всё ещё **fire_all**.
2. **TimeStep=10000 + FixedLTZ=0.04** на span25: всё ещё **fire_all**.  
   Наблюдение: `soma_amp_sum` ≈ 0.165–0.17 на **всех** trials (target и distractors) — паттерны схлопываются в почти одинаковую сумму EPSP.

## Вывод

Ускорение синапса/мембраны необходимо, но **недостаточно** для селективности на span ≤100 мс в текущем learner+tip протоколе: после обучения сома отвечает одинаково на все короткие паттерны. Следующие направления (вне этого раунда): различение по форме/таймингу пиков (не только sum), сильнее Preinh k, другой tip R / число дендритов, или смена задачи селективности под короткие span.

## Команды

```bash
./scripts/setup_fastspan.sh
MAX_JOBS=4 ./scripts/run_fastspan.sh
```

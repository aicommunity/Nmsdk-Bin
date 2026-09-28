# Валидированные Iris, NClassifier и NPCA replay

Этот каталог содержит Iris-клоны `NSpikeClassifier`, четыре пороговых клона `NClassifier` и однопаттерновый `NPCAClassifier`. Перед анализом проверены пути рекордера: выходы классификатора подключены к фактическим `LTZone.Output`, и записанные биты совпадают с фронтами в каждом ответном окне.

**Не используйте `NSpikeSynapseCount_*` и `NSpikeClassifier_AllProbes_*` из этого каталога для подсчёта спайков.** В первой версии этих клонов сохранилась старая диагностическая карта, где aliases `_ltz` были связаны не с выходами нейронов. Исправленная серия перебора синапсов и On/Off находится в [`BurstReplayVerified_20260928`](../BurstReplayVerified_20260928/README.md).

[`burst_replay_summary.csv`](burst_replay_summary.csv) содержит итоги только по валидным Iris/NClassifier/NPCA клонам. Полные трассы `signals.csv`, `output_data.txt` и команды запуска хранятся в каталогах отдельных проектов.

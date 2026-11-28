# Статическая диагностика временных масштабов перенесена в корень

Активные `audit_timelearner_step_stability.py` и
`audit_timelearner_config_tree_stability.py` перенесены в корневой модуль
`Scripts/StructTrain/TimeLearner/declared_time_scales.py`. Старые entrypoints
удалены без wrappers и исторических копий в текущем дереве. Исходные конфиги,
модели, JSON/CSV, диагностики и отчёты сохранены.

Из корня SDK:

```text
python -B -m Scripts.StructTrain.TimeLearner audit-time-scales \
  --config-root /absolute/path/to/TimeLearnerMatrix --discovery matrix \
  --output /existing/output/directory/declared-time-scales.json
```

Для отслеживаемого Git дерева конфигов используется `--discovery tracked-tree`
с его явным `--config-root`. Связанные Project.ini читаются в диалекте Rdk,
включая `<00>`; частота не подменяется молча на 2000 Hz. Пропущенные или
некорректные данные остаются unknown/not_assessed. `Q=C*R*f` — условная
диагностика при нулевой проводимости, без вердикта об устойчивости интегратора,
effective model или storage. Результаты старых запусков не пересчитывались.

Проверенный корневой source:
`4e9aff7b72d3cc2460c6d9c886e0f2d7e39d5277`, 143/143 на M40 и 143/143 на Elder.
Подробности: `Docs/StructTrain/TimeLearner/DeclaredTimeScaleDiagnostic.ru.md`
и migration registry в корневом репозитории.

## Точные исторические исходники

Оба файла доступны в **Bin** commit
`36f4ce6ae4cdbea90240dced08425fdf64f3bcf7`:

| Путь относительно Bin | Git blob | SHA-256 | Последний изменявший commit |
|---|---|---|---|
| `Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/scripts/audit_timelearner_step_stability.py` | `2c865b33ab4bbd3c9c72c8f636aef18dca977160` | `5ef2a7a21163e8cdacdab27da7fbff7130be979673002a6ab2c200e5b065aa7b` | `2c7fdd86c8974c3c7a0ac1635c809d8e6cb0d8d7` |
| `Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/scripts/audit_timelearner_config_tree_stability.py` | `689d78e13ece1fdb8cf7df157e73822f23b16701` | `d6fc4ff1b8ef51a72e37266fdd6e1f87a20a6539a0bde9821b05470ec0ecd02f` | `13b6a7dec175b1aeaeee0700f50f683ab1061970` |

```text
git -C Bin show 36f4ce6ae4cdbea90240dced08425fdf64f3bcf7:Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/scripts/audit_timelearner_step_stability.py
git -C Bin show 36f4ce6ae4cdbea90240dced08425fdf64f3bcf7:Configs/SpikeSamples/StructTrain/TimeLearnerMatrix/scripts/audit_timelearner_config_tree_stability.py
```

Это source retrieval; исторические скрипты не следует запускать как современный
аудитор. Перенос исправляет отсутствующие defaults, invalid/nonfinite factors,
пустые каналы, единообразие thresholds и frozen-byte provenance; побайтовая
эквивалентность ошибочных старых отчётов не заявляется.

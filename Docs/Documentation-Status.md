# Статус документации Bin

Краткий статус документации каталога `Bin/Docs/` и чеклист синхронизации с ресурсами и конфигурациями.

**Аудит:** 2026-06-06 — [Documentation-Inventory.json](../../Docs/Audit/Documentation-Inventory.json), [Link-Health-Report.md](../../Docs/Audit/Link-Health-Report.md), [Bilingual-Parity-Report.md](../../Docs/Audit/Bilingual-Parity-Report.md)

> **Область:** `Bin/Docs/` (markdown). HTML-справка в `Bin/Help/`, XML в `Bin/Configs/` и `Bin/ClDesc/` — упоминаются как связанные артефакты, но не входят в подсчёт файлов ниже.

---

## Статистика

| Метрика | Значение |
|---------|----------|
| Markdown-файлов в `Bin/Docs/` | **21** |
| Файлов с секцией `## EN` | **8** (38%) |
| Файлов RU-only | **13** (62%) — в основном `SpikeSamples/` |
| Битых ссылок (зона Bin/Docs) | **~15** — см. Link-Health-Report |
| SpikeSamples topic docs | **12** |

**Прогресс:** базовая структура Bin и примеры **документированы** (RU/EN); каталог SpikeSamples **создан** (RU-only); основные пробелы — bilingual parity, битые ссылки в SpikeSamples, отсутствие EN для Literature-References.

---

## Выполнено

### Навигация и обзор
- ✅ **README.md** — назначение Bin/, структура каталогов, mermaid-схема (RU/EN)
- ✅ **FAQ.md** — вопросы по конфигурациям и ресурсам (RU/EN)
- ✅ **Help-Structure.md** — структура HTML-справки RU/EN (RU/EN)
- ✅ **Configs-Structure.md** — структура XML-конфигураций (RU/EN)

### Примеры (`Examples/`)
- ✅ **README.md** — индекс примеров (RU/EN)
- ✅ **Config-Example.md** — пример конфигурации (RU/EN)
- ✅ **ClDesc-Example.md** — пример ClDesc (RU/EN)
- ✅ **Style-Example.md** — пример стилей (RU/EN)

### SpikeSamples (`SpikeSamples/`) — RU-only
- ✅ **Overview.md** — обзор тематических конфигов
- ✅ **Index.md** — индекс документов SpikeSamples
- ✅ **HowToDocumentConfigs.md** — руководство по документированию конфигов
- ✅ **ActivitySwitcher.md**
- ✅ **Classification.md**
- ✅ **CognitiveMap.md**
- ✅ **CSNM-Models.md**
- ✅ **ImpulseProcessingModel.md**
- ✅ **IncrementalLearning.md**
- ✅ **MuscleControlStructures.md**
- ✅ **NeuronReactions.md**
- ✅ **StructuralAdaptation.md**

### Справочники
- ✅ **Literature-References.md** — центральный справочник публикаций ([A], [B], [C], номера 1–31); используется библиотеками PulseLib/MotionControlLib (RU-only)

### Связь с конфигурациями
- ✅ Документированы пути `Bin/Configs/`, `Bin/ClDesc/`, `Bin/Help/`, `Bin/Styles/`, `Bin/Platform/`
- ✅ SpikeSamples docs соотнесены с `Bin/Configs/SpikeSamples/` (тематические README в подкаталогах)

---

## Планируется / рекомендации

### Приоритет P0 — битые ссылки
- [ ] **SpikeSamples/Overview.md** — исправить ссылки `SpikeSamples/X.md` → `X.md` (или `./X.md`)
- [ ] **SpikeSamples/HowToDocumentConfigs.md** — удалить/заменить битые ссылки (`Document.md`, `RelatedConfig/README.md`, placeholder `путь`)
- [ ] **Configs-Structure.md** — исправить ссылку на `Docs/Components-And-Configuration/Component-System.md` (создать цель или обновить путь на `Rdk/Docs/Guides/Component-System.md`)
- [ ] **Examples/ClDesc-Example.md** — та же ссылка на Component-System

### Приоритет P1 — bilingual parity
- [ ] Добавить `## EN` в **Literature-References.md** (или вынести EN-таблицу в отдельный блок)
- [ ] Добавить `## EN` во все **12** файлов `SpikeSamples/*.md`
- [ ] Согласовать с allowlist в Bilingual-Parity-Report (`Bin/Configs/SpikeSamples/*` — configs могут оставаться RU-only; **docs** — нет)

### Приоритет P2 — полнота SpikeSamples
- [ ] Сверить Index.md со всеми подкаталогами `Bin/Configs/SpikeSamples/` (Hardware, STDP, MC-Muscles и др.)
- [ ] Добавить Overview-ссылки на недокументированные SpikeSamples-темы
- [ ] Синхронизировать идентификаторы Literature-References с локальными копиями в `Libraries/Nmsdk-PulseLib/Docs/` и `Libraries/Nmsdk-MotionControlLib/Docs/`

### Приоритет P3 — навигация
- [ ] Добавить ссылки на `Libraries/*/Docs/Documentation-Status.md` из README
- [ ] Удалить или заполнить артефакт `SpikeSamples/Untitled` (если присутствует в рабочей копии)

---

## Чеклист по файлам

### Корневые документы
| Файл | RU | EN | Ссылки | Примечание |
|------|----|----|--------|------------|
| README.md | ✅ | ✅ | ✅ | Индекс Bin/Docs |
| FAQ.md | ✅ | ✅ | ✅ | |
| Help-Structure.md | ✅ | ✅ | ✅ | Связь с Bin/Help/ |
| Configs-Structure.md | ✅ | ✅ | ❌ | Component-System |
| Literature-References.md | ✅ | ❌ | ✅ | Центральный справочник |

### Examples/ (4 файла)
| Файл | RU | EN | Ссылки |
|------|----|----|--------|
| README.md | ✅ | ✅ | ✅ |
| Config-Example.md | ✅ | ✅ | ✅ |
| ClDesc-Example.md | ✅ | ✅ | ❌ |
| Style-Example.md | ✅ | ✅ | ✅ |

### SpikeSamples/ (12 файлов)
| Файл | RU | EN | Ссылки | Config mapping |
|------|----|----|--------|----------------|
| Overview.md | ✅ | ❌ | ❌ | Обзор |
| Index.md | ✅ | ❌ | ⚠ | Индекс |
| HowToDocumentConfigs.md | ✅ | ❌ | ❌ | Методология |
| ActivitySwitcher.md | ✅ | ❌ | ✅ | SpikeSamples/ActivitySwitcher |
| Classification.md | ✅ | ❌ | ✅ | SpikeSamples/Classifier |
| CognitiveMap.md | ✅ | ❌ | ✅ | SpikeSamples/CognitiveMap |
| CSNM-Models.md | ✅ | ❌ | ✅ | SpikeSamples/CSNM |
| ImpulseProcessingModel.md | ✅ | ❌ | ✅ | SpikeSamples/ImpulseProcessing |
| IncrementalLearning.md | ✅ | ❌ | ✅ | SpikeSamples/IncrementalLearning |
| MuscleControlStructures.md | ✅ | ❌ | ✅ | SpikeSamples/MC-Muscles |
| NeuronReactions.md | ✅ | ❌ | ✅ | SpikeSamples/NeuronReactions |
| StructuralAdaptation.md | ✅ | ❌ | ✅ | SpikeSamples/StructTrain |

---

## Чеклист синхронизации с артефактами Bin

При добавлении или изменении ресурсов в `Bin/` рекомендуется обновить:

1. **Configs-Structure.md** — при изменении схемы XML-проектов или layout `Bin/Configs/`
2. **Help-Structure.md** — при изменении структуры `Bin/Help/RU/` и `Bin/Help/EN/`
3. **Examples/** — при появлении новых эталонных конфигов, ClDesc или QSS
4. **SpikeSamples/** — при добавлении тематического каталога в `Bin/Configs/SpikeSamples/`:
   - создать или обновить topic doc в `Bin/Docs/SpikeSamples/`
   - добавить запись в **Index.md** и **Overview.md**
   - следовать **HowToDocumentConfigs.md**
5. **Literature-References.md** — при добавлении публикаций, используемых в doc-компонентах библиотек
6. **FAQ.md** — при типовых вопросах по новым ресурсам
7. **Libraries/*/Docs/** — обновить ссылки на `Bin/Configs/SpikeSamples/` в Usage-Examples и компонентах
8. Перезапустить аудит: `Scripts/doc-audit/run-all.sh`

### Связанные артефакты (вне Bin/Docs)

| Артефакт | Документ |
|----------|----------|
| `Bin/Configs/*.xml` | Configs-Structure, SpikeSamples/*, Examples/Config-Example |
| `Bin/ClDesc/*.xml` | Examples/ClDesc-Example, Rdk/Docs/Guides/Component-System |
| `Bin/Help/` | Help-Structure |
| `Bin/Styles/` | Examples/Style-Example, Docs/GUI/Style-System |
| `Bin/Configs/SpikeSamples/*/` | SpikeSamples/*.md, Libraries Usage-Examples |

---

## EN

### Documentation status summary

`Bin/Docs/` has **21** markdown files. **8** are bilingual (38%); **13** SpikeSamples docs are RU-only. Core Bin structure, examples, and Literature-References exist. Main gaps: **broken links** in SpikeSamples/Overview and HowToDocumentConfigs, **missing EN** for SpikeSamples and Literature-References, and **incomplete SpikeSamples index** vs `Bin/Configs/SpikeSamples/` subdirectories.

### Priority actions

1. Fix SpikeSamples relative links (Overview, HowToDocumentConfigs)
2. Add `## EN` to all SpikeSamples docs and Literature-References
3. Align SpikeSamples Index/Overview with all config subdirectories (Hardware, STDP, etc.)

### Sync checklist (artifact changes)

When changing Bin resources: update Configs-Structure, Help-Structure, Examples, SpikeSamples docs (Index, Overview), Literature-References, library cross-links; re-run doc audit.

---

*Источники: [Documentation-Inventory.json](../../Docs/Audit/Documentation-Inventory.json), [Link-Health-Report.md](../../Docs/Audit/Link-Health-Report.md), [Bilingual-Parity-Report.md](../../Docs/Audit/Bilingual-Parity-Report.md); шаблон — [Nmsdk-PulseLib/Docs/Documentation-Status.md](../../Libraries/Nmsdk-PulseLib/Docs/Documentation-Status.md).*

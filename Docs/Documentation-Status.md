# Статус документации Bin

## RU

Краткий статус документации каталога `Bin/Docs/` и чеклист синхронизации с ресурсами и конфигурациями.

**Аудит:** 2026-06-06 — [Documentation-Inventory.json](../../Docs/Audit/Documentation-Inventory.json), [Link-Health-Report.md](../../Docs/Audit/Link-Health-Report.md), [Bilingual-Parity-Report.md](../../Docs/Audit/Bilingual-Parity-Report.md)

> **Область:** `Bin/Docs/` (markdown). HTML-справка в `Bin/Help/`, XML в `Bin/Configs/` и `Bin/ClDesc/` — упоминаются как связанные артефакты, но не входят в подсчёт файлов ниже.

---

## Статистика

| Метрика | Значение |
|---------|----------|
| Markdown-файлов в `Bin/Docs/` | **21** |
| Файлов с секцией `## EN

` | **8** (38%) |
| Файлов RU-only | **13** (62%) — в основном `SpikeSamples/` |
| Битых ссылок (зона Bin/Docs) | **~15** — see Link-Health-Report |
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
- ✅ **ClDesc-Example.md** — пример ClDesc по реальной схеме + Favorites (RU/EN); методология DETAILED — `Docs/ClDesc-Detailed-Methodology.md`
- ✅ **Style-Example.md** — пример стилей (RU/EN)

### SpikeSamples (`SpikeSamples/`) — RU-only
- ✅ **Overview.md** — обзор тематических конфигов
- ✅ **Index.md** — индекс документов SpikeSamples
- ✅ **HowToDocumentConfigs.md** — guide по документированию конфигов
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

## EN

Brief status of the `Bin/Docs/` catalog and a synchronization checklist with resources and configurations.

**Audit:** 2026-06-06 — [Documentation-Inventory.json](../../Docs/Audit/Documentation-Inventory.json), [Link-Health-Report.md](../../Docs/Audit/Link-Health-Report.md), [Bilingual-Parity-Report.md](../../Docs/Audit/Bilingual-Parity-Report.md)

> **Scope:** `Bin/Docs/` (markdown). HTML help in `Bin/Help/`, XML in `Bin/Configs/` and `Bin/ClDesc/` are mentioned as related artifacts but are not included in the file counts below.

---

## Statistics

| Metric | Value |
|---------|----------|
| Markdown files in `Bin/Docs/` | **21** |
| Files with `## EN` section | **8** (38%) |
| RU-only files | **13** (62%) — mainly `SpikeSamples/` |
| Broken links (Bin/Docs zone) | **~15** — see Link-Health-Report |
| SpikeSamples topic docs | **12** |

**Progress:** basic Bin structure and examples are **documented** (RU/EN); SpikeSamples catalog is **created** (RU-only); main gaps — bilingual parity, broken links in SpikeSamples, missing EN for Literature-References.

---

## Completed

### Navigation and overview
- ✅ **README.md** — Bin/ purpose, directory structure, mermaid diagram (RU/EN)
- ✅ **FAQ.md** — questions about configurations and resources (RU/EN)
- ✅ **Help-Structure.md** — HTML help structure RU/EN (RU/EN)
- ✅ **Configs-Structure.md** — XML configuration structure (RU/EN)

### Examples (`Examples/`)
- ✅ **README.md** — examples index (RU/EN)
- ✅ **Config-Example.md** — configuration example (RU/EN)
- ✅ **ClDesc-Example.md** — ClDesc example (RU/EN)
- ✅ **Style-Example.md** — styles example (RU/EN)

### SpikeSamples (`SpikeSamples/`) — RU-only
- ✅ **Overview.md** — thematic configs overview
- ✅ **Index.md** — SpikeSamples documents index
- ✅ **HowToDocumentConfigs.md** — config documentation guide
- ✅ **ActivitySwitcher.md**
- ✅ **Classification.md**
- ✅ **CognitiveMap.md**
- ✅ **CSNM-Models.md**
- ✅ **ImpulseProcessingModel.md**
- ✅ **IncrementalLearning.md**
- ✅ **MuscleControlStructures.md**
- ✅ **NeuronReactions.md**
- ✅ **StructuralAdaptation.md**

### References
- ✅ **Literature-References.md** — central publications reference ([A], [B], [C], numbers 1–31); used by PulseLib/MotionControlLib libraries (RU-only)

### Connection with configurations
- ✅ Documented paths `Bin/Configs/`, `Bin/ClDesc/`, `Bin/Help/`, `Bin/Styles/`, `Bin/Platform/`
- ✅ SpikeSamples docs mapped to `Bin/Configs/SpikeSamples/` (thematic READMEs in subdirectories)

---

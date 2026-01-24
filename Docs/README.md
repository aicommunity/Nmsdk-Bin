# Документация Bin

## RU

### Назначение

Каталог `Bin/` содержит ресурсы и конфигурации, необходимые для работы приложения Nmsdk.

### Быстрые ссылки

- [Структура конфигураций](Configs-Structure.md) - описание конфигурационных файлов
- [Структура справки](Help-Structure.md) - структура справочной системы
- [FAQ](FAQ.md) - часто задаваемые вопросы по Bin

### Структура

- **Configs/** - конфигурационные файлы проектов и компонентов
- **ClDesc/** - описания классов компонентов (XML)
- **Help/** - справочная документация пользователя (RU/EN)
- **Styles/** - стили и темы для GUI
- **Platform/** - платформенные артефакты (Win/Linux)

**Архитектура каталога Bin:**

```mermaid
flowchart TB
    Bin[Bin/] --> Configs[Configs/<br/>XML проекты]
    Bin --> ClDesc[ClDesc/<br/>XML описания классов]
    Bin --> Help[Help/<br/>HTML справка RU/EN]
    Bin --> Styles[Styles/<br/>QSS + JSON темы]
    Bin --> Platform[Platform/<br/>Артефакты сборки]
    
    Platform --> WinBin[Win/<br/>Windows бинарники]
    Platform --> LinuxBin[Linux/<br/>Linux бинарники]
    
    Configs --> Projects[Проекты .xml]
    ClDesc --> ClassXML[Описания .xml]
    Styles --> QSSFiles[*.qss]
    Styles --> JSONThemes[theme.json]
```

Каталог `Bin/` содержит как исходные ресурсы (конфигурации, справка, стили), так и артефакты сборки (скомпилированные библиотеки и исполняемые файлы в `Platform/`). Исходные ресурсы копируются в `Bin/` при сборке из соответствующих каталогов в репозитории.

### Документация

- [Help-Structure.md](Help-Structure.md) - структура справочной системы
- [Configs-Structure.md](Configs-Structure.md) - структура конфигурационных файлов
- [FAQ.md](FAQ.md) - часто задаваемые вопросы по конфигурациям и ресурсам
- [Examples/](Examples/) - примеры конфигураций и использования ресурсов

### Связь с корневой документацией

- [Docs/Components-And-Configuration/Configuration-Files-Overview.md](../../Docs/Components-And-Configuration/Configuration-Files-Overview.md) - обзор конфигураций
- [Docs/GUI/Style-System.md](../../Docs/GUI/Style-System.md) - система стилей

---

## EN

### Purpose

The `Bin/` directory contains resources and configurations necessary for the Nmsdk application to work.

### Quick Links

- [Configuration Structure](Configs-Structure.md) - configuration files description
- [Help Structure](Help-Structure.md) - help system structure
- [FAQ](FAQ.md) - frequently asked questions about Bin

### Structure

- **Configs/** - project and component configuration files
- **ClDesc/** - component class descriptions (XML)
- **Help/** - user help documentation (RU/EN)
- **Styles/** - GUI styles and themes
- **Platform/** - platform artifacts (Win/Linux)

### Documentation

- [Help-Structure.md](Help-Structure.md) - help system structure
- [Configs-Structure.md](Configs-Structure.md) - configuration file structure
- [FAQ.md](FAQ.md) - frequently asked questions about configurations and resources
- [Examples/](Examples/) - configuration and resource usage examples

### Link to Root Documentation

- [Docs/Components-And-Configuration/Configuration-Files-Overview.md](../../Docs/Components-And-Configuration/Configuration-Files-Overview.md) - configuration overview
- [Docs/GUI/Style-System.md](../../Docs/GUI/Style-System.md) - style system

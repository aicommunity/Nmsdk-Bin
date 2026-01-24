# Структура конфигурационных файлов (Configs Structure)

## RU

### Обзор

Конфигурационные файлы в `Bin/Configs/` используются для настройки проектов, компонентов и приложения.

### Типы файлов

- **XML** - основной формат для проектов и компонентов
- **INI** - конфигурационные файлы приложения
- **JPEG/PNG** - изображения для конфигураций

### Структура конфигураций проектов

Конфигурации проектов содержат:
- Описание компонентов и их параметров
- Соединения между компонентами
- Настройки выполнения
- Метаданные проекта

### Использование конфигураций в коде

**Примечание:** Детальная информация о работе с конфигурациями через классы Rdk (UProject, UApplication, UXMLEnvSerialize, UProjectDeployer) находится в [Rdk/Docs/Configuration-Management.md](../../Rdk/Docs/Configuration-Management.md).

**Краткая информация:**

- **Проекты** (`.xml`) - загружаются через `UProject::Load()`
- **Настройки приложения** (`.ini`) - читаются через `UApplication::Init()`
- **Стили** (`theme.json`, `*.qss`) - загружаются через `UStyleManager`
- **Описания классов** (`ClDesc/*.xml`) - загружаются автоматически при загрузке библиотек

### Артефакты сборки vs исходные ресурсы

**Исходные ресурсы** (хранятся в репозитории):
- `Bin/Configs/` - шаблоны и примеры конфигураций
- `Bin/Help/` - исходные HTML файлы справки
- `Bin/Styles/` - исходные файлы стилей (копируются из `Rdk/GUI/Qt/Styles/`)

**Артефакты сборки** (генерируются при сборке):
- `Bin/Platform/<OS>/` - скомпилированные исполняемые файлы и библиотеки
- `Bin/Platform/<OS>/Lib.CMake/` - скомпилированные библиотеки
- `Bin/ClDesc/` - может содержать автогенерируемые описания классов (если используется автогенерация)

### Процесс деплоя конфигураций

`UProjectDeployer` используется для развертывания проектов на удалённые системы. Процесс включает:

1. **Загрузку данных** (`StartProjectDeployment`): загрузка шаблонов, скриптов, весов моделей и данных с FTP сервера
2. **Распаковку** (`DeployTemplate`, `DeployScript`, `DeployWeights`, `DeployData`): распаковка ZIP архивов во временные каталоги
3. **Подготовку проекта** (`PrepareProject`): копирование во временное хранилище, открытие в mock режиме, настройка путей и связей

**Процесс деплоя:**

```mermaid
sequenceDiagram
    participant App as UApplication
    participant Deployer as UProjectDeployer
    participant FTP as FTP Server
    participant Temp as Temp Folder
    participant Project as UProject
    
    App->>Deployer: StartProjectDeployment(task_id)
    Deployer->>FTP: DownloadTemplate.zip
    FTP-->>Deployer: Template files
    Deployer->>Temp: UnpackTemplate
    Deployer->>FTP: DownloadWeights.zip
    FTP-->>Deployer: Model weights
    Deployer->>Temp: UnpackWeights
    Deployer->>App: PrepareProject()
    App->>Project: OpenProjectMockMode()
    Project->>Project: SetupMockParameters()
    Project-->>App: Project ready
```

### См. также

- [Rdk/Docs/Configuration-Management.md](../../Rdk/Docs/Configuration-Management.md) - детальная информация о работе с конфигурациями через классы Rdk (UProject, UApplication, UXMLEnvSerialize, UProjectDeployer)
- [Docs/Components-And-Configuration/Configuration-Files-Overview.md](../../Docs/Components-And-Configuration/Configuration-Files-Overview.md) - обзор конфигураций
- [Component System](../../Rdk/Docs/Guides/Component-System.md) - компонентная система

---

## EN

### Overview

Configuration files in `Bin/Configs/` are used to configure projects, components, and the application.

### File Types

- **XML** - main format for projects and components
- **INI** - application configuration files
- **JPEG/PNG** - images for configurations

### Project Configuration Structure

Project configurations contain:
- Component descriptions and parameters
- Connections between components
- Execution settings
- Project metadata

### Configuration Usage in Code

**Note:** Detailed information about working with configurations through Rdk classes (UProject, UApplication, UXMLEnvSerialize, UProjectDeployer) is in [Rdk/Docs/Configuration-Management.md](../../Rdk/Docs/Configuration-Management.md).

**Brief information:**

- **Projects** (`.xml`) - loaded via `UProject::Load()`
- **Application settings** (`.ini`) - read via `UApplication::Init()`
- **Styles** (`theme.json`, `*.qss`) - loaded via `UStyleManager`
- **Class descriptions** (`ClDesc/*.xml`) - loaded automatically when loading libraries

### Build Artifacts vs Source Resources

**Source resources** (stored in repository):
- `Bin/Configs/` - configuration templates and examples
- `Bin/Help/` - source HTML help files
- `Bin/Styles/` - source style files (copied from `Rdk/GUI/Qt/Styles/`)

**Build artifacts** (generated during build):
- `Bin/Platform/<OS>/` - compiled executables and libraries
- `Bin/Platform/<OS>/Lib.CMake/` - compiled libraries
- `Bin/ClDesc/` - may contain auto-generated class descriptions (if autogeneration is used)

### See Also

- [Rdk/Docs/Configuration-Management.md](../../Rdk/Docs/Configuration-Management.md) - detailed information about working with configurations through Rdk classes (UProject, UApplication, UXMLEnvSerialize, UProjectDeployer)
- [Docs/Components-And-Configuration/Configuration-Files-Overview.md](../../Docs/Components-And-Configuration/Configuration-Files-Overview.md) - configuration overview
- [Docs/Components-And-Configuration/Component-System.md](../../Docs/Components-And-Configuration/Component-System.md) - component system

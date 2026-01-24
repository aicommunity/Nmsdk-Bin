# FAQ - Bin (Ресурсы и конфигурации)

## RU

### Общие вопросы

#### Что такое каталог Bin?

Каталог `Bin/` содержит ресурсы и конфигурации, необходимые для работы приложения Nmsdk. Он включает конфигурационные файлы проектов, описания классов компонентов, справочную систему, стили и платформенные артефакты.

#### Какие типы ресурсов хранятся в Bin?

- **Configs/** - конфигурационные файлы проектов и компонентов (XML)
- **ClDesc/** - описания классов компонентов (XML)
- **Help/** - справочная документация пользователя (HTML, RU/EN)
- **Styles/** - стили и темы для GUI (QSS, JSON)
- **Platform/** - платформенные артефакты сборки (Win/Linux)

### Конфигурации

#### Как создать конфигурационный файл проекта?

См. [Configs-Structure.md](Configs-Structure.md) для детального описания.

**Краткий ответ:**
Конфигурационный файл - это XML файл, описывающий структуру проекта, компоненты и их связи. Пример:

```xml
<Project>
  <Name>MyProject</Name>
  <Components>
    <Component Name="Source" Class="UMatrixSource">
      <Properties>
        <Property Name="FileName" Type="string">data.csv</Property>
      </Properties>
    </Component>
  </Components>
</Project>
```

#### Где хранятся конфигурационные файлы?

Конфигурационные файлы хранятся в `Bin/Configs/`. Они могут быть организованы по категориям:
- `Bin/Configs/User/` - пользовательские проекты
- `Bin/Configs/!OldConfigs/` - старые конфигурации

#### Как загрузить проект из конфигурационного файла?

Используйте `UProject::Load()`:
```cpp
RDK::UProject project;
if (project.Load("Bin/Configs/MyProject.xml")) {
    // Проект загружен
}
```

#### Как сохранить проект в конфигурационный файл?

Используйте `UProject::Save()`:
```cpp
project.Save("Bin/Configs/MyProject.xml");
```

### ClDesc (Описания классов)

#### Что такое ClDesc?

ClDesc - это XML описания классов компонентов, которые используются системой для регистрации и отображения компонентов в GUI.

#### Где хранятся ClDesc файлы?

ClDesc файлы хранятся в `Bin/ClDesc/`. Они автоматически загружаются при инициализации библиотек.

#### Как создать ClDesc для компонента?

ClDesc файл содержит метаданные о компоненте:
- Имя класса
- Описание
- Список свойств
- Категория

См. примеры существующих ClDesc файлов в `Bin/ClDesc/`.

### Справка (Help)

#### Где находится справочная система?

Справочная система находится в `Bin/Help/` и доступна на двух языках:
- `Bin/Help/ru/` - русская версия
- `Bin/Help/en/` - английская версия

#### Как открыть справку в приложении?

Справка доступна через меню Help в GUI приложении или через горячие клавиши.

#### Как обновить справку?

Отредактируйте HTML файлы в `Bin/Help/ru/` или `Bin/Help/en/`.

### Стили (Styles)

#### Где находятся стили GUI?

Стили находятся в `Bin/Styles/`:
- `*.qss` - файлы стилей Qt
- `theme.json` - описание тем

#### Как создать новую тему?

1. Создайте файл `theme.json` с описанием темы
2. Создайте соответствующий `.qss` файл
3. Загрузите тему через `UStyleManager`

См. [Docs/GUI/Style-System.md](../../Docs/GUI/Style-System.md) для детальной информации.

### Платформенные артефакты

#### Что находится в Platform/?

В `Bin/Platform/` находятся скомпилированные исполняемые файлы и библиотеки:
- `Bin/Platform/Win/` - Windows артефакты
- `Bin/Platform/Linux/` - Linux артефакты

#### Можно ли редактировать файлы в Platform/?

Нет, файлы в `Platform/` генерируются при сборке и не должны редактироваться вручную.

### Устранение неполадок

#### Проект не загружается из конфигурационного файла

- Проверьте корректность XML синтаксиса
- Убедитесь, что все указанные классы компонентов зарегистрированы
- Проверьте пути к файлам в конфигурации
- См. логи приложения для деталей ошибки

#### Компоненты не отображаются в GUI

- Проверьте наличие ClDesc файлов для компонентов
- Убедитесь, что библиотеки загружены
- Проверьте регистрацию компонентов в Storage

#### Стили не применяются

- Проверьте корректность синтаксиса QSS
- Убедитесь, что файлы стилей находятся в `Bin/Styles/`
- Проверьте загрузку темы через `UStyleManager`

### Дополнительные ресурсы

- [Configs-Structure.md](Configs-Structure.md) - детальное описание конфигураций
- [Help-Structure.md](Help-Structure.md) - структура справки
- [Docs/Components-And-Configuration/Configuration-Files-Overview.md](../../Docs/Components-And-Configuration/Configuration-Files-Overview.md) - обзор конфигураций
- [Docs/GUI/Style-System.md](../../Docs/GUI/Style-System.md) - система стилей

---

## EN

### General Questions

#### What is the Bin directory?

The `Bin/` directory contains resources and configurations necessary for the Nmsdk application to work. It includes project configuration files, component class descriptions, user help, styles, and platform artifacts.

#### What types of resources are stored in Bin?

- **Configs/** - project and component configuration files (XML)
- **ClDesc/** - component class descriptions (XML)
- **Help/** - user help documentation (HTML, RU/EN)
- **Styles/** - GUI styles and themes (QSS, JSON)
- **Platform/** - platform build artifacts (Win/Linux)

### Configurations

#### How do I create a project configuration file?

See [Configs-Structure.md](Configs-Structure.md) for detailed description.

**Quick answer:**
A configuration file is an XML file describing project structure, components, and their connections. Example:

```xml
<Project>
  <Name>MyProject</Name>
  <Components>
    <Component Name="Source" Class="UMatrixSource">
      <Properties>
        <Property Name="FileName" Type="string">data.csv</Property>
      </Properties>
    </Component>
  </Components>
</Project>
```

#### Where are configuration files stored?

Configuration files are stored in `Bin/Configs/`. They can be organized by categories:
- `Bin/Configs/User/` - user projects
- `Bin/Configs/!OldConfigs/` - old configurations

#### How do I load a project from a configuration file?

Use `UProject::Load()`:
```cpp
RDK::UProject project;
if (project.Load("Bin/Configs/MyProject.xml")) {
    // Project loaded
}
```

#### How do I save a project to a configuration file?

Use `UProject::Save()`:
```cpp
project.Save("Bin/Configs/MyProject.xml");
```

### ClDesc (Class Descriptions)

#### What is ClDesc?

ClDesc are XML descriptions of component classes used by the system to register and display components in the GUI.

#### Where are ClDesc files stored?

ClDesc files are stored in `Bin/ClDesc/`. They are automatically loaded when libraries are initialized.

#### How do I create ClDesc for a component?

A ClDesc file contains component metadata:
- Class name
- Description
- Property list
- Category

See examples of existing ClDesc files in `Bin/ClDesc/`.

### Help

#### Where is the help system located?

The help system is located in `Bin/Help/` and is available in two languages:
- `Bin/Help/ru/` - Russian version
- `Bin/Help/en/` - English version

#### How do I open help in the application?

Help is available through the Help menu in the GUI application or via keyboard shortcuts.

#### How do I update help?

Edit HTML files in `Bin/Help/ru/` or `Bin/Help/en/`.

### Styles

#### Where are GUI styles located?

Styles are located in `Bin/Styles/`:
- `*.qss` - Qt style files
- `theme.json` - theme descriptions

#### How do I create a new theme?

1. Create a `theme.json` file with theme description
2. Create corresponding `.qss` file
3. Load theme via `UStyleManager`

See [Docs/GUI/Style-System.md](../../Docs/GUI/Style-System.md) for detailed information.

### Platform Artifacts

#### What is in Platform/?

`Bin/Platform/` contains compiled executables and libraries:
- `Bin/Platform/Win/` - Windows artifacts
- `Bin/Platform/Linux/` - Linux artifacts

#### Can I edit files in Platform/?

No, files in `Platform/` are generated during build and should not be edited manually.

### Troubleshooting

#### Project doesn't load from configuration file

- Check XML syntax correctness
- Ensure all specified component classes are registered
- Check file paths in configuration
- See application logs for error details

#### Components don't appear in GUI

- Check for ClDesc files for components
- Ensure libraries are loaded
- Check component registration in Storage

#### Styles don't apply

- Check QSS syntax correctness
- Ensure style files are in `Bin/Styles/`
- Check theme loading via `UStyleManager`

### Additional Resources

- [Configs-Structure.md](Configs-Structure.md) - detailed configuration description
- [Help-Structure.md](Help-Structure.md) - help structure
- [Docs/Components-And-Configuration/Configuration-Files-Overview.md](../../Docs/Components-And-Configuration/Configuration-Files-Overview.md) - configuration overview
- [Docs/GUI/Style-System.md](../../Docs/GUI/Style-System.md) - style system

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

### CSNM модели (Компартментная спайковая модель нейрона)

#### Что такое CSNM?

CSNM (Compartmental Spiking Neuron Model) — это компартментная спайковая модель нейрона, которая учитывает пространственное распределение мембранного потенциала по дендритам и соме. В отличие от точечных моделей, CSNM позволяет моделировать пространственное распространение сигналов и влияние геометрических параметров нейрона на его поведение.

#### Какие компоненты используются для CSNM?

Основные компоненты кабельной модели в NMSDK:
- `NSynapseCable` — синапс для кабельной модели
- `NPulseChannelCable` — канал, реализующий кабельное уравнение
- `NPulseMembraneCable` — мембрана для кабельной модели
- `NPulseLTZoneCable` — низкопороговая зона для кабельной модели
- `NPulseNeuronCable` — нейрон на основе кабельной модели
- `NPulseNeuronCableMulti` — многокомпартментный нейрон

#### Какие пространственные параметры используются в CSNM?

Согласно [1], для точечной конфигурации идентифицированы следующие пространственные параметры:
- **Длина сегмента:** ~200 мкм (2·10⁻⁴ м)
- **Диаметр сегмента:** ~20 мкм (2·10⁻⁵ м)

Эти значения сопоставимы с биологическими данными.

#### Где найти документацию по CSNM?

См. [`Bin/Docs/SpikeSamples/CSNM-Models.md`](SpikeSamples/CSNM-Models.md) для детального описания CSNM моделей, кабельной теории и компонентов.

#### Какие конфигурации демонстрируют CSNM?

Примеры конфигураций:
- `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM` — базовая CSNM модель
- `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM_Nd` — CSNM с различным количеством дендритов
- `SpikeSamples/NM-Neurons/CableModel/CableNeuronMulti_CSNM_Nsyn` — CSNM с различным количеством синапсов

### Структурная адаптация

#### Что такое структурная адаптация?

Структурная адаптация — это метод автоматического подбора параметров компартментной спайковой модели нейрона в зависимости от заданного входного паттерна. В отличие от традиционных методов обучения, где изменяются только синаптические веса, структурная адаптация изменяет саму топологию нейрона: размер сомы, длину дендритов и количество синапсов на каждом дендрите.

#### Как работает структурная адаптация?

Процесс включает следующие этапы:
1. Анализ входного паттерна (временное кодирование)
2. Определение необходимой структуры нейрона
3. Автоматическое создание/модификация структуры
4. Обучение на заданном паттерне
5. Корректировка структуры при необходимости

#### Какой компонент реализует структурную адаптацию?

В NMSDK структурная адаптация реализована через компонент `NNeuronTrainer` из библиотеки `Nmsdk-PulseLib`.

#### Какие параметры влияют на структурную адаптацию?

Основные параметры:
- `MaxDendriteLength` — максимальная длина дендритов
- `LTZThreshold` — порог активации низкопороговой зоны
- `FixedLTZThreshold` — фиксированный порог активации
- `SpikesFrequency` — частота генерации спайков
- `InputPattern` — матрица входных паттернов

#### Где найти документацию по структурной адаптации?

См. [`Bin/Docs/SpikeSamples/StructuralAdaptation.md`](SpikeSamples/StructuralAdaptation.md) для детального описания метода структурной адаптации.

#### Какие конфигурации демонстрируют структурную адаптацию?

Примеры конфигураций:
- `SpikeSamples/StructTrain/SpikeTrainer` — базовое структурное обучение
- `SpikeSamples/StructTrain/SpikeAnsTrainer` — структурное обучение с ответами
- `SpikeSamples/StructTrain/XOR` — применение для задачи XOR

### Инкрементальное обучение

#### Что такое инкрементальное обучение?

Инкрементальное обучение позволяет обучать нейрон на новых образцах без необходимости хранить и переобучаться на всех предыдущих обучающих образцах. Это особенно важно для задач, где данные поступают последовательно или когда требуется адаптация к новым классам без потери знаний о старых классах.

#### Как работает инкрементальное обучение?

Процесс включает:
1. Инициализацию нейрона
2. Последовательное предъявление новых образцов
3. Адаптацию структуры и параметров под новый образец
4. Формирование новых классов при необходимости
5. Сохранение знаний о предыдущих классах без явного хранения всех образцов

#### Какие преимущества у инкрементального обучения?

Преимущества:
- **Эффективность памяти:** не требуется хранить все предыдущие образцы
- **Адаптивность:** возможность обучения на новых данных без полного переобучения
- **Масштабируемость:** возможность добавления новых классов без переобучения на всех данных
- **Биологическая реалистичность:** соответствует процессу обучения в биологических нейронных сетях

#### Где найти документацию по инкрементальному обучению?

См. [`Bin/Docs/SpikeSamples/IncrementalLearning.md`](SpikeSamples/IncrementalLearning.md) для детального описания стратегии инкрементального обучения.

#### Какие конфигурации демонстрируют инкрементальное обучение?

Примеры конфигураций:
- `SpikeSamples/Classifier/SpikeIrisClassifier` — классификация на Iris с инкрементальным обучением
- `SpikeSamples/StructTrain/SpikeTrainer` — базовое структурное обучение
- `SpikeSamples/StructTrain/SpikeAnsTrainer` — структурное обучение с ответами

### Классификация

#### Как применяется сегментная спайковая модель для классификации?

Сегментная спайковая модель нейрона со структурной адаптацией применяется для решения задач классификации, где требуется:
- Распознавание различных классов объектов
- Адаптация к новым классам без полного переобучения
- Эффективная обработка временных паттернов
- Работа в условиях ограниченных вычислительных ресурсов

#### Что такое временное кодирование?

Временное кодирование — это преобразование числовой информации в паттерны импульсов, где момент времени появления импульса несёт информацию о значении. Например, большее значение может кодироваться более ранним временем появления спайка.

#### Какие результаты получены на задачах классификации?

Согласно публикации [1]:
- **Iris:** сопоставимость результатов с классическими методами машинного обучения
- **MNIST:** применение временного кодирования для преобразования изображений в паттерны спайков
- **АНПА:** успешное применение для определения состояния телеуправляемого необитаемого подводного аппарата

#### Где найти документацию по классификации?

См. [`Bin/Docs/SpikeSamples/Classification.md`](SpikeSamples/Classification.md) для детального описания применения для задач классификации.

### Дополнительные ресурсы

- [Configs-Structure.md](Configs-Structure.md) - детальное описание конфигураций
- [Help-Structure.md](Help-Structure.md) - структура справки
- [Docs/Components-And-Configuration/Configuration-Files-Overview.md](../../Docs/Components-And-Configuration/Configuration-Files-Overview.md) - обзор конфигураций
- [Docs/GUI/Style-System.md](../../Docs/GUI/Style-System.md) - система стилей
- [SpikeSamples/Overview.md](SpikeSamples/Overview.md) - обзор конфигураций SpikeSamples
- [SpikeSamples/Index.md](SpikeSamples/Index.md) - индекс тематических разделов

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

## Literature
1. Демчева А.А. Разработка сегментной спайковой модели нейрона на основе кабельной теории для нейроморфных систем: выпускная квалификационная работа магистра. 2023. [онлайн](https://doi.org/10.18720/SPBPU/3/2023/vr/vr23-5657)

2. Korsakov, A. M., Astapova, L. A., Bakhshiev, A. V. Application of a compartmental spiking neuron model with structural adaptation for solving classification problems // Informatics and Automation, 2022, 21(3), 493-520. [DOI](https://doi.org/10.15622/ia.21.3.2)

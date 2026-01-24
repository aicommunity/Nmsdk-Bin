# Пример: Создание конфигурационного файла проекта

## RU

### Описание задачи

Создать конфигурационный файл проекта с несколькими компонентами и связями между ними.

### Решение

#### Пример 1: Простой проект с двумя компонентами

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Project>
    <Name>SimpleProject</Name>
    <Description>Простой проект с источником данных и обработчиком</Description>
    
    <Components>
        <!-- Источник данных -->
        <Component Name="DataSource" Class="UMatrixSource">
            <Properties>
                <Property Name="FileName" Type="string">data.csv</Property>
                <Property Name="AutoLoad" Type="bool">true</Property>
            </Properties>
        </Component>
        
        <!-- Обработчик данных -->
        <Component Name="Processor" Class="UStatistic">
            <Properties>
                <Property Name="InputData" Type="link">DataSource.OutputMatrix</Property>
                <Property Name="CalculateMean" Type="bool">true</Property>
                <Property Name="CalculateStdDev" Type="bool">true</Property>
            </Properties>
        </Component>
    </Components>
    
    <Settings>
        <Setting Name="AutoStart" Type="bool">false</Setting>
        <Setting Name="MaxIterations" Type="int">1000</Setting>
    </Settings>
</Project>
```

#### Пример 2: Проект с сетью компонентов

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Project>
    <Name>NetworkProject</Name>
    
    <Components>
        <!-- Источник 1 -->
        <Component Name="Source1" Class="UMatrixSource">
            <Properties>
                <Property Name="FileName" Type="string">input1.csv</Property>
            </Properties>
        </Component>
        
        <!-- Источник 2 -->
        <Component Name="Source2" Class="UMatrixSource">
            <Properties>
                <Property Name="FileName" Type="string">input2.csv</Property>
            </Properties>
        </Component>
        
        <!-- Обработчик 1 -->
        <Component Name="Processor1" Class="UStatistic">
            <Properties>
                <Property Name="InputData" Type="link">Source1.OutputMatrix</Property>
            </Properties>
        </Component>
        
        <!-- Обработчик 2 -->
        <Component Name="Processor2" Class="UStatistic">
            <Properties>
                <Property Name="InputData" Type="link">Source2.OutputMatrix</Property>
            </Properties>
        </Component>
        
        <!-- Агрегатор результатов -->
        <Component Name="Aggregator" Class="UIO">
            <Properties>
                <Property Name="Input1" Type="link">Processor1.Output</Property>
                <Property Name="Input2" Type="link">Processor2.Output</Property>
                <Property Name="OutputFile" Type="string">result.txt</Property>
            </Properties>
        </Component>
    </Components>
</Project>
```

#### Пример 3: Проект с контейнером компонентов

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Project>
    <Name>ContainerProject</Name>
    
    <Components>
        <!-- Контейнер с подкомпонентами -->
        <Component Name="MainContainer" Class="UNet">
            <Properties>
                <Property Name="Name" Type="string">Main Processing Network</Property>
            </Properties>
            
            <SubComponents>
                <!-- Подкомпонент 1 -->
                <Component Name="SubComponent1" Class="UMatrixSource">
                    <Properties>
                        <Property Name="FileName" Type="string">data1.csv</Property>
                    </Properties>
                </Component>
                
                <!-- Подкомпонент 2 -->
                <Component Name="SubComponent2" Class="UStatistic">
                    <Properties>
                        <Property Name="InputData" Type="link">SubComponent1.OutputMatrix</Property>
                    </Properties>
                </Component>
            </SubComponents>
        </Component>
        
        <!-- Внешний компонент -->
        <Component Name="Output" Class="UIO">
            <Properties>
                <Property Name="Input" Type="link">MainContainer.SubComponent2.Output</Property>
            </Properties>
        </Component>
    </Components>
</Project>
```

### Объяснение структуры

1. **Корневой элемент `<Project>`** - содержит весь проект
2. **`<Name>`** - имя проекта
3. **`<Components>`** - список компонентов проекта
4. **`<Component>`** - описание одного компонента
   - `Name` - имя компонента в проекте
   - `Class` - класс компонента
5. **`<Properties>`** - свойства компонента
   - `Type="link"` - связь с другим компонентом
   - `Type="string"` - строковое значение
   - `Type="bool"` - булево значение
   - `Type="int"` - целое число
   - `Type="double"` - число с плавающей точкой

### Создание связей

Связи создаются через свойства типа `link`:
```xml
<Property Name="InputData" Type="link">SourceComponent.OutputProperty</Property>
```

Формат: `ИмяКомпонента.ИмяСвойства`

### Загрузка проекта

```cpp
#include "Rdk/Core/Application/UProject.h"

RDK::UProject project;
if (project.Load("Bin/Configs/MyProject.xml")) {
    // Проект успешно загружен
    // Компоненты созданы и настроены
} else {
    // Ошибка загрузки
}
```

### Сохранение проекта

```cpp
// После создания и настройки проекта
project.Save("Bin/Configs/MyProject.xml");
```

### Связанная документация

- [Configs-Structure.md](../Configs-Structure.md) - детальное описание структуры
- [Docs/Components-And-Configuration/Configuration-Files-Overview.md](../../../Docs/Components-And-Configuration/Configuration-Files-Overview.md) - обзор конфигураций

---

## EN

### Task Description

Create a project configuration file with multiple components and connections between them.

### Solution

#### Example 1: Simple Project with Two Components

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Project>
    <Name>SimpleProject</Name>
    <Description>Simple project with data source and processor</Description>
    
    <Components>
        <!-- Data source -->
        <Component Name="DataSource" Class="UMatrixSource">
            <Properties>
                <Property Name="FileName" Type="string">data.csv</Property>
                <Property Name="AutoLoad" Type="bool">true</Property>
            </Properties>
        </Component>
        
        <!-- Data processor -->
        <Component Name="Processor" Class="UStatistic">
            <Properties>
                <Property Name="InputData" Type="link">DataSource.OutputMatrix</Property>
                <Property Name="CalculateMean" Type="bool">true</Property>
                <Property Name="CalculateStdDev" Type="bool">true</Property>
            </Properties>
        </Component>
    </Components>
    
    <Settings>
        <Setting Name="AutoStart" Type="bool">false</Setting>
        <Setting Name="MaxIterations" Type="int">1000</Setting>
    </Settings>
</Project>
```

#### Example 2: Project with Component Network

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Project>
    <Name>NetworkProject</Name>
    
    <Components>
        <!-- Source 1 -->
        <Component Name="Source1" Class="UMatrixSource">
            <Properties>
                <Property Name="FileName" Type="string">input1.csv</Property>
            </Properties>
        </Component>
        
        <!-- Source 2 -->
        <Component Name="Source2" Class="UMatrixSource">
            <Properties>
                <Property Name="FileName" Type="string">input2.csv</Property>
            </Properties>
        </Component>
        
        <!-- Processor 1 -->
        <Component Name="Processor1" Class="UStatistic">
            <Properties>
                <Property Name="InputData" Type="link">Source1.OutputMatrix</Property>
            </Properties>
        </Component>
        
        <!-- Processor 2 -->
        <Component Name="Processor2" Class="UStatistic">
            <Properties>
                <Property Name="InputData" Type="link">Source2.OutputMatrix</Property>
            </Properties>
        </Component>
        
        <!-- Result aggregator -->
        <Component Name="Aggregator" Class="UIO">
            <Properties>
                <Property Name="Input1" Type="link">Processor1.Output</Property>
                <Property Name="Input2" Type="link">Processor2.Output</Property>
                <Property Name="OutputFile" Type="string">result.txt</Property>
            </Properties>
        </Component>
    </Components>
</Project>
```

#### Example 3: Project with Component Container

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Project>
    <Name>ContainerProject</Name>
    
    <Components>
        <!-- Container with subcomponents -->
        <Component Name="MainContainer" Class="UNet">
            <Properties>
                <Property Name="Name" Type="string">Main Processing Network</Property>
            </Properties>
            
            <SubComponents>
                <!-- Subcomponent 1 -->
                <Component Name="SubComponent1" Class="UMatrixSource">
                    <Properties>
                        <Property Name="FileName" Type="string">data1.csv</Property>
                    </Properties>
                </Component>
                
                <!-- Subcomponent 2 -->
                <Component Name="SubComponent2" Class="UStatistic">
                    <Properties>
                        <Property Name="InputData" Type="link">SubComponent1.OutputMatrix</Property>
                    </Properties>
                </Component>
            </SubComponents>
        </Component>
        
        <!-- External component -->
        <Component Name="Output" Class="UIO">
            <Properties>
                <Property Name="Input" Type="link">MainContainer.SubComponent2.Output</Property>
            </Properties>
        </Component>
    </Components>
</Project>
```

### Structure Explanation

1. **Root element `<Project>`** - contains entire project
2. **`<Name>`** - project name
3. **`<Components>`** - list of project components
4. **`<Component>`** - description of one component
   - `Name` - component name in project
   - `Class` - component class
5. **`<Properties>`** - component properties
   - `Type="link"` - connection to another component
   - `Type="string"` - string value
   - `Type="bool"` - boolean value
   - `Type="int"` - integer
   - `Type="double"` - floating point number

### Creating Links

Links are created through properties of type `link`:
```xml
<Property Name="InputData" Type="link">SourceComponent.OutputProperty</Property>
```

Format: `ComponentName.PropertyName`

### Loading Project

```cpp
#include "Rdk/Core/Application/UProject.h"

RDK::UProject project;
if (project.Load("Bin/Configs/MyProject.xml")) {
    // Project successfully loaded
    // Components created and configured
} else {
    // Load error
}
```

### Saving Project

```cpp
// After creating and configuring project
project.Save("Bin/Configs/MyProject.xml");
```

### Related Documentation

- [Configs-Structure.md](../Configs-Structure.md) - detailed structure description
- [Docs/Components-And-Configuration/Configuration-Files-Overview.md](../../../Docs/Components-And-Configuration/Configuration-Files-Overview.md) - configuration overview

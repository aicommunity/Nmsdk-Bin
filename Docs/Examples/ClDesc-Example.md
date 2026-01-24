# Пример: Создание ClDesc для компонента

## RU

### Описание задачи

Создать ClDesc (описание класса) для компонента, чтобы он отображался в GUI и имел правильные метаданные.

### Решение

#### Пример ClDesc файла

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ClassDescription>
    <ClassName>UMultiplier</ClassName>
    <DisplayName>Multiplier</DisplayName>
    <Category>Basic</Category>
    <Description>Компонент для умножения входного значения на параметр</Description>
    
    <Properties>
        <Property>
            <Name>Input</Name>
            <Type>double</Type>
            <Direction>Input</Direction>
            <Description>Входное значение</Description>
            <DefaultValue>0.0</DefaultValue>
        </Property>
        
        <Property>
            <Name>Output</Name>
            <Type>double</Type>
            <Direction>Output</Direction>
            <Description>Результат умножения</Description>
        </Property>
        
        <Property>
            <Name>Multiplier</Name>
            <Type>double</Type>
            <Direction>Parameter</Direction>
            <Description>Множитель</Description>
            <DefaultValue>1.0</DefaultValue>
            <MinValue>0.0</MinValue>
            <MaxValue>100.0</MaxValue>
        </Property>
    </Properties>
    
    <Icon>multiplier.png</Icon>
    <Color>#4CAF50</Color>
</ClassDescription>
```

### Объяснение структуры

1. **`<ClassName>`** - имя класса компонента в коде
2. **`<DisplayName>`** - отображаемое имя в GUI
3. **`<Category>`** - категория для группировки в библиотеке компонентов
4. **`<Description>`** - описание компонента
5. **`<Properties>`** - список свойств компонента
   - `Name` - имя свойства
   - `Type` - тип данных
   - `Direction` - направление (Input, Output, Parameter, State)
   - `Description` - описание свойства
   - `DefaultValue` - значение по умолчанию
   - `MinValue` / `MaxValue` - ограничения для параметров

### Размещение файла

ClDesc файл должен быть размещен в `Bin/ClDesc/` с именем, соответствующим классу компонента:
- `Bin/ClDesc/UMultiplier.xml`

### Загрузка ClDesc

ClDesc файлы автоматически загружаются при инициализации библиотек через `UStorage::LoadClassesDescription()`.

### Связанная документация

- [Configs-Structure.md](../Configs-Structure.md) - структура конфигураций
- [Docs/Components-And-Configuration/Component-System.md](../../../Docs/Components-And-Configuration/Component-System.md) - компонентная система

---

## EN

### Task Description

Create ClDesc (class description) for a component so it appears in GUI and has correct metadata.

### Solution

#### Example ClDesc File

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ClassDescription>
    <ClassName>UMultiplier</ClassName>
    <DisplayName>Multiplier</DisplayName>
    <Category>Basic</Category>
    <Description>Component for multiplying input value by parameter</Description>
    
    <Properties>
        <Property>
            <Name>Input</Name>
            <Type>double</Type>
            <Direction>Input</Direction>
            <Description>Input value</Description>
            <DefaultValue>0.0</DefaultValue>
        </Property>
        
        <Property>
            <Name>Output</Name>
            <Type>double</Type>
            <Direction>Output</Direction>
            <Description>Multiplication result</Description>
        </Property>
        
        <Property>
            <Name>Multiplier</Name>
            <Type>double</Type>
            <Direction>Parameter</Direction>
            <Description>Multiplier</Description>
            <DefaultValue>1.0</DefaultValue>
            <MinValue>0.0</MinValue>
            <MaxValue>100.0</MaxValue>
        </Property>
    </Properties>
    
    <Icon>multiplier.png</Icon>
    <Color>#4CAF50</Color>
</ClassDescription>
```

### Structure Explanation

1. **`<ClassName>`** - component class name in code
2. **`<DisplayName>`** - display name in GUI
3. **`<Category>`** - category for grouping in component library
4. **`<Description>`** - component description
5. **`<Properties>`** - list of component properties
   - `Name` - property name
   - `Type` - data type
   - `Direction` - direction (Input, Output, Parameter, State)
   - `Description` - property description
   - `DefaultValue` - default value
   - `MinValue` / `MaxValue` - constraints for parameters

### File Placement

ClDesc file should be placed in `Bin/ClDesc/` with name matching component class:
- `Bin/ClDesc/UMultiplier.xml`

### Loading ClDesc

ClDesc files are automatically loaded when libraries are initialized via `UStorage::LoadClassesDescription()`.

### Related Documentation

- [Configs-Structure.md](../Configs-Structure.md) - configuration structure
- [Docs/Components-And-Configuration/Component-System.md](../../../Docs/Components-And-Configuration/Component-System.md) - component system

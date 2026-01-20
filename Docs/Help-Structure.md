# Структура справочной системы (Help Structure)

## RU

### Обзор

Справочная система пользователя находится в `Bin/Help/` и доступна на двух языках: русском и английском.

### Структура

```
Bin/Help/
├── en/          # Английская версия
│   ├── index.html
│   ├── getting-started.html
│   ├── components.html
│   └── ...
├── ru/          # Русская версия
│   ├── index.html
│   ├── getting-started.html
│   ├── components.html
│   └── ...
└── styles/      # Стили для справки
    └── help.css
```

### Основные разделы

- **getting-started.html** - начало работы
- **components.html** - описание компонентов
- **class-editor.html** - редактор классов
- **components-list-widget.html** - список компонентов
- **component-property-editor.html** - редактор свойств
- **modern-diagram.html** - редактор диаграмм
- **logger-widget.html** - окно логов
- **graph-widget.html** - окно графиков
- **keyboard-shortcuts.html** - горячие клавиши

### См. также

- [GUI/Widgets-Reference.md](../../Docs/GUI/Widgets-Reference.md) - справочник виджетов

---

## EN

### Overview

The user help system is located in `Bin/Help/` and is available in two languages: Russian and English.

### Structure

```
Bin/Help/
├── en/          # English version
│   ├── index.html
│   ├── getting-started.html
│   ├── components.html
│   └── ...
├── ru/          # Russian version
│   ├── index.html
│   ├── getting-started.html
│   ├── components.html
│   └── ...
└── styles/      # Shared help styles
    └── help.css
```

### Main Sections

- **getting-started.html** - getting started guide
- **components.html** - component overview and usage
- **class-editor.html** - class editor guide
- **components-list-widget.html** - components list widget
- **component-property-editor.html** - component property editor
- **modern-diagram.html** - modern diagram editor
- **logger-widget.html** - logger window
- **graph-widget.html** - graph window
- **keyboard-shortcuts.html** - keyboard shortcuts

### See Also

- [GUI/Widgets-Reference.md](../../Docs/GUI/Widgets-Reference.md) - widgets reference

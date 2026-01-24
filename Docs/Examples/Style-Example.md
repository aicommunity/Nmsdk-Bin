# Пример: Создание темы и стилей

## RU

### Описание задачи

Создать новую тему для GUI приложения с кастомными стилями.

### Решение

#### Шаг 1: Создание theme.json

Создайте файл `Bin/Styles/MyTheme/theme.json`:

```json
{
    "name": "MyTheme",
    "displayName": "My Custom Theme",
    "version": "1.0",
    "description": "Пользовательская тема с темным фоном",
    "qssFile": "style.qss",
    "colors": {
        "primary": "#2196F3",
        "secondary": "#FF9800",
        "background": "#1E1E1E",
        "foreground": "#FFFFFF",
        "accent": "#4CAF50"
    },
    "fonts": {
        "default": "Arial",
        "monospace": "Courier New",
        "size": 10
    }
}
```

#### Шаг 2: Создание QSS файла

Создайте файл `Bin/Styles/MyTheme/style.qss`:

```css
/* Основные стили */
QMainWindow {
    background-color: #1E1E1E;
    color: #FFFFFF;
}

/* Кнопки */
QPushButton {
    background-color: #2196F3;
    color: #FFFFFF;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

/* Поля ввода */
QLineEdit, QTextEdit {
    background-color: #2D2D2D;
    color: #FFFFFF;
    border: 1px solid #3D3D3D;
    border-radius: 4px;
    padding: 4px;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #2196F3;
}

/* Меню */
QMenuBar {
    background-color: #252525;
    color: #FFFFFF;
}

QMenu {
    background-color: #2D2D2D;
    color: #FFFFFF;
    border: 1px solid #3D3D3D;
}

QMenu::item:selected {
    background-color: #2196F3;
}

/* Списки */
QListWidget, QTreeWidget {
    background-color: #1E1E1E;
    color: #FFFFFF;
    border: 1px solid #3D3D3D;
}

QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #2196F3;
    color: #FFFFFF;
}
```

#### Шаг 3: Загрузка темы

```cpp
#include "Rdk/GUI/Qt/UStyleManager.h"

// Загрузка темы
RDK::UStyleManager* styleManager = RDK::UStyleManager::Instance();
if (styleManager->loadTheme("Bin/Styles/MyTheme/theme.json")) {
    // Тема успешно загружена
} else {
    // Ошибка загрузки темы
}
```

### Использование цветов из theme.json

Цвета, определенные в `theme.json`, доступны через `UStyleManager`:

```cpp
QColor primaryColor = styleManager->getColor("primary");
QColor backgroundColor = styleManager->getColor("background");
```

### Объяснение ключевых моментов

1. **theme.json** - метаданные темы (имя, версия, цвета, шрифты)
2. **QSS файл** - стили Qt для элементов интерфейса
3. **Загрузка** - тема загружается через `UStyleManager::loadTheme()`
4. **Применение** - стили применяются автоматически после загрузки

### Связанная документация

- [Docs/GUI/Style-System.md](../../../Docs/GUI/Style-System.md) - детальное описание системы стилей
- [Docs/GUI/Widgets-Reference.md](../../../Docs/GUI/Widgets-Reference.md) - справочник виджетов

---

## EN

### Task Description

Create a new theme for GUI application with custom styles.

### Solution

#### Step 1: Create theme.json

Create file `Bin/Styles/MyTheme/theme.json`:

```json
{
    "name": "MyTheme",
    "displayName": "My Custom Theme",
    "version": "1.0",
    "description": "Custom theme with dark background",
    "qssFile": "style.qss",
    "colors": {
        "primary": "#2196F3",
        "secondary": "#FF9800",
        "background": "#1E1E1E",
        "foreground": "#FFFFFF",
        "accent": "#4CAF50"
    },
    "fonts": {
        "default": "Arial",
        "monospace": "Courier New",
        "size": 10
    }
}
```

#### Step 2: Create QSS File

Create file `Bin/Styles/MyTheme/style.qss`:

```css
/* Main styles */
QMainWindow {
    background-color: #1E1E1E;
    color: #FFFFFF;
}

/* Buttons */
QPushButton {
    background-color: #2196F3;
    color: #FFFFFF;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

/* Input fields */
QLineEdit, QTextEdit {
    background-color: #2D2D2D;
    color: #FFFFFF;
    border: 1px solid #3D3D3D;
    border-radius: 4px;
    padding: 4px;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #2196F3;
}

/* Menu */
QMenuBar {
    background-color: #252525;
    color: #FFFFFF;
}

QMenu {
    background-color: #2D2D2D;
    color: #FFFFFF;
    border: 1px solid #3D3D3D;
}

QMenu::item:selected {
    background-color: #2196F3;
}

/* Lists */
QListWidget, QTreeWidget {
    background-color: #1E1E1E;
    color: #FFFFFF;
    border: 1px solid #3D3D3D;
}

QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #2196F3;
    color: #FFFFFF;
}
```

#### Step 3: Load Theme

```cpp
#include "Rdk/GUI/Qt/UStyleManager.h"

// Load theme
RDK::UStyleManager* styleManager = RDK::UStyleManager::Instance();
if (styleManager->loadTheme("Bin/Styles/MyTheme/theme.json")) {
    // Theme successfully loaded
} else {
    // Theme load error
}
```

### Using Colors from theme.json

Colors defined in `theme.json` are available through `UStyleManager`:

```cpp
QColor primaryColor = styleManager->getColor("primary");
QColor backgroundColor = styleManager->getColor("background");
```

### Key Points Explanation

1. **theme.json** - theme metadata (name, version, colors, fonts)
2. **QSS file** - Qt styles for interface elements
3. **Loading** - theme loaded via `UStyleManager::loadTheme()`
4. **Application** - styles applied automatically after loading

### Related Documentation

- [Docs/GUI/Style-System.md](../../../Docs/GUI/Style-System.md) - detailed style system description
- [Docs/GUI/Widgets-Reference.md](../../../Docs/GUI/Widgets-Reference.md) - widgets reference

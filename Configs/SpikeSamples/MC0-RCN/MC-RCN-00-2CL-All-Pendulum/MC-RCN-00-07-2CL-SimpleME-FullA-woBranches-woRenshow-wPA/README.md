## MC-RCN-00-07-2CL-SimpleME-FullA-woBranches-woRenshow-wPA — двухуровневый рефлекторный контур с маятником

**Путь:** `Bin/Configs/SpikeSamples/MC0-RCN/MC-RCN-00-2CL-All-Pendulum/MC-RCN-00-07-2CL-SimpleME-FullA-woBranches-woRenshow-wPA`  
**Статус валидации:** VALID (см. `Reports/SpikeSamples-Validation-Report.md`)

### Назначение конфигурации

Эта конфигурация демонстрирует **двухуровневый рефлекторный контур (RCN)** для управления маятником с двумя контурами управления:
- Простой двигательный элемент (SimpleME), Полная афферентация (FullA), Без ветвления (woBranches), Без клеток Реншоу (woRenshow), С пресинаптическим торможением (wPA)
- **Двухуровневая структура (2CL)** — два контура управления (например, по углу и скорости)
- **Модель маятника** — использование маятника вместо DC-двигателя в качестве объекта управления

Согласно [A] и `MuscleControlStructures.md`, двухуровневые контуры обеспечивают более точное управление за счёт использования нескольких сенсорных сигналов. Данная конфигурация аналогична `MC-RCN-00-07-2CL-SimpleME-FullA-woBranches-woRenshow-wPA` из группы `MC-RCN-00-2CL-All-DcEngine`, но использует модель маятника вместо DC-двигателя.

### Отличия от других конфигураций

Данная конфигурация отличается:
- От `MC-RCN-00-07-1CL-SimpleME-FullA-woBranches-woRenshow-wPA` из группы `MC-RCN-00-1CL-All-Pendulum`: использованием двух контуров управления (2CL вместо 1CL)
- От `MC-RCN-00-07-2CL-SimpleME-FullA-woBranches-woRenshow-wPA` из группы `MC-RCN-00-2CL-All-DcEngine`: использованием модели маятника вместо DC-двигателя

### Структура двухуровневого рефлекторного контура

Двухуровневый рефлекторный контур содержит два контура управления, каждый из которых обрабатывает свой сенсорный сигнал от маятника и формирует управляющее воздействие. Контуры могут работать параллельно или последовательно, обеспечивая более точное управление маятником.

### Связанные материалы

- Теория и функциональное описание:
  - [`Bin/Docs/SpikeSamples/MuscleControlStructures.md`](../../../../../Docs/SpikeSamples/MuscleControlStructures.md) — нейронные структуры управления мышечным сокращением
- Описание конфигурации:
  - `Description.rtf` — подробное описание конфигурации (в формате RTF)
- Групповой README:
  - [`README.md`](../README.md) — общее описание группы конфигураций
- Аналогичные конфигурации:
  - [`../MC-RCN-00-1CL-All-Pendulum/MC-RCN-00-07-1CL-SimpleME-FullA-woBranches-woRenshow-wPA/README.md`](../../MC-RCN-00-1CL-All-Pendulum/MC-RCN-00-07-1CL-SimpleME-FullA-woBranches-woRenshow-wPA/README.md) — одноуровневая конфигурация с маятником
  - [`../MC-RCN-00-2CL-All-DcEngine/MC-RCN-00-07-2CL-SimpleME-FullA-woBranches-woRenshow-wPA/README.md`](../../MC-RCN-00-2CL-All-DcEngine/MC-RCN-00-07-2CL-SimpleME-FullA-woBranches-woRenshow-wPA/README.md) — двухуровневая конфигурация с DC-двигателем

## Литература

1. [27] Нейроморфные системы управления на основе модели импульсного нейрона со структурной адаптацией: диссертация на соискание ученой степени кандидата технических наук. [онлайн](https://www.elibrary.ru/item.asp?id=54445157)

2. [31] Моделирование нейронных структур управления мышечным сокращением. Схемы нейронных сетей. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=29:1&catid=67&lang=ru&Itemid=676)

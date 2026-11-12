## MC-RCN-00-05-1CL-TS-SimpleME-SimpleA-wBranches-woRenshow-wPA — одноуровневый рефлекторный контур с TS-SimpleME и ветвлением

**Путь:** `Bin/Configs/SpikeSamples/MC0-RCN/MC-RCN-00-1CL-All-DcEngine/MC-RCN-00-05-1CL-TS-SimpleME-SimpleA-wBranches-woRenshow-wPA`
**Статус валидации:** VALID (см. `Reports/SpikeSamples-Validation-Report.md`)

### Назначение конфигурации

Эта конфигурация демонстрирует **одноуровневый рефлекторный контур (RCN)** для управления DC-двигателем с двигательным элементом типа TS и ветвлением:
- Двигательный элемент типа TS (TS-SimpleME)
- Простая афферентация (SimpleA)
- **С ветвлением афферентных путей (wBranches)** — отличие от MC-RCN-00-04
- Без клеток Реншоу (woRenshow)
- С пресинаптическим торможением (wPA)

Согласно [A] и `MuscleControlStructures.md`, комбинация TS-SimpleME с ветвлением афферентных путей позволяет изучать влияние обоих факторов на работу рефлекторных контуров.

### Отличия от других конфигураций

Данная конфигурация отличается от `MC-RCN-00-04` наличием ветвления афферентных путей (wBranches). Комбинация TS-SimpleME с ветвлением:
- Улучшает пространственную суммацию сигналов
- Позволяет более сложную обработку афферентной информации
- Может влиять на характеристики управления в сочетании с типом TS

### Связанные материалы

- Теория и функциональное описание:
  - [`Bin/Docs/SpikeSamples/MuscleControlStructures.md`](../../../../../Docs/SpikeSamples/MuscleControlStructures.md) — нейронные структуры управления мышечным сокращением
- Описание конфигурации:
  - `Description.rtf` — подробное описание конфигурации (в формате RTF)
- Групповой README:
  - [`README.md`](../README.md) — общее описание группы конфигураций
- Связанные конфигурации:
  - `MC-RCN-00-04-1CL-TS-SimpleME-SimpleA-woBranches-woRenshow-wPA` — TS-SimpleME без ветвления
  - `MC-RCN-00-06-1CL-TS-SimpleME-SimpleA-woBranches-wRenshow-wPA` — TS-SimpleME с клетками Реншоу

## Литература

1. [27] Нейроморфные системы управления на основе модели импульсного нейрона со структурной адаптацией: диссертация на соискание ученой степени кандидата технических наук. [онлайн](https://www.elibrary.ru/item.asp?id=54445157)

2. [31] Моделирование нейронных структур управления мышечным сокращением. Схемы нейронных сетей. [онлайн](https://neuromodeler.ru/index.php?option=com_content&view=article&id=29:1&catid=67&lang=ru&Itemid=676)

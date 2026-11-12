# Пример: ClDesc (описание класса)

## RU

### Назначение

XML-метаданные компонента для GUI NeuroModeler: заголовки, описания свойств, избранные свойства (Favorites) и алиасы вложенных портов.

**Путь файла:** `Bin/ClDesc/<Library>/ru-RU/<ClassName>.xml`  
**Загрузка:** `UStorage::LoadClassesDescription()`  
**Методология DETAILED:** `Docs/ClDesc-Detailed-Methodology.md` (корень репозитория)

### Реальная схема (фрагмент)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ClassDescription>
	<ClassName>UNoiseGen</ClassName>
	<Header>генераторы шума (Rdk-BasicLib)</Header>
	<Description>Генератор аддитивного шума для матриц. Primary-параметры — уровень шума и I/O.</Description>
	<Properties>
		<NoiseLevel>
			<Header>Уровень шума</Header>
			<Description>Амплитуда добавляемого шума относительно входных данных.</Description>
			<Type>| ptPubParameter |</Type>
			<DataSelectionType>0</DataSelectionType>
			<ValueList Type="std::vector" Size="2" elemType="std::string">
				<elem Type="std::string"></elem>
				<elem Type="std::string"></elem>
			</ValueList>
			<PropertyType>257</PropertyType>
		</NoiseLevel>
		<InputParams>
			<Header>Входные данные</Header>
			<Description>Матрица или вектор, к которому добавляется шум.</Description>
			<Type>| ptPubInput |</Type>
			<DataSelectionType>0</DataSelectionType>
			<ValueList Type="std::vector" Size="2" elemType="std::string">
				<elem Type="std::string"></elem>
				<elem Type="std::string"></elem>
			</ValueList>
			<PropertyType>264</PropertyType>
		</InputParams>
		<OutputParams>
			<Header>Выходные данные</Header>
			<Description>Результат: вход + шум.</Description>
			<Type>| ptPubOutput |</Type>
			<DataSelectionType>0</DataSelectionType>
			<ValueList Type="std::vector" Size="2" elemType="std::string">
				<elem Type="std::string"></elem>
				<elem Type="std::string"></elem>
			</ValueList>
			<PropertyType>272</PropertyType>
		</OutputParams>
		<!-- Activity, Coord, Name, TimeStep, … — secondary; в Favorites не включать -->
	</Properties>
	<Favorites>
		<NoiseLevel>
			<Path>{CompName}:NoiseLevel</Path>
		</NoiseLevel>
		<InputParams>
			<Path>{CompName}:InputParams</Path>
		</InputParams>
		<OutputParams>
			<Path>{CompName}:OutputParams</Path>
		</OutputParams>
	</Favorites>
</ClassDescription>
```

### Поля

| Поле | Смысл |
|------|--------|
| `ClassName` | Имя класса в `UStorage` |
| `Header` / `Description` | Заголовок и описание класса |
| `Properties/<PropName>/…` | Имя узла = имя свойства |
| `Header` / `Description` (свойства) | UI-заголовок и поведение |
| `Type` | Текстовые флаги (`\| ptPubParameter \|` …) |
| `PropertyType` | Числовая маска (257 = ptPubParameter, 264 = ptPubInput, 272 = ptPubOutput, …) |
| `DataSelectionType` | Виджет редактора (0…4) |
| `ValueList` / `Step` | Подсказки UI; `Step` при типе 4 |
| `Favorites/<Name>/Path` | Direct: `{CompName}:Prop` или `Prop`; Alias: `Nested.Path.Prop` |

### Favorites: primary vs alias

- **Direct (primary):** `Path` без точки — закладка на своё свойство; в GUI без пометки `[Alias]`.
- **Alias:** `Path` содержит `.` — порт вложенного компонента; GUI помечает `[Alias]`.

```xml
<Favorites>
	<Frequency>
		<Path>{CompName}:Frequency</Path>
	</Frequency>
	<LTZoneOutput>
		<Path>LTZone.Output</Path>
	</LTZoneOutput>
</Favorites>
```

Не класть в Favorites: `Activity`, `Coord`, `Name`, `Id`, `TimeStep`, debug/duration, а также nested `*.Coord` / `*.Activity` / `*.Type`.

### Автоген vs DETAILED

`NeuroModelerConsole --generate-cldesc` создаёт каркас и (для `UNet`) сырые aliases. Курация primary Favorites и смысловых Description — **вручную** (XML или ClDesc Editor). Не запускать массовый `-F` после ручной курации Favorites.

### См. также

- `Docs/ClDesc-Detailed-Methodology.md`
- `Docs/PropertyAliasGeneration.md`
- [Configs-Structure.md](../Configs-Structure.md)

---

## EN

ClDesc XML lives at `Bin/ClDesc/<Library>/ru-RU/<Class>.xml`. Real schema uses `Header`/`Description`/`PropertyType`/`Favorites/Path` — not the old fictional `DisplayName`/`Category`/`Direction` fields. Direct Favorites use `{CompName}:Prop`; aliases use dotted nested paths. See RU section and `Docs/ClDesc-Detailed-Methodology.md`.

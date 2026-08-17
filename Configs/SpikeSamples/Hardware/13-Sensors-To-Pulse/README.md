# Hardware test: Sensors to network

**Путь:** `Bin/Configs/SpikeSamples/Hardware/13-Sensors-To-Pulse`

Общий HOWTO Firmata: [LAB-Firmata.md](../LAB-Firmata.md).

## Назначение

DeviceIO потенциометр A0 и кнопка D2. Результат — `Pot.Value` / `Btn.Value` в инспекторе и Monitor.

## BOM

Плата + USB + потенциометр + тактовая кнопка.

## Проводка

Потенциометр: крайние выводы на 5V и GND, средний (wiper) на **A0**. См. [Analog Input](https://docs.arduino.cc/built-in-examples/analog/AnalogInput/) (Arduino docs, CC BY-SA 4.0). Кнопка на **D2**: один контакт на D2, второй на GND; либо D2–кнопка–5V с подтяжкой. См. [Button](https://docs.arduino.cc/built-in-examples/digital/Button/) (Arduino docs, CC BY-SA 4.0).

![Arduino Mega 2560 Rev3](../_shared/media/Arduino_MEGA2560.png)

*Arduino, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Arduino_MEGA2560.png). Pinout PDF: [Mega A000067](../_shared/media/A000067-full-pinout.pdf) / [Uno A000066](../_shared/media/A000066-full-pinout.pdf) (Arduino, CC BY-SA 4.0).*


## Перед запуском

1. Подключите плату по USB. По умолчанию генератор пишет `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
2. Откройте `Project.ini` в NeuroModeler.
3. Клик по узлу **Firmata** (или Board) → вкладки **Assembly** / **Pinout** / **Pins** / **Monitor** / **Board**.
4. **Upload** bundled `standard_firmata` (если ещё не прошито) → **Connect** → дождитесь `FirmataReady`.
5. Для DeviceIO: **ApplyConfig**, затем Continuous / Calculate.

## Компоненты

- `Firmata` + `Pot` + `Btn`.

## Схема Assembly

Pot A0 и button D2 на Assembly (JSON 09 также содержит servo — на схеме щита).

## Критерий успеха

`Pot.Value` меняется при вращении; `Btn.Value` 0/1 при нажатии. Watch не требуется.

Тексты BOM/проводки — пересказ открытых Arduino docs ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)), не копипаст гайдов. Firmata: [firmata/arduino](https://github.com/firmata/arduino) (LGPL-2.1, в документ не вставляем `.ino`).

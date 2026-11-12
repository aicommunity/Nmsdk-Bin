# Hardware test: DeviceIO Potentiometer

**Путь:** `Bin/Configs/SpikeSamples/Hardware/10-DeviceIO-Potentiometer`

Общий HOWTO Firmata: [LAB-Firmata.md](../LAB-Firmata.md).

## Назначение

Firmata + DeviceIO potentiometer A0. Результат — `Pot.Value` в инспекторе.

## BOM

Плата + USB + потенциометр.

## Проводка

Потенциометр: крайние выводы на 5V и GND, средний (wiper) на **A0**. См. [Analog Input](https://docs.arduino.cc/built-in-examples/analog/AnalogInput/) (Arduino docs, CC BY-SA 4.0).

![Arduino Mega 2560 Rev3](../_shared/media/Arduino_MEGA2560.png)

*Arduino, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Arduino_MEGA2560.png). Pinout PDF: [Mega A000067](../_shared/media/A000067-full-pinout.pdf) / [Uno A000066](../_shared/media/A000066-full-pinout.pdf) (Arduino, CC BY-SA 4.0).*


## Перед запуском

1. Подключите плату по USB. По умолчанию генератор пишет `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
2. Откройте `Project.ini` в NeuroModeler.
3. Клик по узлу **Firmata** (или Board) → вкладки **Assembly** / **Pinout** / **Pins** / **Monitor** / **Board**.
4. **Upload** bundled `standard_firmata` (если ещё не прошито) → **Connect** → дождитесь `FirmataReady`.
5. Для DeviceIO: **ApplyConfig**, затем Continuous / Calculate.

## Компоненты

- `Firmata` + `Pot` (`ArduinoDeviceIO`, ModuleId=potentiometer).

## Схема Assembly

Sensor Shield + potentiometer A0 (и servo D9 в JSON — на схеме есть, узел IO только Pot).

## Критерий успеха

Continuous: `Pot.Value` в диапазоне 0..1 следует за ручкой.

Тексты BOM/проводки — пересказ открытых Arduino docs ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)), не копипаст гайдов. Firmata: [firmata/arduino](https://github.com/firmata/arduino) (LGPL-2.1, в документ не вставляем `.ino`).

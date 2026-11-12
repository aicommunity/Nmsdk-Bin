# Hardware test: ArduinoFirmata

**Путь:** `Bin/Configs/SpikeSamples/Hardware/03-ArduinoFirmata`

Общий HOWTO Firmata: [LAB-Firmata.md](../LAB-Firmata.md).

## Назначение

Пульт пинов StandardFirmata: handshake, D13 с вкладки Pins, Monitor.

## BOM

Плата Arduino + USB. Датчики не нужны.

## Проводка

Встроенный светодиод платы на **D13** (Uno/Mega). Дополнительная проводка не нужна. См. [Digital Pins](https://docs.arduino.cc/learn/microcontrollers/digital-pins/) (Arduino docs, CC BY-SA 4.0).

![Arduino Mega 2560 Rev3](../_shared/media/Arduino_MEGA2560.png)

*Arduino, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Arduino_MEGA2560.png). Pinout PDF: [Mega A000067](../_shared/media/A000067-full-pinout.pdf) / [Uno A000066](../_shared/media/A000066-full-pinout.pdf) (Arduino, CC BY-SA 4.0).*


## Перед запуском

1. Подключите плату по USB. По умолчанию генератор пишет `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
2. Откройте `Project.ini` в NeuroModeler.
3. Клик по узлу **Firmata** (или Board) → вкладки **Assembly** / **Pinout** / **Pins** / **Monitor** / **Board**.
4. **Upload** bundled `standard_firmata` (если ещё не прошито) → **Connect** → дождитесь `FirmataReady`.
5. Для DeviceIO: **ApplyConfig**, затем Continuous / Calculate.

## Компоненты

- `Firmata` (`ArduinoFirmata`) — bundled `standard_firmata`.

## Схема Assembly

Setup JSON не задан. Смотрите вкладки **Pinout** и **Pins**.

## Критерий успеха

`FirmataReady`; D13 OUTPUT + WriteDigital 1 зажигает встроенный светодиод.

Тексты BOM/проводки — пересказ открытых Arduino docs ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)), не копипаст гайдов. Firmata: [firmata/arduino](https://github.com/firmata/arduino) (LGPL-2.1, в документ не вставляем `.ino`).

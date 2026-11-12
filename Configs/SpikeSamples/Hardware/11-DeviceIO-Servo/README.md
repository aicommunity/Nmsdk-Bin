# Hardware test: DeviceIO Servo

**Путь:** `Bin/Configs/SpikeSamples/Hardware/11-DeviceIO-Servo`

Общий HOWTO Firmata: [LAB-Firmata.md](../LAB-Firmata.md).

## Назначение

Firmata + DeviceIO servo D9; `ValueIn` 0..1 → угол ~0..180°.

## BOM

Плата + USB + сервопривод (3 провода).

## Проводка

Сервопривод: сигнал на **D9** (PWM), питание 5V, земля GND. Внешнее питание серво — если ток больше, чем даёт USB. См. [Servo](https://docs.arduino.cc/learn/electronics/servo-motors/) (Arduino docs, CC BY-SA 4.0).

![Arduino Mega 2560 Rev3](../_shared/media/Arduino_MEGA2560.png)

*Arduino, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Arduino_MEGA2560.png). Pinout PDF: [Mega A000067](../_shared/media/A000067-full-pinout.pdf) / [Uno A000066](../_shared/media/A000066-full-pinout.pdf) (Arduino, CC BY-SA 4.0).*


## Перед запуском

1. Подключите плату по USB. По умолчанию генератор пишет `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
2. Откройте `Project.ini` в NeuroModeler.
3. Клик по узлу **Firmata** (или Board) → вкладки **Assembly** / **Pinout** / **Pins** / **Monitor** / **Board**.
4. **Upload** bundled `standard_firmata` (если ещё не прошито) → **Connect** → дождитесь `FirmataReady`.
5. Для DeviceIO: **ApplyConfig**, затем Continuous / Calculate.

## Компоненты

- `Firmata` + `Servo` (`ArduinoDeviceIO`).

## Схема Assembly

Sensor Shield + servo D9 на вкладке Assembly.

## Критерий успеха

`Servo.ValueIn` 0..1 поворачивает вал. ApplyConfig перед записью.

Тексты BOM/проводки — пересказ открытых Arduino docs ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)), не копипаст гайдов. Firmata: [firmata/arduino](https://github.com/firmata/arduino) (LGPL-2.1, в документ не вставляем `.ino`).

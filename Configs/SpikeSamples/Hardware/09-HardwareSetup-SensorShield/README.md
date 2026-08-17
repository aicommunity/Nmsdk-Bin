# Hardware test: Hardware Setup + Assembly

**Путь:** `Bin/Configs/SpikeSamples/Hardware/09-HardwareSetup-SensorShield`

Общий HOWTO Firmata: [LAB-Firmata.md](../LAB-Firmata.md).

## Назначение

Только Firmata + JSON Sensor Shield (pot A0, servo D9). IO-узлов нет — схема на вкладке Assembly.

## BOM

Как лабы 10+11: потенциометр и/или серво (для сверки схемы). Запуск без деталей допустим.

## Проводка

Потенциометр: крайние выводы на 5V и GND, средний (wiper) на **A0**. См. [Analog Input](https://docs.arduino.cc/built-in-examples/analog/AnalogInput/) (Arduino docs, CC BY-SA 4.0). Сервопривод: сигнал на **D9** (PWM), питание 5V, земля GND. Внешнее питание серво — если ток больше, чем даёт USB. См. [Servo](https://docs.arduino.cc/learn/electronics/servo-motors/) (Arduino docs, CC BY-SA 4.0).

![Arduino Mega 2560 Rev3](../_shared/media/Arduino_MEGA2560.png)

*Arduino, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Arduino_MEGA2560.png). Pinout PDF: [Mega A000067](../_shared/media/A000067-full-pinout.pdf) / [Uno A000066](../_shared/media/A000066-full-pinout.pdf) (Arduino, CC BY-SA 4.0).*


## Перед запуском

1. Подключите плату по USB. По умолчанию генератор пишет `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
2. Откройте `Project.ini` в NeuroModeler.
3. Клик по узлу **Firmata** (или Board) → вкладки **Assembly** / **Pinout** / **Pins** / **Monitor** / **Board**.
4. **Upload** bundled `standard_firmata` (если ещё не прошито) → **Connect** → дождитесь `FirmataReady`.
5. Для DeviceIO: **ApplyConfig**, затем Continuous / Calculate.

## Компоненты

- `Firmata` — `HardwareSetupPath=../_shared/HardwareSetup-mega2560.json`, firmware `standard_firmata`.

## Схема Assembly

Вкладка **Assembly**: плата, Sensor Shield, pot A0, servo D9. IO читайте в 10/11.

## Критерий успеха

Схема отображается; `HardwareSetupValid` = 1.

Тексты BOM/проводки — пересказ открытых Arduino docs ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)), не копипаст гайдов. Firmata: [firmata/arduino](https://github.com/firmata/arduino) (LGPL-2.1, в документ не вставляем `.ino`).

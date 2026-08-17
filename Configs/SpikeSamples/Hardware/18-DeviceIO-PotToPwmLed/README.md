# Hardware lab: pot A0 → PWM LED D9

**Путь:** `Bin/Configs/SpikeSamples/Hardware/18-DeviceIO-PotToPwmLed`

Общий HOWTO Firmata: [LAB-Firmata.md](../LAB-Firmata.md).

## Назначение

Analog In/Out: потенциометр A0 управляет яркостью PWM LED на D9 (модуль `pwm_led`).

## BOM

Плата + USB + потенциометр + светодиод + резистор ~220 Ω.

## Проводка

Потенциометр на **A0** (как в лабе 10). Светодиод: анод через резистор **~220 Ω** на **D9** (PWM), катод на GND. Сценарий как в [Analog In, Out Serial](https://docs.arduino.cc/built-in-examples/analog/AnalogInOutSerial/) (Arduino docs, CC BY-SA 4.0).

![Arduino Mega 2560 Rev3](../_shared/media/Arduino_MEGA2560.png)

*Arduino, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Arduino_MEGA2560.png). Pinout PDF: [Mega A000067](../_shared/media/A000067-full-pinout.pdf) / [Uno A000066](../_shared/media/A000066-full-pinout.pdf) (Arduino, CC BY-SA 4.0).*


## Перед запуском

1. Подключите плату по USB. По умолчанию генератор пишет `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
2. Откройте `Project.ini` в NeuroModeler.
3. Клик по узлу **Firmata** (или Board) → вкладки **Assembly** / **Pinout** / **Pins** / **Monitor** / **Board**.
4. **Upload** bundled `standard_firmata` (если ещё не прошито) → **Connect** → дождитесь `FirmataReady`.
5. Для DeviceIO: **ApplyConfig**, затем Continuous / Calculate.

## Компоненты

- `Firmata` + `Pot` + `PwmLed` (`ArduinoDeviceIO`).

## Схема Assembly

Pot A0 и PWM LED D9.

## Критерий успеха

Крутите A0 → `Pot.Value` и яркость LED на D9 меняются. Нужны внешние детали.

Тексты BOM/проводки — пересказ открытых Arduino docs ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)), не копипаст гайдов. Firmata: [firmata/arduino](https://github.com/firmata/arduino) (LGPL-2.1, в документ не вставляем `.ino`).

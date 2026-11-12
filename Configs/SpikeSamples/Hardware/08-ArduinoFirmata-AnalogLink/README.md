# Hardware test: Firmata AnalogSamples link

**Путь:** `Bin/Configs/SpikeSamples/Hardware/08-ArduinoFirmata-AnalogLink`

Общий HOWTO Firmata: [LAB-Firmata.md](../LAB-Firmata.md).

## Назначение

Firmata с `AutoRefreshPins` + `ArduinoAdc.UseLinkedAnalogSamples` (потенциометр A0).

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

- `Firmata` + `Adc` (linked samples, A0 = Firmata pin 54).

## Схема Assembly

Нет HardwareSetup. Результат — `AnalogSamples` / `AdcValue`, не Watch.

## Критерий успеха

При вращении потенциометра меняются `Adc.AdcValue` и строки `Firmata.AnalogSamples`.

Тексты BOM/проводки — пересказ открытых Arduino docs ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)), не копипаст гайдов. Firmata: [firmata/arduino](https://github.com/firmata/arduino) (LGPL-2.1, в документ не вставляем `.ino`).

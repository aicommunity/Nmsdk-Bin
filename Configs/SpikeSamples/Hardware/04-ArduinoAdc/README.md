# Hardware test: ArduinoAdc

**Путь:** `Bin/Configs/SpikeSamples/Hardware/04-ArduinoAdc`

## Назначение

Проверка `ArduinoAdc` через связанный `Firmata` (A0 = Firmata pin 54).

## Перед запуском

1. Подключите Arduino по USB.
2. Свойства по умолчанию: `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
3. Connect / Upload из GUI при необходимости.
4. Чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `Firmata` + `Adc` (`ArduinoAdc`, `LinkedFirmataName=Firmata`).

## Проверка

Открыть проект в NeuroModeler → Build / Reset / Calculate.

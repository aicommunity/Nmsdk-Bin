# Hardware test: ArduinoBoard

**Путь:** `Bin/Configs/SpikeSamples/Hardware/01-ArduinoBoard`

## Назначение

Проверка `ArduinoBoard`: прошивка sensor_lab, upload, heartbeat, подключение.

## Перед запуском

1. Подключите Arduino по USB.
2. Свойства по умолчанию: `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
3. Connect / Upload из GUI при необходимости.
4. Чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `Board` (`ArduinoBoard`) — upload `sensor_lab_v1`, порт, heartbeat.

## Проверка

Открыть проект в NeuroModeler → Build / Reset / Calculate.

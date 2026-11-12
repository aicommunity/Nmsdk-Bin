# Hardware test: ArduinoSensorSketch PROTO v2

**Путь:** `Bin/Configs/SpikeSamples/Hardware/06-ArduinoSensorSketch-Proto2`

## Назначение

Проверка framed protocol v2: `ProtocolVersion` = 2, команда `PROTO 2` при подключении.

## Перед запуском

1. Подключите Arduino по USB.
2. Свойства по умолчанию: `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
3. Connect / Upload из GUI при необходимости.
4. Чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `SensorSketch` (`ArduinoSensorSketch`) — ProtocolVersion 2.

## Проверка

Открыть проект в NeuroModeler → Build / Reset / Calculate.

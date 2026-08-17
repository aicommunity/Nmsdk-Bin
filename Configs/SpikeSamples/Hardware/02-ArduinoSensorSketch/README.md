# Hardware test: ArduinoSensorSketch

**Путь:** `Bin/Configs/SpikeSamples/Hardware/02-ArduinoSensorSketch`

## Назначение

Проверка `ArduinoSensorSketch`: кастомный протокол sensor_lab, команды, матрица.

## Перед запуском

1. Подключите Arduino по USB.
2. Свойства по умолчанию: `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
3. Connect / Upload из GUI при необходимости.
4. Чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `SensorSketch` (`ArduinoSensorSketch`) — bundled `sensor_lab_v1`, ProtocolVersion 1.

## Проверка

Открыть проект в NeuroModeler → Build / Reset / Calculate.

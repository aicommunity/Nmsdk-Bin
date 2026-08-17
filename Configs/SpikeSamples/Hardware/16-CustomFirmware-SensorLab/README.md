# Hardware test: CustomFirmware + sensor_lab plugin

**Путь:** `Bin/Configs/SpikeSamples/Hardware/16-CustomFirmware-SensorLab`

## Назначение

ArduinoCustomFirmware bound to sensor_lab_v1 plugin (generic custom path).

## Перед запуском

1. Подключите Arduino по USB.
2. Свойства по умолчанию: `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
3. Connect / Upload из GUI при необходимости.
4. Чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `Fw` (`ArduinoCustomFirmware`) — HostPluginId=sensor_lab_v1.

## Проверка

Открыть проект в NeuroModeler → Build / Reset / Calculate.

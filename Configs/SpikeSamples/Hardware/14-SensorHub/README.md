# Hardware test: Nmsdk Sensor Hub

**Путь:** `Bin/Configs/SpikeSamples/Hardware/14-SensorHub`

## Назначение

CustomFirmware + plugin `nmsdk_sensor_hub_v1`: DHT/HC-SR04 framed hub, Assembly setup.

## Перед запуском

1. Подключите Arduino по USB.
2. Свойства по умолчанию: `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
3. Connect / Upload из GUI при необходимости.
4. Чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `Hub` (`ArduinoCustomFirmware`) — HostPluginId/BundledFirmwareId = nmsdk_sensor_hub_v1.

## Проверка

Открыть проект в NeuroModeler → Build / Reset / Calculate.

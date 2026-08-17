# Hardware test: Nmsdk Motor Hub

**Путь:** `Bin/Configs/SpikeSamples/Hardware/15-MotorHub`

## Назначение

CustomFirmware + plugin `nmsdk_motor_hub_v1`: MOTOR A pwm/dir, framed status 0x20.

## Перед запуском

1. Подключите Arduino по USB.
2. Свойства по умолчанию: `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
3. Connect / Upload из GUI при необходимости.
4. Чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `Hub` (`ArduinoCustomFirmware`) — HostPluginId = nmsdk_motor_hub_v1.

## Проверка

Открыть проект в NeuroModeler → Build / Reset / Calculate.

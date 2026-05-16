# Hardware test: ArduinoSensorSketch PROTO v2

**Путь:** `Bin/Configs/SpikeSamples/Hardware/06-ArduinoSensorSketch-Proto2`

## Назначение

Проверка framed protocol v2: `ProtocolVersion` = 2, команда `PROTO 2` при подключении.

## Перед запуском

1. Подключите Arduino Uno/Mega по USB.
2. В свойстве `PortName` укажите порт (`/dev/ttyACM0`, `COM3`, …).
3. При необходимости установите `ConnectOnBuild` = 1 или нажмите Connect в GUI.
4. См. чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `SensorSketch` (`ArduinoSensorSketch`) — ProtocolVersion 2.

## Проверка

- Открыть проект в NeuroModeler.
- Build / Reset / Calculate.
- Сверить с пунктами чеклиста для данного компонента.

# Hardware test: ArduinoSensorSketch

**Путь:** `Bin/Configs/SpikeSamples/Hardware/02-ArduinoSensorSketch`

## Назначение

Проверка `ArduinoSensorSketch`: кастомный протокол sensor_lab, команды, матрица.

## Перед запуском

1. Подключите Arduino Uno/Mega по USB.
2. В свойстве `PortName` укажите порт (`/dev/ttyACM0`, `COM3`, …).
3. При необходимости установите `ConnectOnBuild` = 1 или нажмите Connect в GUI.
4. См. чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `SensorSketch` (`ArduinoSensorSketch`) — bundled `sensor_lab_v1`, ProtocolVersion 1.

## Проверка

- Открыть проект в NeuroModeler.
- Build / Reset / Calculate.
- Сверить с пунктами чеклиста для данного компонента.

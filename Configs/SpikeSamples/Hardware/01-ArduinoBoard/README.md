# Hardware test: ArduinoBoard

**Путь:** `Bin/Configs/SpikeSamples/Hardware/01-ArduinoBoard`

## Назначение

Проверка `ArduinoBoard`: прошивка sensor_lab, upload, heartbeat, подключение.

## Перед запуском

1. Подключите Arduino Uno/Mega по USB.
2. В свойстве `PortName` укажите порт (`/dev/ttyACM0`, `COM3`, …).
3. При необходимости установите `ConnectOnBuild` = 1 или нажмите Connect в GUI.
4. См. чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `Board` (`ArduinoBoard`) — upload `sensor_lab_v1`, порт, heartbeat.

## Проверка

- Открыть проект в NeuroModeler.
- Build / Reset / Calculate.
- Сверить с пунктами чеклиста для данного компонента.

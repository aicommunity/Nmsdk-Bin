# Hardware test: Arduino property edges

**Путь:** `Bin/Configs/SpikeSamples/Hardware/07-ArduinoPropertyEdges`

## Назначение

Ручная проверка edge-свойств Board без отдельного железа (порт можно оставить пустым).

## Перед запуском

1. Подключите Arduino Uno/Mega по USB.
2. В свойстве `PortName` укажите порт (`/dev/ttyACM0`, `COM3`, …).
3. При необходимости установите `ConnectOnBuild` = 1 или нажмите Connect в GUI.
4. См. чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `Board` (`ArduinoBoard`) — примеры `<Connect>1</Connect>`, `<UploadFirmware>1</UploadFirmware>`.

## Проверка

- Открыть проект в NeuroModeler.
- Build / Reset / Calculate.
- Сверить с пунктами чеклиста для данного компонента.

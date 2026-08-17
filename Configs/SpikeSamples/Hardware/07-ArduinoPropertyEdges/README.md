# Hardware test: Arduino property edges

**Путь:** `Bin/Configs/SpikeSamples/Hardware/07-ArduinoPropertyEdges`

## Назначение

Ручная проверка edge-свойств Board: в XML edges = 0; импульс Connect/UploadFirmware из GUI или Property editor.

## Перед запуском

1. Подключите Arduino по USB.
2. Свойства по умолчанию: `PortName=COM3`, `BoardProfile=1` (Arduino Mega 2560).
3. Connect / Upload из GUI при необходимости.
4. Чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `Board` (`ArduinoBoard`) — edges по умолчанию 0; пульсируйте `Connect` / `UploadFirmware` вручную.

## Проверка

Открыть проект в NeuroModeler → Build / Reset / Calculate.

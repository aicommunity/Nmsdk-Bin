# Hardware test: Nmsdk Sensor Hub

**Путь:** `Bin/Configs/SpikeSamples/Hardware/14-SensorHub`

## Назначение

CustomFirmware + plugin `nmsdk_sensor_hub_v1`: DHT/HC-SR04 framed hub, Assembly setup.

## Перед запуском

1. Подключите Arduino Uno/Mega по USB.
2. В свойстве `PortName` укажите порт (`/dev/ttyACM0`, `COM3`, …).
3. При необходимости установите `ConnectOnBuild` = 1 или нажмите Connect в GUI.
4. См. чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Плата Uno vs Mega 2560

- Свойство `BoardProfile`: **0** = Arduino Uno, **1** = Arduino Mega 2560.
- Bundled HEX (`BundledFirmwareId`) выбирается по профилю (см. `Bin/ArduinoFirmware/manifest.json`).
- Перед **Upload** на Mega установите профиль **1** в GUI (Board) или включите авто-детект при выборе COM.
- Конфиги в этом каталоге по умолчанию используют **Uno (0)**.

## Компоненты

- `Hub` (`ArduinoCustomFirmware`) — HostPluginId/BundledFirmwareId = nmsdk_sensor_hub_v1.

## Проверка

- Открыть проект в NeuroModeler.
- Build / Reset / Calculate.
- Сверить с пунктами чеклиста для данного компонента.

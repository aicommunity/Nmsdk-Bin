# Hardware test: ArduinoAdc

**Путь:** `Bin/Configs/SpikeSamples/Hardware/04-ArduinoAdc`

## Назначение

Проверка `ArduinoAdc` через связанный `Firmata` (analog pin A0 = Firmata 14).

## Перед запуском

1. Подключите Arduino Uno/Mega по USB.
2. В свойстве `PortName` укажите порт (`/dev/ttyACM0`, `COM3`, …).
3. При необходимости установите `ConnectOnBuild` = 1 или нажмите Connect в GUI.
4. См. чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `Firmata` + `Adc` (`ArduinoAdc`, `LinkedFirmataName=Firmata`).

## Проверка

- Открыть проект в NeuroModeler.
- Build / Reset / Calculate.
- Сверить с пунктами чеклиста для данного компонента.

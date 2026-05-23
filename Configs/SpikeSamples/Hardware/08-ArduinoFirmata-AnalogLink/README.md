# Hardware test: Firmata AnalogSamples link

**Путь:** `Bin/Configs/SpikeSamples/Hardware/08-ArduinoFirmata-AnalogLink`

## Назначение

Firmata с `AutoRefreshPins` + `ArduinoAdc.UseLinkedAnalogSamples` для проверки link на `AnalogSamples`.

## Перед запуском

1. Подключите Arduino Uno/Mega по USB.
2. В свойстве `PortName` укажите порт (`/dev/ttyACM0`, `COM3`, …).
3. При необходимости установите `ConnectOnBuild` = 1 или нажмите Connect в GUI.
4. См. чеклист: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

## Компоненты

- `Firmata` + `Adc` (linked samples, A0 = pin 14).

## Проверка

- Открыть проект в NeuroModeler.
- Build / Reset / Calculate.
- Сверить с пунктами чеклиста для данного компонента.

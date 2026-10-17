# Hardware test: Esp32Board

**Путь:** `Bin/Configs/SpikeSamples/Hardware/12-Esp32Board`

## Назначение

Проверка `Esp32Board` (Connect-only P0): serial 115200, без DTR reset pulse.

## Перед запуском

1. Подключите ESP32 DevKit по USB.
2. Укажите `PortName` (`/dev/ttyUSB0`, `COM3`, …).
3. BaudRate по умолчанию **115200**.
4. Upload через esptool в IDE — P1; в P0 используйте Connect.

## Компоненты

- `Board` (`Esp32Board`) — порт, ChipTarget, FlashBaud, heartbeat.

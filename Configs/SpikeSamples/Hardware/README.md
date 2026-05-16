# Hardware — тестовые конфигурации Rdk-HardwareLib

Набор минимальных проектов для ручной проверки компонентов Arduino на плате.

| Каталог | ClassName | Прошивка |
|---------|-----------|----------|
| [01-ArduinoBoard](01-ArduinoBoard/) | `ArduinoBoard` | sensor_lab_v1 |
| [02-ArduinoSensorSketch](02-ArduinoSensorSketch/) | `ArduinoSensorSketch` | sensor_lab_v1 |
| [03-ArduinoFirmata](03-ArduinoFirmata/) | `ArduinoFirmata` | standard_firmata |
| [04-ArduinoAdc](04-ArduinoAdc/) | `ArduinoAdc` + `ArduinoFirmata` | standard_firmata |
| [05-ArduinoDcDemo](05-ArduinoDcDemo/) | `ArduinoDcDemo` + `ArduinoSensorSketch` | sensor_lab_v1 |
| [06-ArduinoSensorSketch-Proto2](06-ArduinoSensorSketch-Proto2/) | `ArduinoSensorSketch` (v2) | sensor_lab_v1 |

Перед тестом задайте `PortName` (57600) и следуйте [чеклисту](../../../../Libraries/Rdk-HardwareLib/Firmware/README.md).

Документация компонентов: [Rdk-HardwareLib/Docs/README.md](../../../../Libraries/Rdk-HardwareLib/Docs/README.md).

Генерация: `Scripts/generate_arduino_hardware_configs.py`

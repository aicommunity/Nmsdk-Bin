# Hardware — тестовые конфигурации Rdk-HardwareLib

Набор минимальных проектов для ручной проверки компонентов Arduino на плате.

| Каталог | ClassName | Прошивка | Default BP |
|---------|-----------|----------|------------|
| [01-ArduinoBoard](01-ArduinoBoard/) | `ArduinoBoard` | sensor_lab_v1 | Uno (0) |
| [02-ArduinoSensorSketch](02-ArduinoSensorSketch/) | `ArduinoSensorSketch` | sensor_lab_v1 | Uno (0) |
| [03-ArduinoFirmata](03-ArduinoFirmata/) | `ArduinoFirmata` | standard_firmata | Uno (0) |
| [04-ArduinoAdc](04-ArduinoAdc/) | `ArduinoAdc` + `ArduinoFirmata` | standard_firmata | Uno (0) |
| [05-ArduinoDcDemo](05-ArduinoDcDemo/) | `ArduinoDcDemo` (single node) | sensor_lab_v1 | Uno (0) |
| [06-ArduinoSensorSketch-Proto2](06-ArduinoSensorSketch-Proto2/) | `ArduinoSensorSketch` (v2) | sensor_lab_v1 | Uno (0) |
| [07-ArduinoPropertyEdges](07-ArduinoPropertyEdges/) | `ArduinoBoard` (edge API) | sensor_lab_v1 | Uno (0) |
| [08-ArduinoFirmata-AnalogLink](08-ArduinoFirmata-AnalogLink/) | `ArduinoFirmata` + `ArduinoAdc` | standard_firmata | Uno (0) |
| [09-HardwareSetup-SensorShield](09-HardwareSetup-SensorShield/) | `ArduinoFirmata` + HardwareSetup | standard_firmata | Uno (0) |
| [10-DeviceIO-Potentiometer](10-DeviceIO-Potentiometer/) | `ArduinoDeviceIO` | standard_firmata | Uno (0) |
| [11-DeviceIO-Servo](11-DeviceIO-Servo/) | `ArduinoDeviceIO` | standard_firmata | Uno (0) |
| [12-MotorShield-R3](12-MotorShield-R3/) | `ArduinoDeviceIO` motor | standard_firmata | Uno (0) |
| [13-Sensors-To-Pulse](13-Sensors-To-Pulse/) | DeviceIO sensors | standard_firmata | Uno (0) |

**BoardProfile:** 0 = Uno, 1 = Mega 2560. Перед Upload на Mega выберите профиль 1 или авто-детект в GUI.

Перед тестом задайте `PortName` и следуйте [чеклисту](../../../../Libraries/Rdk-HardwareLib/Firmware/README.md).

Генерация: `Scripts/generate_arduino_hardware_configs.py`  
Миграция legacy DC: `Scripts/migrate_arduino_board_hierarchy.py`

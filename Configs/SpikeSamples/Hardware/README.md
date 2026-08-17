# Hardware — тестовые конфигурации Rdk-HardwareLib

Набор проектов для проверки компонентов Arduino. **Firmata-лабы (схема → сборка → результат):**
см. [LAB-Firmata.md](LAB-Firmata.md).

По умолчанию генератор пишет **Arduino Mega 2560 (1)**, порт `COM3`.
Перегенерация: `python Scripts/generate_arduino_hardware_configs.py --port COM3 --board-profile 1`

| Каталог | ClassName | Прошивка | Примечание |
|---------|-----------|----------|------------|
| [01-ArduinoBoard](01-ArduinoBoard/) | `ArduinoBoard` | sensor_lab_v1 | |
| [02-ArduinoSensorSketch](02-ArduinoSensorSketch/) | `ArduinoSensorSketch` | sensor_lab_v1 | |
| [03-ArduinoFirmata](03-ArduinoFirmata/) | `ArduinoFirmata` | standard_firmata | лаба, без датчиков |
| [04-ArduinoAdc](04-ArduinoAdc/) | `ArduinoAdc` + `ArduinoFirmata` | standard_firmata | |
| [05-ArduinoDcDemo](05-ArduinoDcDemo/) | `ArduinoDcDemo` | sensor_lab_v1 | |
| [06-ArduinoSensorSketch-Proto2](06-ArduinoSensorSketch-Proto2/) | `ArduinoSensorSketch` | sensor_lab_v1 | |
| [07-ArduinoPropertyEdges](07-ArduinoPropertyEdges/) | `ArduinoBoard` | sensor_lab_v1 | |
| [08-ArduinoFirmata-AnalogLink](08-ArduinoFirmata-AnalogLink/) | `ArduinoFirmata` + `ArduinoAdc` | standard_firmata | лаба, нужен pot |
| [09-HardwareSetup-SensorShield](09-HardwareSetup-SensorShield/) | `ArduinoFirmata` + HardwareSetup | standard_firmata | лаба, схема Assembly |
| [10-DeviceIO-Potentiometer](10-DeviceIO-Potentiometer/) | `ArduinoDeviceIO` | standard_firmata | лаба, pot A0 |
| [11-DeviceIO-Servo](11-DeviceIO-Servo/) | `ArduinoDeviceIO` | standard_firmata | лаба, servo D9 |
| [12-MotorShield-R3](12-MotorShield-R3/) | `ArduinoDeviceIO` motor | standard_firmata | лаба, шилд |
| [13-Sensors-To-Pulse](13-Sensors-To-Pulse/) | DeviceIO sensors | standard_firmata | лаба, pot+кнопка |
| [14-SensorHub](14-SensorHub/) | `ArduinoCustomFirmware` | nmsdk_sensor_hub_v1 | не Firmata |
| [15-MotorHub](15-MotorHub/) | `ArduinoCustomFirmware` | nmsdk_motor_hub_v1 | не Firmata |
| [16-CustomFirmware-SensorLab](16-CustomFirmware-SensorLab/) | `ArduinoCustomFirmware` | sensor_lab_v1 | не Firmata |
| [17-DeviceIO-LED](17-DeviceIO-LED/) | `ArduinoDeviceIO` led | standard_firmata | лаба, без датчиков |
| [18-DeviceIO-PotToPwmLed](18-DeviceIO-PotToPwmLed/) | DeviceIO pot+PWM LED | standard_firmata | лаба Analog In/Out |

**BoardProfile:** 0 = Uno, 1 = Mega 2560. JSON setup: `_shared/HardwareSetup-uno.json` и `HardwareSetup-mega2560.json`.

Чеклист прошивок: `Libraries/Rdk-HardwareLib/Firmware/README.md`.

Генерация: `Scripts/generate_arduino_hardware_configs.py`  
Ассеты: `Scripts/download_hardware_lab_assets.py`  
Валидация: `Scripts/validate_hardware_spike_configs.py`  
Миграция legacy DC: `Scripts/migrate_arduino_board_hierarchy.py`

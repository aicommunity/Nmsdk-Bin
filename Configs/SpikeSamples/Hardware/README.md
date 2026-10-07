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
| [09-ArduinoWheeledRobot](09-ArduinoWheeledRobot/) | `ArduinoWheeledRobot` | nmsdk_motor_hub_v1 | Uno (0) |
| [10-WaveRover](10-WaveRover/) | `WaveRover` | stock Waveshare JSON | ESP32 |
| [11-Esp32WheeledRobot](11-Esp32WheeledRobot/) | `Esp32WheeledRobot` | nmsdk_motor_hub_esp32_v1 | ESP32 |
| [12-Esp32Board](12-Esp32Board/) | `Esp32Board` | — (Connect-only) | ESP32 |
| [13-DeviceIO-Joystick](13-DeviceIO-Joystick/) | `ArduinoDeviceIO` | firmata | Uno (0) |
| [14-SensorHub](14-SensorHub/) | `ArduinoCustomFirmware` | nmsdk_sensor_hub_v1 | Uno (0) |
| [15-I2cHub-BME280](15-I2cHub-BME280/) | `ArduinoCustomFirmware` | nmsdk_i2c_hub_v1 | Uno (0) |
| [16-DisplayHub](16-DisplayHub/) | `ArduinoCustomFirmware` | nmsdk_display_hub_v1 | Uno (0) |
| [17-PixelHub](17-PixelHub/) | `ArduinoCustomFirmware` | nmsdk_pixel_hub_v1 | Uno (0) |
| [18-RadioHub](18-RadioHub/) | `ArduinoCustomFirmware` | nmsdk_radio_hub_v1 | Uno / ESP32 |
| [19-UartDeviceHub](19-UartDeviceHub/) | `ArduinoCustomFirmware` | nmsdk_uart_device_hub_v1 | Mega/ESP32 preferred |

**BoardProfile:** 0 = Uno, 1 = Mega 2560. Перед Upload на Mega выберите профиль 1 или авто-детект в GUI.

Перед тестом задайте `PortName` и следуйте [чеклисту](../../../../Libraries/Rdk-HardwareLib/Firmware/README.md).

Генерация: `Scripts/generate_arduino_hardware_configs.py`  
Миграция legacy DC: `Scripts/migrate_arduino_board_hierarchy.py`

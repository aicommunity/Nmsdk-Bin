# Bundled Arduino firmware (runtime)

Каталог прошивок по умолчанию для компонентов `ArduinoBoard` / `ArduinoFirmata` / `ArduinoSensorSketch`.

Относительно exe (`Bin/Platform/<OS>/`): **`../../ArduinoFirmware/`**

Сборка HEX:

```bash
./Scripts/build_arduino_firmware.sh
```

Исходники sketch (только для сборки): `Libraries/Rdk-HardwareLib/Firmware/`.

Переменная окружения `RDK_HARDWARE_FIRMWARE_DIR` переопределяет корень.

# 15-I2cHub-BME280

P2 Tier C: `ArduinoCustomFirmware` + `nmsdk_i2c_hub_v1` (BME280).

1. Wire BME280 I2C (Uno: SDA=A4 SCL=A5), address 0x76 or 0x77.
2. Flash `Firmware/nmsdk_i2c_hub` (Adafruit BME280 libs).
3. Connect @ 57600; `START READING`; watch NamedValues `t` / `h` / `pressure_hpa`.

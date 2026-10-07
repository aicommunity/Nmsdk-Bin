# 15-I2cHub (I2C hub)

P2 / P2+: `ArduinoCustomFirmware` + `HostPluginId=nmsdk_i2c_hub_v1`.

| Module | Frame / cmd | Named values | Flag default |
|--------|-------------|--------------|--------------|
| `bme280` | `0x01` | `t`, `h`, `pressure_hpa` | 1 |
| `vl53l0x` | `0x30` | `distance_mm` | 1 |
| `mpu_6050` | `0x31` | `ax`…`gz` | 1 |
| `ina219` | `0x32` | `bus_v`, `current_ma`, `power_mw` | 1 |
| `pca9685_16_ch_pwm` | `SET PWM` → `0x33` | `pca_ch`, `pca_duty` | 1 |
| `bmp280` / `bme680` | `0x34` | `t`, `h`, `pressure_hpa` | 0 |
| `vl53l1x` | `0x35` | `distance_mm` | 0 |
| `icm_20948` | `0x36` | `ax`…`gz`, `mx`, `my` | 0 |
| `aht20` / `sht31` | `0x37` | `t`, `h` | 0 |
| `bh1750` | `0x38` | `lux` | 0 |
| `mlx90614` | `0x39` | `object_c`, `ambient_c` | 0 |
| `sgp30` | `0x3A` | `eco2`, `tvoc` | 0 |
| `tcs34725` | `0x3B` | `r`,`g`,`b`,`c` | 0 |
| `adxl345` | `0x3C` | `ax`,`ay`,`az` | 0 |
| `apds_9960` | `0x3D` | `gesture`,`proximity`,`r`… | 0 |
| `ads1115_adc` | `0x3E` | `ch0`…`ch3` | 0 |

1. Wire I2C (Uno SDA=A4 SCL=A5); flash `Firmware/nmsdk_i2c_hub` with needed Adafruit/BH1750 libs.
2. Connect @ **57600**, Hub Workbench → plugin `nmsdk_i2c_hub_v1`, `START READING`.
3. Optional: `SET PWM 0 2048` for PCA9685.

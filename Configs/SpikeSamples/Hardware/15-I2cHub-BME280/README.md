# 15-I2cHub-BME280 (I2C hub)

P2 Tier C: `ArduinoCustomFirmware` + `nmsdk_i2c_hub_v1`.

Covers priority I2C modules on one sketch (enable/disable via compile flags):

| Module | Frame / cmd | Named values |
|--------|-------------|--------------|
| `bme280` | `0x01` | `t`, `h`, `pressure_hpa` |
| `vl53l0x` | `0x30` | `distance_mm` |
| `mpu_6050` | `0x31` | `ax`…`gz` |
| `ina219` | `0x32` | `bus_v`, `current_ma`, `power_mw` |
| `pca9685_16_ch_pwm` | `SET PWM ch duty` → `0x33` | `pca_ch`, `pca_duty` |

1. Wire I2C (Uno SDA=A4 SCL=A5); flash `Firmware/nmsdk_i2c_hub` with Adafruit libs.
2. Connect @ **57600**, `START READING`.
3. Optional: send `SET PWM 0 2048` for PCA9685.

`icm_20948` / `vl53l1x` remain catalog `planned`.

# 14-SensorHub

Tier B: `ArduinoCustomFirmware` + `nmsdk_sensor_hub_v1`.

- Baud **57600** (ESP32 twin: `nmsdk_sensor_hub_esp32_v1` @ 115200)
- DHT11 default; build with `-DDHTTYPE=DHT22` for DHT22
- Optional DS18B20: `-DNMSDK_SENSOR_HUB_DS18B20=1` (OneWire + DallasTemperature)
- Commands: `START READING`, `SET DEVICE dht|trig|echo|hall|ds <pin>`

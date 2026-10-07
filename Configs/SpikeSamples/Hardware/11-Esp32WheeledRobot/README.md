# Esp32WheeledRobot

Nmsdk motor hub on ESP32 (`nmsdk_motor_hub_esp32_v1`). Not WaveRover JSON.

- Default **MotorDriverId:** `wire_l298n` (or `motor_shield_r3` on esp32_uno_formfactor)
- Baud **115200**, DTR/RTS off
- Connect → ApplyMotorDriver (if pins known) → ApplyDrive / Stop

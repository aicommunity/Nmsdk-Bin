# ArduinoWheeledRobot

Open-loop Left/Right PWM+Dir via `nmsdk_motor_hub_v1`.

- **MotorDriverId:** `motor_shield_r3`
- **Pins R3:** channel A DIR=D12 PWM=D3 BRAKE=D9 SENSE=A0; B DIR=D13 PWM=D11 BRAKE=D8 SENSE=A1
- Baud **57600**. Upload bundled `nmsdk_motor_hub_v1`, Connect, `ApplyMotorDriver`, then `ApplyDrive` / `Stop`.

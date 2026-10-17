# 13-DeviceIO-Joystick

Tier A Firmata + `ArduinoDeviceIO` (`ModuleId=analog_joystick`, defaultPort A0).

1. Flash `standard_firmata`, Connect Firmata.
2. DeviceIO → LinkedFirmataName=`Firmata`, ModuleId=`analog_joystick`.
3. ApplyConfig then Continuous/ReadInput for Value.
4. Module picker grouped by catalog Category with runtime badges.

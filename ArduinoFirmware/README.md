# Bundled Arduino firmware (runtime)

Runtime HEX files for NeuroModeler upload (`../../ArduinoFirmware` relative to `Bin/Platform/<OS>/`).

## Build

**Windows** (after [SetupArduinoTools.bat](../Platform/Win/SetupArduinoTools.bat) or with `arduino-cli` on PATH):

```powershell
.\Scripts\build_arduino_firmware.ps1
```

**Linux / macOS:**

```bash
./Scripts/build_arduino_firmware.sh
```

## Layout

| Path | Description |
|------|-------------|
| `manifest.json` | Bundled firmware ids (`sensor_lab_v1`, `standard_firmata`) |
| `sensor_lab/uno.hex`, `mega2560.hex` | Custom sensor_lab sketch |
| `firmata/standard_firmata_*.hex` | StandardFirmata |

Sources: `Libraries/Rdk-HardwareLib/Firmware/`.

Build artifacts under `.build_*` are local only (gitignored).

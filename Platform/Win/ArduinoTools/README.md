# ArduinoTools (not in git except this README)

This directory is populated by the setup script. After a successful run you should have:

- `bin/avrdude.exe` (and any DLLs from the Arduino AVR package)
- `etc/avrdude.conf`

## Install

From the repository root or from `Bin/Platform/Win`:

```bat
Bin\Platform\Win\SetupArduinoTools.bat
```

Requirements: internet access, PowerShell 5+, write access to the repo.

## Verify

```bat
cd Bin\Platform\Win
ArduinoTools\bin\avrdude.exe -C ArduinoTools\etc\avrdude.conf -?
```

NeuroModeler resolves `avrdude` automatically when started from `Bin/Platform/Win`.

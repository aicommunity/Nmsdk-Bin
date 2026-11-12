@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\..\..\Scripts\setup_arduino_tools.ps1" -Platform Win
if errorlevel 1 (
  echo Setup failed. See messages above.
  exit /b 1
)
echo.
echo Setup completed. Start NeuroModeler from this folder.
pause

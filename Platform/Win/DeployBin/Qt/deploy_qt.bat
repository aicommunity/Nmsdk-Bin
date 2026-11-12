@echo off
REM Скрипт для развёртывания Qt DLL из vcpkg в Bin/Platform/Win
REM Использование: deploy_qt.bat <путь_к_vcpkg_installed>

setlocal enabledelayedexpansion

if "%1"=="" (
    echo ERROR: Usage: deploy_qt.bat ^<vcpkg_installed_path^>
    echo Example: deploy_qt.bat E:\Science-Repo\nmsdk-git\build\win-msvc-debug\vcpkg_installed
    exit /b 1
)

set "VCPKG_INSTALLED=%1"
set "VCPKG_BIN=%VCPKG_INSTALLED%\x64-windows\bin"
set "VCPKG_DEBUG_BIN=%VCPKG_INSTALLED%\x64-windows\debug\bin"
set "TARGET_DIR=%~dp0..\.."

if not exist "%VCPKG_BIN%" (
    echo ERROR: vcpkg bin directory not found: %VCPKG_BIN%
    exit /b 1
)

echo ========================================
echo Deploying Qt DLLs from vcpkg
echo ========================================
echo Source (release): %VCPKG_BIN%
if exist "%VCPKG_DEBUG_BIN%" (
    echo Source (debug): %VCPKG_DEBUG_BIN%
)
echo Target: %TARGET_DIR%
echo ========================================
echo.

REM Копируем все release DLL
echo Copying release DLLs...
robocopy "%VCPKG_BIN%" "%TARGET_DIR%" *.dll /NP /NFL /NDL /NJH /NJS
if errorlevel 8 (
    echo ERROR: robocopy failed
    exit /b 1
)

REM Копируем debug DLL, если они существуют
if exist "%VCPKG_DEBUG_BIN%" (
    echo.
    echo Copying debug DLLs...
    robocopy "%VCPKG_DEBUG_BIN%" "%TARGET_DIR%" *.dll /NP /NFL /NDL /NJH /NJS
    if errorlevel 8 (
        echo ERROR: robocopy failed for debug DLLs
        exit /b 1
    )
)

REM Копируем Qt WebEngine файлы, если они есть
if exist "%VCPKG_BIN%\QtWebEngineProcess.exe" (
    echo.
    echo Copying QtWebEngineProcess.exe...
    copy /Y "%VCPKG_BIN%\QtWebEngineProcess.exe" "%TARGET_DIR%\" >nul
)

REM Копируем debug версию QtWebEngineProcess
if exist "%VCPKG_DEBUG_BIN%\QtWebEngineProcessd.exe" (
    echo Copying QtWebEngineProcessd.exe...
    copy /Y "%VCPKG_DEBUG_BIN%\QtWebEngineProcessd.exe" "%TARGET_DIR%\" >nul
)

REM Также проверяем tools директорию
set "VCPKG_ROOT=%VCPKG_INSTALLED%\x64-windows"
set "VCPKG_TOOLS_BIN=%VCPKG_ROOT%\tools\qt5\bin"
if exist "%VCPKG_TOOLS_BIN%\QtWebEngineProcess.exe" (
    echo Copying QtWebEngineProcess.exe from tools...
    copy /Y "%VCPKG_TOOLS_BIN%\QtWebEngineProcess.exe" "%TARGET_DIR%\" >nul
)
if exist "%VCPKG_TOOLS_BIN%\QtWebEngineProcessd.exe" (
    echo Copying QtWebEngineProcessd.exe from tools...
    copy /Y "%VCPKG_TOOLS_BIN%\QtWebEngineProcessd.exe" "%TARGET_DIR%\" >nul
)

REM Копируем Qt WebEngine DLL
if exist "%VCPKG_BIN%\Qt5WebEngine*.dll" (
    echo Copying Qt WebEngine DLLs...
    robocopy "%VCPKG_BIN%" "%TARGET_DIR%" Qt5WebEngine*.dll /NP /NFL /NDL /NJH /NJS
)

REM Копируем ресурсы WebEngine, если они есть
set "VCPKG_ROOT=%VCPKG_INSTALLED%\x64-windows"
if exist "%VCPKG_ROOT%\resources" (
    echo.
    echo Copying Qt WebEngine resources...
    xcopy /E /I /Y "%VCPKG_ROOT%\resources" "%TARGET_DIR%\resources\" >nul
)

REM Копируем переводы WebEngine, если они есть
if exist "%VCPKG_ROOT%\translations" (
    echo Copying Qt WebEngine translations...
    if not exist "%TARGET_DIR%\translations" mkdir "%TARGET_DIR%\translations"
    xcopy /E /I /Y "%VCPKG_ROOT%\translations" "%TARGET_DIR%\translations\" >nul
)

echo.
echo ========================================
echo Deployment completed successfully
echo ========================================
echo.

endlocal

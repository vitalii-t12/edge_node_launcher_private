@echo off
setlocal EnableDelayedExpansion

REM Check for parameters
set CREATE_MSI=0
if "%1"=="--msi" set CREATE_MSI=1

REM Your base PyInstaller command
set PYINSTALLER_CMD=pyinstaller -w --onefile -n "EdgeNodeLauncher" main.py

REM Combine the base command with the hidden imports and execute
echo %PYINSTALLER_CMD%
%PYINSTALLER_CMD%

REM Optionally create MSI installer
if %CREATE_MSI% EQU 1 (
    echo Creating MSI installer...
    call create_msi.bat
    if %ERRORLEVEL% NEQ 0 (
        echo MSI creation failed.
        exit /b 1
    )
)

echo Build process completed successfully!
endlocal
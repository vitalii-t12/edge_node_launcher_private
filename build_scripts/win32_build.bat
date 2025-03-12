@echo off
setlocal EnableDelayedExpansion

REM Default to building both
set BUILD_EXE=1
set BUILD_MSI=0

REM Parse command line parameters
if "%1"=="--msi" (
    set BUILD_MSI=1
) else if "%1"=="--exe-only" (
    set BUILD_EXE=1
    set BUILD_MSI=0
) else if "%1"=="--msi-only" (
    set BUILD_EXE=0
    set BUILD_MSI=1
) else if "%1" NEQ "" (
    echo Invalid parameter: %1
    echo Usage: win32_build.bat [--msi^|--exe-only^|--msi-only]
    echo   --msi        Build both EXE and MSI
    echo   --exe-only   Build only the EXE (default)
    echo   --msi-only   Build only the MSI
    exit /b 1
)

REM Your base PyInstaller command
set PYINSTALLER_CMD=pyinstaller -w --onefile -n "EdgeNodeLauncher" main.py

REM Build EXE if requested
if %BUILD_EXE% EQU 1 (
    echo Building EXE executable...
    echo %PYINSTALLER_CMD%
    %PYINSTALLER_CMD%
    if %ERRORLEVEL% NEQ 0 (
        echo EXE creation failed.
        exit /b 1
    )
)

REM Build MSI if requested
if %BUILD_MSI% EQU 1 (
    echo Creating MSI installer...
    
    REM If we didn't build the EXE and it doesn't exist, show an error
    if %BUILD_EXE% EQU 0 (
        if not exist "dist\EdgeNodeLauncher.exe" (
            if not exist "..\dist\EdgeNodeLauncher.exe" (
                echo ERROR: EdgeNodeLauncher.exe not found in dist folder. 
                echo Please run win32_build.bat --exe-only first or use win32_build.bat --msi to build both.
                exit /b 1
            )
        )
    )
    
    call create_msi.bat
    if %ERRORLEVEL% NEQ 0 (
        echo MSI creation failed.
        exit /b 1
    )
)

echo Build process completed successfully!
endlocal
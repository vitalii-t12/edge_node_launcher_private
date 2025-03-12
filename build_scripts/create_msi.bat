@echo off
setlocal EnableDelayedExpansion

REM Check if WiX Toolset is installed
where candle >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: WiX Toolset not found. Please install WiX Toolset to generate MSI installers.
    echo Download from: https://wixtoolset.org/releases/
    exit /b 1
)

REM Check if PyInstaller output exists in either possible location
set EXE_FOUND=0
if exist "..\dist\EdgeNodeLauncher.exe" (
    set EXE_FOUND=1
    set EXE_PATH=..\dist\EdgeNodeLauncher.exe
    set DIST_PATH=..\dist
) else if exist "dist\EdgeNodeLauncher.exe" (
    set EXE_FOUND=1
    set EXE_PATH=dist\EdgeNodeLauncher.exe
    set DIST_PATH=dist
)

if %EXE_FOUND% EQU 0 (
    echo ERROR: EdgeNodeLauncher.exe not found in dist folder. 
    echo Please run win32_build.bat first to generate the executable.
    exit /b 1
)

REM Ensure dist folder exists
if not exist "%DIST_PATH%" mkdir "%DIST_PATH%"

REM Get version from ver.py
if exist "..\ver.py" (
    for /f "tokens=2 delims=''" %%v in ('type ..\ver.py') do set VERSION=%%v
) else if exist "ver.py" (
    for /f "tokens=2 delims=''" %%v in ('type ver.py') do set VERSION=%%v
) else (
    echo ERROR: ver.py not found
    exit /b 1
)

echo Using version: %VERSION%

REM Update the version in the WiX file
powershell -Command "(Get-Content EdgeNodeLauncher.wxs) -replace 'Version=\"1.0.0\"', 'Version=\"%VERSION%\"' | Set-Content EdgeNodeLauncher.wxs"
powershell -Command "(Get-Content EdgeNodeLauncher.wxs) -replace 'Your Company', 'Ratio One' | Set-Content EdgeNodeLauncher.wxs"

REM Create License.rtf if it doesn't exist
if not exist "License.rtf" (
    echo Creating placeholder License.rtf file...
    echo {\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1033{\fonttbl{\f0\fnil\fcharset0 Calibri;}} > License.rtf
    echo {\*\generator Riched20 10.0.19041}\viewkind4\uc1 >> License.rtf
    echo \pard\sa200\sl276\slmult1\f0\fs22\lang9 License for EdgeNodeLauncher v%VERSION%\par >> License.rtf
    echo \par >> License.rtf
    echo Copyright (c) Ratio One\par >> License.rtf
    echo \par >> License.rtf
    echo All rights reserved.\par >> License.rtf
    echo } >> License.rtf
)

echo Building MSI installer...

REM Compile WiX source file
echo Compiling WiX source file...
candle EdgeNodeLauncher.wxs -dSourcePath=%EXE_PATH%
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: WiX compilation failed.
    exit /b 1
)

REM Link WiX objects - output directly to dist folder
echo Linking WiX objects...
light -ext WixUIExtension EdgeNodeLauncher.wixobj -out %DIST_PATH%\EdgeNodeLauncher.msi
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: WiX linking failed.
    exit /b 1
)

REM Create versioned copy of the MSI inside dist folder
copy %DIST_PATH%\EdgeNodeLauncher.msi %DIST_PATH%\EdgeNodeLauncher-v%VERSION%.msi
echo MSI installer created successfully: %DIST_PATH%\EdgeNodeLauncher.msi and %DIST_PATH%\EdgeNodeLauncher-v%VERSION%.msi

endlocal 
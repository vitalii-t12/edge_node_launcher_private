@echo off
setlocal EnableDelayedExpansion

REM Default build type
set BUILD_EXE=1
set BUILD_MSI=0

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :end_parse_args
if /i "%~1"=="--exe" (
    set BUILD_EXE=1
    set BUILD_MSI=0
) else if /i "%~1"=="--msi" (
    set BUILD_EXE=0
    set BUILD_MSI=1
) else if /i "%~1"=="--both" (
    set BUILD_EXE=1
    set BUILD_MSI=1
) else (
    echo Unknown option: %~1
    echo Usage: %0 [--exe^|--msi^|--both]
    exit /b 1
)
shift
goto :parse_args
:end_parse_args

REM Your base PyInstaller command
set PYINSTALLER_CMD=pyinstaller -w --onefile -n "EdgeNodeLauncher" --icon=assets\r1_icon.ico main.py
set APP_NAME=EdgeNodeLauncher
set OUTPUT_DIR=dist

REM Build EXE if requested
if %BUILD_EXE%==1 (
    echo Building EXE package...
    echo %PYINSTALLER_CMD%
    %PYINSTALLER_CMD%
    if errorlevel 1 (
        echo Failed to build EXE package.
        exit /b 1
    )
    echo EXE package built successfully.
)

REM Build MSI if requested
if %BUILD_MSI%==1 (
    echo Building MSI installer...
    
    REM Check if WiX toolset is installed
    where candle >nul 2>&1
    if errorlevel 1 (
        echo Error: WiX Toolset not found. Please install WiX Toolset v3.11 or later.
        echo Download from: https://wixtoolset.org/releases/
        exit /b 1
    )
    
    REM Create temporary WiX files directory
    if not exist wix mkdir wix
    
    REM Create WiX source file
    echo ^<?xml version="1.0" encoding="UTF-8"?^> > wix\product.wxs
    echo ^<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi"^> >> wix\product.wxs
    echo     ^<Product Id="*" Name="%APP_NAME%" Language="1033" Version="1.0.0.0" Manufacturer="Your Company" UpgradeCode="61DAB716-7CE9-4F67-BC46-7ADB96FB074A"^> >> wix\product.wxs
    echo         ^<Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine" /^> >> wix\product.wxs
    echo         ^<MajorUpgrade DowngradeErrorMessage="A newer version of [ProductName] is already installed." /^> >> wix\product.wxs
    echo         ^<MediaTemplate EmbedCab="yes" /^> >> wix\product.wxs
    echo         ^<Feature Id="ProductFeature" Title="%APP_NAME%" Level="1"^> >> wix\product.wxs
    echo             ^<ComponentGroupRef Id="ProductComponents" /^> >> wix\product.wxs
    echo         ^</Feature^> >> wix\product.wxs
    echo         ^<Icon Id="AppIcon.ico" SourceFile="assets\r1_icon.ico"/^> >> wix\product.wxs
    echo         ^<Property Id="ARPPRODUCTICON" Value="AppIcon.ico" /^> >> wix\product.wxs
    echo         ^<Property Id="ARPHELPLINK" Value="https://your-company-website.com" /^> >> wix\product.wxs
    echo         ^<Property Id="ARPURLINFOABOUT" Value="https://your-company-website.com/about" /^> >> wix\product.wxs
    echo         ^<UIRef Id="WixUI_Minimal" /^> >> wix\product.wxs
    echo         ^<WixVariable Id="WixUIDialogBmp" Value="assets\r1_icon.png" /^> >> wix\product.wxs
    echo         ^<WixVariable Id="WixUIBannerBmp" Value="assets\r1_icon.png" /^> >> wix\product.wxs
    echo         ^<Directory Id="TARGETDIR" Name="SourceDir"^> >> wix\product.wxs
    echo             ^<Directory Id="ProgramFilesFolder"^> >> wix\product.wxs
    echo                 ^<Directory Id="INSTALLFOLDER" Name="%APP_NAME%"^> >> wix\product.wxs
    echo                     ^<Component Id="ApplicationComponent" Guid="*"^> >> wix\product.wxs
    echo                         ^<File Id="ApplicationExecutable" Source="%OUTPUT_DIR%\%APP_NAME%.exe" KeyPath="yes"^> >> wix\product.wxs
    echo                             ^<Shortcut Id="ApplicationStartMenuShortcut" Directory="ProgramMenuDir" Name="%APP_NAME%" WorkingDirectory="INSTALLFOLDER" Advertise="yes" Icon="AppIcon.ico" /^> >> wix\product.wxs
    echo                             ^<Shortcut Id="ApplicationDesktopShortcut" Directory="DesktopFolder" Name="%APP_NAME%" WorkingDirectory="INSTALLFOLDER" Advertise="yes" Icon="AppIcon.ico" /^> >> wix\product.wxs
    echo                         ^</File^> >> wix\product.wxs
    echo                     ^</Component^> >> wix\product.wxs
    echo                 ^</Directory^> >> wix\product.wxs
    echo             ^</Directory^> >> wix\product.wxs
    echo             ^<Directory Id="ProgramMenuFolder"^> >> wix\product.wxs
    echo                 ^<Directory Id="ProgramMenuDir" Name="%APP_NAME%"^> >> wix\product.wxs
    echo                     ^<Component Id="ProgramMenuDir" Guid="*"^> >> wix\product.wxs
    echo                         ^<RemoveFolder Id="ProgramMenuDir" On="uninstall" /^> >> wix\product.wxs
    echo                         ^<RegistryValue Root="HKCU" Key="Software\[Manufacturer]\[ProductName]" Type="string" Value="" KeyPath="yes" /^> >> wix\product.wxs
    echo                     ^</Component^> >> wix\product.wxs
    echo                 ^</Directory^> >> wix\product.wxs
    echo             ^</Directory^> >> wix\product.wxs
    echo             ^<Directory Id="DesktopFolder" Name="Desktop" /^> >> wix\product.wxs
    echo         ^</Directory^> >> wix\product.wxs
    echo         ^<ComponentGroup Id="ProductComponents"^> >> wix\product.wxs
    echo             ^<ComponentRef Id="ApplicationComponent" /^> >> wix\product.wxs
    echo             ^<ComponentRef Id="ProgramMenuDir" /^> >> wix\product.wxs
    echo         ^</ComponentGroup^> >> wix\product.wxs
    echo     ^</Product^> >> wix\product.wxs
    echo ^</Wix^> >> wix\product.wxs
    
    REM Check for WiX UI Extension
    echo Checking for WiX UI Extension...
    where light >nul 2>&1
    if not errorlevel 1 (
        set "LIGHT_ARGS=-ext WixUIExtension"
    ) else (
        set "LIGHT_ARGS="
        echo Warning: WixUIExtension not found. Installer will not have a custom UI.
    )
    
    echo Linking MSI installer...
    light %LIGHT_ARGS% -out %OUTPUT_DIR%\%APP_NAME%.msi wix\product.wixobj
    if errorlevel 1 (
        echo Failed to link MSI installer.
        exit /b 1
    )
    
    echo MSI installer built successfully.
)

echo.
echo Build summary:
if %BUILD_EXE%==1 echo - EXE package: %OUTPUT_DIR%\%APP_NAME%.exe
if %BUILD_MSI%==1 echo - MSI installer: %OUTPUT_DIR%\%APP_NAME%.msi
echo.

endlocal
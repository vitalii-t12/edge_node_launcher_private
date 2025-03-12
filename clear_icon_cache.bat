@echo off
echo This script will clear the Windows icon cache to force refresh of application icons.
echo Administrative privileges are required.
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script requires administrative privileges.
    echo Please right-click and select "Run as administrator".
    pause
    exit /b 1
)

echo Stopping Windows Explorer...
taskkill /f /im explorer.exe

echo Clearing icon cache...
REM Delete icon cache files
del /f /s /q %localappdata%\IconCache.db
del /f /s /q %localappdata%\Microsoft\Windows\Explorer\iconcache*

REM Clear the thumbnail cache
del /f /s /q %localappdata%\Microsoft\Windows\Explorer\thumbcache*

echo Restarting Windows Explorer...
start explorer.exe

echo.
echo Icon cache cleared successfully!
echo.
echo If your application still shows the old icon:
echo 1. Right-click the application shortcut and select Properties
echo 2. Click "Change Icon..." and browse to assets\r1_icon.ico
echo 3. Click OK and Apply
echo.
pause 
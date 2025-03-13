@echo off
REM Post-build script to update shortcuts with the correct icon and configure silent execution

echo Running post-build tasks...

REM Check if Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Make sure Python is installed and in your PATH.
    exit /b 1
)

REM Check for required Python packages
python -c "import winshell, win32com.client" 2>nul
if errorlevel 1 (
    echo Installing required Python packages...
    pip install pywin32 winshell
)

REM Create shortcuts with the correct icon and no-console option
echo Creating shortcuts with the correct icon...
python "%~dp0\..\create_shortcut.py"

REM Create a launcher script to suppress console windows
echo Creating no-console launcher...
echo @echo off > "%~dp0\..\dist\launch_silent.bat"
echo start /b "" "%%~dp0EdgeNodeLauncher.exe" %%* >> "%~dp0\..\dist\launch_silent.bat"
echo echo EdgeNodeLauncher started without console window >> "%~dp0\..\dist\launch_silent.bat"

REM Clear icon cache (with admin privileges warning)
echo.
echo To clear the Windows icon cache and ensure the new icon appears:
echo 1. Run the clear_icon_cache.bat script with administrator privileges
echo 2. This will restart Windows Explorer to refresh all icons
echo.

REM Ask if user wants to run the cache clearing script
set /p RUN_CACHE_SCRIPT=Do you want to clear the icon cache now? (Y/N): 
if /i "%RUN_CACHE_SCRIPT%"=="Y" (
    echo Running icon cache clearing script...
    "%~dp0\clear_icon_cache.bat"
) else (
    echo Skipping icon cache clearing.
    echo You can run build_scripts\clear_icon_cache.bat manually later if needed.
)

echo.
echo Post-build tasks completed successfully.
echo.
echo NOTE: If you are still seeing terminal windows when running the app:
echo 1. Use the created "EdgeNodeLauncher (No Console)" shortcut
echo 2. Or run the app using "launch_silent.bat" in the dist folder
echo.

exit /b 0 
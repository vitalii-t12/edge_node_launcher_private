@echo off
REM Post-build script to update shortcuts with the correct icon

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

REM Create shortcuts with the correct icon
echo Creating shortcuts with the correct icon...
python create_shortcut.py

echo Post-build tasks completed successfully. 
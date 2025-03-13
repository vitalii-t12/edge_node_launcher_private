#!/bin/bash

# Detect platform
PLATFORM=$(uname)

# Set icon path based on platform
if [[ "$PLATFORM" == "Darwin" ]]; then
    # macOS uses .icns format
    ICON_PATH="assets/r1_icon.icns"
else
    # Linux/Ubuntu uses .png format
    ICON_PATH="assets/r1_icon.png"
fi

# Your base PyInstaller command with platform-specific icon
PYINSTALLER_CMD="pyinstaller -w --onefile -n 'EdgeNodeLauncher' --icon=$ICON_PATH main.py"

# Combine the base command with the hidden imports and execute
echo "$PYINSTALLER_CMD"
eval "$PYINSTALLER_CMD"

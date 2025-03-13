"""
Shortcut Creator for Edge Node Launcher

This script creates a Windows shortcut with the correct icon and settings.
Run this script after installation to ensure shortcuts have the right icon.
"""

import os
import sys
import subprocess
import winshell
from win32com.client import Dispatch

def create_shortcut(target_path, shortcut_path, icon_path=None, description=None):
    """Create a Windows shortcut with the specified icon and description."""
    print(f"Creating shortcut: {shortcut_path}")
    print(f"Target: {target_path}")
    print(f"Icon: {icon_path}")
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    
    if icon_path:
        shortcut.IconLocation = icon_path
    
    if description:
        shortcut.Description = description
    
    shortcut.save()
    print(f"Shortcut created successfully")
    return shortcut_path

def create_app_shortcuts(exe_path, icon_path=None):
    """Create shortcuts for the application on desktop and start menu."""
    if not os.path.exists(exe_path):
        print(f"Error: Executable not found at {exe_path}")
        return False
    
    app_name = os.path.basename(exe_path).replace('.exe', '')
    description = f"Launch {app_name}"
    
    # If icon_path is not specified, use the exe itself as the icon source
    if not icon_path or not os.path.exists(icon_path):
        print(f"Warning: Icon file not found, using executable as icon source")
        icon_path = f"{exe_path},0"
    else:
        print(f"Using icon from: {icon_path}")
    
    # Create desktop shortcut
    desktop_path = winshell.desktop()
    desktop_shortcut = os.path.join(desktop_path, f"{app_name}.lnk")
    create_shortcut(exe_path, desktop_shortcut, icon_path, description)
    
    # Create start menu shortcut
    start_menu_path = os.path.join(winshell.start_menu(), "Programs", app_name)
    if not os.path.exists(start_menu_path):
        os.makedirs(start_menu_path)
    start_menu_shortcut = os.path.join(start_menu_path, f"{app_name}.lnk")
    create_shortcut(exe_path, start_menu_shortcut, icon_path, description)
    
    # Create additional shortcut that suppresses console windows
    # This sets the shortcut to run minimized/hidden
    launcher_shortcut = os.path.join(start_menu_path, f"{app_name} (No Console).lnk")
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(launcher_shortcut)
    shortcut.Targetpath = exe_path
    shortcut.WorkingDirectory = os.path.dirname(exe_path)
    shortcut.IconLocation = icon_path
    shortcut.Description = f"Launch {app_name} without console windows"
    # Set window style to minimized
    shortcut.WindowStyle = 7  # 7 = Minimized
    shortcut.save()
    
    return True

if __name__ == "__main__":
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get paths
    exe_path = os.path.join(script_dir, "dist", "EdgeNodeLauncher.exe")
    icon_path = os.path.join(script_dir, "assets", "r1_icon.ico")
    
    print(f"Script directory: {script_dir}")
    print(f"Creating shortcuts for: {exe_path}")
    print(f"Using icon: {icon_path}")
    
    if not os.path.exists(exe_path):
        print(f"Executable not found at {exe_path}")
        # Try alternate path for installed app
        alt_exe_path = os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 
                                   "EdgeNodeLauncher", "EdgeNodeLauncher.exe")
        if os.path.exists(alt_exe_path):
            exe_path = alt_exe_path
            print(f"Using alternate executable path: {exe_path}")
        else:
            print(f"Executable not found. Please build the application first.")
            sys.exit(1)
    
    if not os.path.exists(icon_path):
        print(f"Warning: Icon file not found at {icon_path}")
        # Try alternate paths
        alt_icon_paths = [
            os.path.join(os.path.dirname(exe_path), "assets", "r1_icon.ico"),
            os.path.join(os.path.dirname(exe_path), "r1_icon.ico")
        ]
        for alt_path in alt_icon_paths:
            if os.path.exists(alt_path):
                icon_path = alt_path
                print(f"Using alternate icon path: {icon_path}")
                break
        else:
            print("Using executable's embedded icon as fallback")
            icon_path = None
    
    if create_app_shortcuts(exe_path, icon_path):
        print("Shortcuts created successfully.")
    else:
        print("Failed to create shortcuts.") 
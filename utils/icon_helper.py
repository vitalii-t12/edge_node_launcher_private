"""
Icon Helper Module for Edge Node Launcher

This module handles consistent icon loading across the application
and ensures proper fallbacks for all execution environments.
"""

import os
import sys
from PyQt5.QtGui import QIcon, QPixmap
import base64

def get_absolute_path(relative_path):
    """Get absolute path to a resource, works in both dev and PyInstaller environments"""
    if hasattr(sys, '_MEIPASS'):  # PyInstaller environment
        base_path = sys._MEIPASS
    else:
        # If we're running in development environment
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    return os.path.join(base_path, relative_path)

def get_app_icon():
    """Get the application icon with multiple fallback methods"""
    # Search in multiple locations
    icon_paths = []
    
    # Add platform-specific paths
    if sys.platform == 'win32':  # Windows
        icon_paths.extend([
            get_absolute_path(os.path.join('assets', 'r1_icon.ico')),
            os.path.join(os.getcwd(), 'assets', 'r1_icon.ico'),
            os.path.abspath('assets/r1_icon.ico')
        ])
    elif sys.platform == 'darwin':  # macOS
        icon_paths.extend([
            get_absolute_path(os.path.join('assets', 'r1_icon.icns')),
            os.path.join(os.getcwd(), 'assets', 'r1_icon.icns'),
            os.path.abspath('assets/r1_icon.icns')
        ])
    else:  # Linux and other platforms
        icon_paths.extend([
            get_absolute_path(os.path.join('assets', 'r1_icon.png')),
            os.path.join(os.getcwd(), 'assets', 'r1_icon.png'),
            os.path.abspath('assets/r1_icon.png')
        ])
    
    # Add fallback paths for all platforms
    icon_paths.extend([
        get_absolute_path(os.path.join('assets', 'r1_icon.png')),
        get_absolute_path(os.path.join('assets', 'r1_icon.ico')),
        os.path.join(os.getcwd(), 'assets', 'r1_icon.png'),
        os.path.join(os.getcwd(), 'assets', 'r1_icon.ico'),
        os.path.abspath('assets/r1_icon.png'),
        os.path.abspath('assets/r1_icon.ico')
    ])
    
    # Try each path
    for path in icon_paths:
        if os.path.exists(path):
            print(f"Loading icon from: {path}")
            return QIcon(path)
    
    # Last resort: Use embedded icon from base64
    from utils.icon import ICON_BASE64
    print("Using embedded base64 icon as fallback")
    pixmap = QPixmap()
    pixmap.loadFromData(base64.b64decode(ICON_BASE64))
    return QIcon(pixmap)

def apply_icon_to_app(app):
    """Apply the icon to the QApplication instance"""
    icon = get_app_icon()
    app.setWindowIcon(icon)
    return icon 
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from app_forms.frm_main import EdgeNodeLauncher
from utils.icon_helper import apply_icon_to_app

if __name__ == '__main__':
    # Handle high DPI displays
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set app name for better integration
    app.setApplicationName("EdgeNodeLauncher")
    app.setOrganizationName("Naeural")
    
    # Apply icon from helper
    icon = apply_icon_to_app(app)
    
    # Set app ID for Windows
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("naeural.edge_node_launcher")
            print("Set Windows AppUserModelID for taskbar icon")
        except Exception as e:
            print(f"Error setting AppUserModelID: {e}")
    
    # Create and show the main window
    manager = EdgeNodeLauncher(icon)
    manager.show()
    
    # Start the event loop
    sys.exit(app.exec_())


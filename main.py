import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from app_forms.frm_main import EdgeNodeLauncher

# Get the absolute path to the application directory
app_dir = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
  app = QApplication(sys.argv)
  
  # Set application-wide icon for all platforms using absolute paths
  if sys.platform == 'win32':  # Windows
      icon_path = os.path.join(app_dir, 'assets', 'r1_icon.ico')
  elif sys.platform == 'darwin':  # macOS
      icon_path = os.path.join(app_dir, 'assets', 'r1_icon.icns')
  else:  # Linux and other platforms
      icon_path = os.path.join(app_dir, 'assets', 'r1_icon.png')
      
  print(f"Looking for icon at: {icon_path}")
  if os.path.exists(icon_path):
      print(f"Icon found at {icon_path}, setting application icon")
      app_icon = QIcon(icon_path)
      app.setWindowIcon(app_icon)
  else:
      print(f"Warning: Icon file not found at {icon_path}")
  
  manager = EdgeNodeLauncher(app_icon if 'app_icon' in locals() else None)
  manager.show()
  sys.exit(app.exec_())


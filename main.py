import sys
from PyQt5.QtWidgets import QApplication
from app_forms.frm_main import EdgeNodeLauncher
                             
if __name__ == '__main__':
  app = QApplication(sys.argv)
  manager = EdgeNodeLauncher()
  manager.show()
  sys.exit(app.exec_())

import sys
from PyQt5.QtWidgets import QApplication
from app_forms.frm_main import EdgeNodeManager
                             
if __name__ == '__main__':
  app = QApplication(sys.argv)
  manager = EdgeNodeManager()
  manager.show()
  sys.exit(app.exec_())

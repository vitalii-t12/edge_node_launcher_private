
import sys
import base64
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QAbstractButton, QCheckBox, QRadioButton
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtGui import QPainter, QColor, QBrush
from pyqtgraph import AxisItem


def get_icon_from_base64(base64_str):
  icon_data = base64.b64decode(base64_str)
  pixmap = QPixmap()
  pixmap.loadFromData(icon_data)
  return QIcon(pixmap)

class DateAxisItem(AxisItem):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.setLabel(text='Time')

  def tickStrings(self, values, scale, spacing):
    return [datetime.fromtimestamp(value).strftime("%H:%M:%S") for value in values]


class ToggleButtonApp1(QWidget):
  def __init__(self):
    super().__init__()

    self.initUI()

  def initUI(self):
    self.setWindowTitle('Styled Toggle Button Example')

    layout = QVBoxLayout()

    self.toggle_button = QCheckBox('OFF')
    self.toggle_button.setStyleSheet("""
      QCheckBox::indicator { width: 40px; height: 20px; }
      QCheckBox::indicator:unchecked { background-color: red; border-radius: 10px; }
      QCheckBox::indicator:checked { background-color: green; border-radius: 10px; }
      QCheckBox::indicator:unchecked:pressed { background-color: lightcoral; }
      QCheckBox::indicator:checked:pressed { background-color: lightgreen; }
    """)
    self.toggle_button.setChecked(False)
    self.toggle_button.toggled.connect(self.toggle_button_clicked)

    layout.addWidget(self.toggle_button)

    self.setLayout(layout)
    self.show()

  def toggle_button_clicked(self):
    if self.toggle_button.isChecked():
      self.toggle_button.setText('ON')
    else:
      self.toggle_button.setText('OFF')
      
      
class ToggleButtonApp2(QWidget):
  def __init__(self):
    super().__init__()

    self.initUI()

  def initUI(self):
    self.setWindowTitle('Styled Toggle Button Example')

    layout = QVBoxLayout()

    self.toggle_button = QRadioButton('OFF')
    self.toggle_button.setStyleSheet("""
      QRadioButton::indicator { width: 40px; height: 20px; }
      QRadioButton::indicator:unchecked { background-color: red; border-radius: 10px; }
      QRadioButton::indicator:checked { background-color: green; border-radius: 10px; }
      QRadioButton::indicator:unchecked:pressed { background-color: lightcoral; }
      QRadioButton::indicator:checked:pressed { background-color: lightgreen; }
    """)
    self.toggle_button.setChecked(False)
    self.toggle_button.toggled.connect(self.toggle_button_clicked)

    layout.addWidget(self.toggle_button)

    self.setLayout(layout)
    self.show()

  def toggle_button_clicked(self):
    if self.toggle_button.isChecked():
      self.toggle_button.setText('ON')
    else:
      self.toggle_button.setText('OFF')      
      
class ToggleButton3(QAbstractButton):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setCheckable(True)
    self._background_color = QColor(255, 0, 0)
    self._circle_color = QColor(255, 255, 255)
    self._circle_position = 3

    self.anim = QPropertyAnimation(self, b"circle_position", self)
    self.anim.setDuration(200)

    self.setFixedSize(50, 25)

  def paintEvent(self, event):
    rect = self.rect()
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(self._background_color))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(0, 0, rect.width(), rect.height(), rect.height() // 2, rect.height() // 2)
    painter.setBrush(QBrush(self._circle_color))
    painter.drawEllipse(self._circle_position, 3, rect.height() - 6, rect.height() - 6)

  def mouseReleaseEvent(self, event):
    if self.rect().contains(event.pos()):
      self.setChecked(not self.isChecked())
      self.anim.setStartValue(self._circle_position)
      self.anim.setEndValue(3 if not self.isChecked() else self.width() - self.height() + 3)
      self.anim.start()
    super().mouseReleaseEvent(event)

  def setBackgroundColor(self, color):
    self._background_color = QColor(color)
    self.update()

  def setCircleColor(self, color):
    self._circle_color = QColor(color)
    self.update()

  def get_circle_position(self):
    return self._circle_position

  def set_circle_position(self, pos):
    self._circle_position = pos
    self.update()

  circle_position = property(get_circle_position, set_circle_position)


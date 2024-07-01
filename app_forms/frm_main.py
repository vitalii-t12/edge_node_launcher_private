import sys
import os
import json
import base64

from PyQt5.QtWidgets import (
  QApplication, 
  QWidget, 
  QVBoxLayout, 
  QPushButton, 
  QLabel, 
  QMessageBox, 
  QTextEdit, 
  QDialog, 
  QHBoxLayout, 
  QStackedWidget, 
  QFrame, 
  QGridLayout, 
  QSpacerItem, 
  QSizePolicy
  
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime

from utils.const import *
from utils.docker import _DockerUtilsMixin

from utils.icon import ICON_BASE64


def get_icon_from_base64(base64_str):
  icon_data = base64.b64decode(base64_str)
  pixmap = QPixmap()
  pixmap.loadFromData(icon_data)
  return QIcon(pixmap)


class EdgeNodeManager(QWidget, _DockerUtilsMixin):
  def __init__(self):
    super().__init__()

    if not self.check_docker():
      sys.exit(1)
    
    self.initUI()
    self.timer = QTimer(self)
    self.timer.timeout.connect(self.refresh_all)
    self.timer.start(5_000)  # Refresh every 10 seconds

    self.plot_data()  # Initial plot
    return
  
  def center(self):
    screen_geometry = QApplication.desktop().screenGeometry()
    x = (screen_geometry.width() - self.width()) // 2
    y = (screen_geometry.height() - self.height()) // 2
    self.move(x, y)
    return


  def initUI(self):
    HEIGHT = 1100
    self.setWindowTitle(WINDOW_TITLE)
    self.setGeometry(0, 0, 1800, HEIGHT)
    
    self.center()


    main_layout = QHBoxLayout(self)

    # Left menu layout with fixed width
    menu_widget = QWidget()
    menu_widget.setFixedWidth(300)  # Set the fixed width here
    menu_layout = QVBoxLayout(menu_widget)
    menu_layout.setAlignment(Qt.AlignTop)
    
    top_button_area = QVBoxLayout()

    self.toggleButton = QPushButton(LAUNCH_CONTAINER_BUTTON_TEXT)
    self.toggleButton.clicked.connect(self.toggle_container)
    top_button_area.addWidget(self.toggleButton)

    menu_layout.addLayout(top_button_area)

    # Spacer to push bottom_button_area to the bottom
    menu_layout.addSpacerItem(QSpacerItem(20, int(HEIGHT * 0.75) , QSizePolicy.Minimum, QSizePolicy.Expanding))

    # Add a horizontal line
    horizontal_line = QFrame()
    horizontal_line.setFrameShape(QFrame.HLine)
    horizontal_line.setFrameShadow(QFrame.Sunken)
    menu_layout.addWidget(horizontal_line)

    # Bottom button area
    bottom_button_area = QVBoxLayout()

    self.addressDisplay = QLabel('')
    self.addressDisplay.setFont(QFont("Courier New"))
    bottom_button_area.addWidget(self.addressDisplay)

    self.nameDisplay = QLabel('')
    self.nameDisplay.setFont(QFont("Courier New"))
    bottom_button_area.addWidget(self.nameDisplay)
    
    self.copyButton = QPushButton(COPY_ADDRESS_BUTTON_TEXT)
    self.copyButton.clicked.connect(self.copy_address)
    bottom_button_area.addWidget(self.copyButton)

    self.envEditButton = QPushButton(EDIT_ENV_BUTTON_TEXT)
    self.envEditButton.clicked.connect(self.edit_env_file)
    bottom_button_area.addWidget(self.envEditButton)
    
    self.deleteButton = QPushButton(DELETE_AND_RESTART_BUTTON_TEXT)
    self.deleteButton.clicked.connect(self.delete_and_restart)
    bottom_button_area.addWidget(self.deleteButton)

    bottom_button_area.addStretch()
    menu_layout.addLayout(bottom_button_area)
    
    main_layout.addWidget(menu_widget)  # Add the fixed-width widget

    # Right side layout (stacked widget for main view and graphs)
    self.stack = QStackedWidget(self)
    
    self.mainView = QWidget()
    main_layout_2 = QVBoxLayout()
    self.localAddressLabelMain = QLabel(LOCAL_NODE_ADDRESS_LABEL_TEXT)
    main_layout_2.addWidget(self.localAddressLabelMain)
    self.addressDisplayMain = QLabel('')
    main_layout_2.addWidget(self.addressDisplayMain)
    self.mainView.setLayout(main_layout_2)
    
    self.graphView = QWidget()
    graph_layout = QGridLayout()
    self.fig_cpu = Figure(facecolor='#243447')
    self.canvas_cpu = FigureCanvas(self.fig_cpu)
    self.fig_memory = Figure(facecolor='#243447')
    self.canvas_memory = FigureCanvas(self.fig_memory)
    self.fig_gpu = Figure(facecolor='#243447')
    self.canvas_gpu = FigureCanvas(self.fig_gpu)
    self.fig_gpu_memory = Figure(facecolor='#243447')
    self.canvas_gpu_memory = FigureCanvas(self.fig_gpu_memory)
    
    graph_layout.addWidget(self.canvas_cpu, 0, 0)
    graph_layout.addWidget(self.canvas_memory, 0, 1)
    graph_layout.addWidget(self.canvas_gpu, 1, 0)
    graph_layout.addWidget(self.canvas_gpu_memory, 1, 1)
    
    self.graphView.setLayout(graph_layout)
    
    self.stack.addWidget(self.mainView)
    self.stack.addWidget(self.graphView)
    
    main_layout.addWidget(self.stack, 3)

    self.setLayout(main_layout)
    self.refresh_local_address()
    self.apply_stylesheet()
    
    self.setWindowIcon(get_icon_from_base64(ICON_BASE64))
    return



  def apply_stylesheet(self):
    self.setStyleSheet("""
      QPushButton {
        background-color: #1E90FF; 
        color: white; 
        border: 2px solid #87CEEB; 
        padding: 10px 20px; 
        font-size: 16px; 
        margin: 4px 2px;
        border-radius: 15px;
      }
      QPushButton:hover {
        background-color: #104E8B;
      }
      QLabel {
        font-size: 16px;
        color: white;
        margin: 10px 2px;
      }
      QWidget {
        background-color: #0D1F2D;
      }
      QFrame {
        background-color: #0D1F2D;
      }
      QVBoxLayout, QHBoxLayout {
        background-color: #0D1F2D;
      }
    """)


  def toggle_container(self):
    if self.is_container_running():
      self.stop_container()
    else:
      self.launch_container()
    self.update_toggle_button_text()
    return


  def update_toggle_button_text(self):
    if self.is_container_running():
      self.toggleButton.setText(STOP_CONTAINER_BUTTON_TEXT)
    else:
      self.toggleButton.setText(LAUNCH_CONTAINER_BUTTON_TEXT)
    return


  def edit_env_file(self):
    env_content = ''
    try:
        with open(self.env_file, 'r') as file:
            env_content = file.read()
    except FileNotFoundError:
        pass

    # Create the text edit widget with Courier New font and light font color
    text_edit = QTextEdit()
    text_edit.setText(env_content)
    text_edit.setFont(QFont("Courier New", 12))
    text_edit.setStyleSheet("color: #FFFFFF; background-color: #0D1F2D;")

    # Create the dialog
    dialog = QDialog(self)
    dialog.setWindowTitle('Edit .env File')
    dialog.setGeometry(0, 0, 1000, 900)  # Enlarge the edit window

    # Center the dialog on the screen
    screen_geometry = QApplication.desktop().screenGeometry()
    x = (screen_geometry.width() - dialog.width()) // 2
    y = (screen_geometry.height() - dialog.height()) // 2
    dialog.move(x, y)

    dialog_layout = QVBoxLayout()
    dialog_layout.addWidget(text_edit)

    # Save button
    save_button = QPushButton('Save')
    save_button.clicked.connect(lambda: self.save_env_file(text_edit.toPlainText(), dialog))
    dialog_layout.addWidget(save_button)

    dialog.setLayout(dialog_layout)
    dialog.exec_()
    return



  def save_env_file(self, content, dialog):
    with open(self.env_file, 'w') as file:
      file.write(content)
    dialog.accept()
    return


  def plot_data(self):
    data_path = os.path.join(self.volume_path, LOCAL_HISTORY_FILE)
    try:
      if os.path.exists(data_path):
        with open(data_path, 'r') as file:
          data = json.load(file)
        self.plot_graphs(data)
      else:
        self.plot_graphs(None)
    except FileNotFoundError:
      self.plot_graphs(None)
    return  


  def plot_graphs(self, data):
    self.stack.setCurrentIndex(1)

    timestamps = [datetime.fromisoformat(ts) for ts in data['timestamps']] if data and 'timestamps' in data else []

    def setup_axis(ax, title, xlabel, ylabel):
      ax.set_facecolor('#243447')
      ax.set_title(title, color='white')
      ax.set_xlabel(xlabel, color='white')
      ax.set_ylabel(ylabel, color='white')
      if timestamps:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax.xaxis.set_major_locator(mdates.SecondLocator(interval=60))
        ax.xaxis.set_minor_locator(mdates.SecondLocator(interval=10))
        ax.tick_params(axis='x', colors='white', which='major')
        ax.tick_params(axis='y', colors='white')
        ax.tick_params(axis='x', which='minor', length=4, color='white')
        ax.tick_params(which='both', width=1)
        ax.tick_params(which='major', length=7)
      return

    def plot_graph(ax, timestamps, values, label, color):
      if timestamps and values:
        ax.plot(timestamps, values, label=label, color=color)
        ax.legend()
      else:
        ax.text(0.5, 0.5, 'NO DATA', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, color='white')

    # Plot CPU Load
    self.fig_cpu.clear()
    ax_cpu = self.fig_cpu.add_subplot(111)
    setup_axis(ax_cpu, 'CPU Load', 'Timestamp', 'Load (%)')
    plot_graph(ax_cpu, timestamps, data.get('cpu_load', []) if data else [], 'CPU Load', 'white')
    self.canvas_cpu.draw()

    # Plot Memory Load
    self.fig_memory.clear()
    ax_memory = self.fig_memory.add_subplot(111)
    setup_axis(ax_memory, 'Memory Load', 'Timestamp', 'Memory (GB)')
    plot_graph(ax_memory, timestamps, data.get('occupied_memory', []) if data else [], 'Occupied Memory', 'white')
    plot_graph(ax_memory, timestamps, data.get('total_memory', []) if data else [], 'Total Memory', 'yellow')
    self.canvas_memory.draw()

    # Plot GPU Load if available
    self.fig_gpu.clear()
    ax_gpu = self.fig_gpu.add_subplot(111)
    setup_axis(ax_gpu, 'GPU Load', 'Timestamp', 'Load (%)')
    plot_graph(ax_gpu, timestamps, data.get('gpu_load', []) if data else [], 'GPU Load', 'white')
    self.canvas_gpu.draw()

    # Plot GPU Memory Load if available
    self.fig_gpu_memory.clear()
    ax_gpu_memory = self.fig_gpu_memory.add_subplot(111)
    setup_axis(ax_gpu_memory, 'GPU Memory Load', 'Timestamp', 'Memory (GB)')
    plot_graph(ax_gpu_memory, timestamps, data.get('gpu_occupied_memory', []) if data else [], 'Occupied GPU Memory', 'white')
    plot_graph(ax_gpu_memory, timestamps, data.get('gpu_total_memory', []) if data else [], 'Total GPU Memory', 'yellow')
    self.canvas_gpu_memory.draw()

    return

    return



  def refresh_local_address(self):
    address_path = os.path.join(self.volume_path, LOCAL_ADDRESS_FILE)
    try:
      with open(address_path, 'r') as file:
        address_info = [x for x in file.read().split(' ') if len(x) > 0]
        self.node_addr = address_info[0]
        self.node_name = address_info[1] if len(address_info) > 1 else ''
        str_display = address_info[0][:8] + '...' + address_info[0][-8:]
        self.addressDisplay.setText('Addr: ' + str_display)
        self.nameDisplay.setText('Name: ' + address_info[1] if len(address_info) > 1 else '')
    except FileNotFoundError:
      self.addressDisplay.setText('Address file not found.')
      self.nameDisplay.setText('')
    return

  def copy_address(self):
    clipboard = QApplication.clipboard()
    clipboard.setText(self.addressDisplay.text())
    
    
  def refresh_all(self):
    self.refresh_local_address()
    self.plot_data()
    return    


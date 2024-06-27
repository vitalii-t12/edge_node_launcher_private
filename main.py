import sys
import os
import subprocess
import json
import platform
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, QTextEdit, QDialog, QHBoxLayout, QStackedWidget, QFrame, QGridLayout, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime

# Constants Section
ENV_FILE = '.env'
DOCKER_IMAGE = 'naeural/edge_node'
DOCKER_CONTAINER_NAME = 'edge_node_container'
WINDOWS_VOLUME_PATH = '\\\\wsl.localhost\\docker-desktop-data\\data\\docker\\volumes\\naeural_vol\\_data'
LINUX_VOLUME_PATH = '/var/lib/docker/volumes/naeural_vol/_data'
LOCAL_HISTORY_FILE = '_data/local_history.json'
E2_PEM_FILE = '_data/e2.pem'
LOCAL_ADDRESS_FILE = '_data/local_address.txt'
WINDOW_TITLE = 'Edge Node Manager'
EDIT_ENV_BUTTON_TEXT = 'Edit .env File'
LAUNCH_CONTAINER_BUTTON_TEXT = 'Launch Container'
STOP_CONTAINER_BUTTON_TEXT = 'Stop Container'
DELETE_AND_RESTART_BUTTON_TEXT = 'Delete e2.pem and Restart Container'
LOCAL_NODE_ADDRESS_LABEL_TEXT = 'Local Node Address'
REFRESH_LOCAL_ADDRESS_BUTTON_TEXT = 'Refresh Local Address'
COPY_ADDRESS_BUTTON_TEXT = 'Copy Address'

class EdgeNodeManager(QWidget):
  def __init__(self):
    super().__init__()

    self.env_file = ENV_FILE
    self.volume_path = self.get_volume_path()
    self.docker_image = DOCKER_IMAGE
    self.docker_container_name = DOCKER_CONTAINER_NAME

    if not self.check_docker():
      sys.exit(1)
    
    self.initUI()
    self.timer = QTimer(self)
    self.timer.timeout.connect(self.plot_data)
    self.timer.start(10000)  # Refresh every 10 seconds

    self.plot_data()  # Initial plot
    return

  def initUI(self):
    self.setWindowTitle(WINDOW_TITLE)
    self.setGeometry(100, 100, 1000, 800)

    main_layout = QHBoxLayout(self)

    # Left menu layout
    menu_layout = QVBoxLayout()
    menu_layout.setAlignment(Qt.AlignTop)
    
    top_button_area = QVBoxLayout()
    self.envEditButton = QPushButton(EDIT_ENV_BUTTON_TEXT)
    self.envEditButton.clicked.connect(self.edit_env_file)
    top_button_area.addWidget(self.envEditButton)

    self.toggleButton = QPushButton(LAUNCH_CONTAINER_BUTTON_TEXT)
    self.toggleButton.clicked.connect(self.toggle_container)
    top_button_area.addWidget(self.toggleButton)

    menu_layout.addLayout(top_button_area)

    menu_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    bottom_button_area = QVBoxLayout()
    self.localAddressLabel = QLabel(LOCAL_NODE_ADDRESS_LABEL_TEXT)
    bottom_button_area.addWidget(self.localAddressLabel)
    
    self.addressDisplay = QLabel('')
    self.addressDisplay.setFont(QFont("Courier New"))
    bottom_button_area.addWidget(self.addressDisplay)

    self.nameDisplay = QLabel('')
    self.nameDisplay.setFont(QFont("Courier New"))
    bottom_button_area.addWidget(self.nameDisplay)
    
    self.copyButton = QPushButton(COPY_ADDRESS_BUTTON_TEXT)
    self.copyButton.clicked.connect(self.copy_address)
    bottom_button_area.addWidget(self.copyButton)
    
    self.refreshButton = QPushButton(REFRESH_LOCAL_ADDRESS_BUTTON_TEXT)
    self.refreshButton.clicked.connect(self.refresh_local_address)
    bottom_button_area.addWidget(self.refreshButton)

    self.deleteButton = QPushButton(DELETE_AND_RESTART_BUTTON_TEXT)
    self.deleteButton.clicked.connect(self.delete_and_restart)
    bottom_button_area.addWidget(self.deleteButton)

    bottom_button_area.addStretch()
    menu_layout.addLayout(bottom_button_area)
    
    main_layout.addLayout(menu_layout, 1)

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

  def get_volume_path(self):
    if platform.system() == 'Windows':
      return WINDOWS_VOLUME_PATH
    else:
      return LINUX_VOLUME_PATH

  def check_docker(self):
    try:
      subprocess.check_output(['docker', '--version'])
      return True
    except subprocess.CalledProcessError:
      QMessageBox.warning(self, 'Docker Check', 'Docker is not installed. Please install Docker and restart the application.')
      return False

  def toggle_container(self):
    if self.is_container_running():
      self.stop_container()
    else:
      self.launch_container()
    self.update_toggle_button_text()

  def is_container_running(self):
    try:
      status = subprocess.check_output(['docker', 'inspect', '--format', '{{.State.Running}}', self.docker_container_name])
      return status.strip() == b'true'
    except subprocess.CalledProcessError:
      return False

  def update_toggle_button_text(self):
    if self.is_container_running():
      self.toggleButton.setText(STOP_CONTAINER_BUTTON_TEXT)
    else:
      self.toggleButton.setText(LAUNCH_CONTAINER_BUTTON_TEXT)

  def edit_env_file(self):
    env_content = ''
    try:
      with open(self.env_file, 'r') as file:
        env_content = file.read()
    except FileNotFoundError:
      pass
    
    text_edit = QTextEdit()
    text_edit.setText(env_content)
    
    dialog = QDialog(self)
    dialog.setWindowTitle('Edit .env File')
    dialog_layout = QVBoxLayout()
    dialog_layout.addWidget(text_edit)
    
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

  def launch_container(self):
    try:
      subprocess.check_call([
        'docker', 'run', '--gpus=all', '--env-file', self.env_file, '-v', 
        f'{self.volume_path}:/edge_node/_local_cache', '--name', self.docker_container_name, '-d', self.docker_image
      ])
      QMessageBox.information(self, 'Container Launch', 'Container launched successfully.')
    except subprocess.CalledProcessError:
      QMessageBox.warning(self, 'Container Launch', 'Failed to launch container.')
    return

  def stop_container(self):
    try:
      subprocess.check_call(['docker', 'stop', self.docker_container_name])
      subprocess.check_call(['docker', 'rm', self.docker_container_name])
      QMessageBox.information(self, 'Container Stop', 'Container stopped successfully.')
    except subprocess.CalledProcessError:
      QMessageBox.warning(self, 'Container Stop', 'Failed to stop container.')
    return

  def plot_data(self):
    data_path = os.path.join(self.volume_path, LOCAL_HISTORY_FILE)
    try:
      with open(data_path, 'r') as file:
        data = json.load(file)
      self.plot_graphs(data)
    except FileNotFoundError:
      QMessageBox.warning(self, 'Plot Data', f'{LOCAL_HISTORY_FILE} not found.')
    return  
    
  def plot_graphs(self, data):
    self.stack.setCurrentIndex(1)
    
    timestamps = [datetime.fromisoformat(ts) for ts in data['timestamps']]
    
    # Plot CPU Load
    self.fig_cpu.clear()
    ax_cpu = self.fig_cpu.add_subplot(111, facecolor='#243447')
    ax_cpu.plot(timestamps, data['cpu_load'], label='CPU Load', color='white')
    ax_cpu.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax_cpu.xaxis.set_major_locator(mdates.SecondLocator(interval=60))
    ax_cpu.xaxis.set_minor_locator(mdates.SecondLocator(interval=10))
    ax_cpu.set_title('CPU Load', color='white')
    ax_cpu.set_xlabel('Timestamp', color='white')
    ax_cpu.set_ylabel('Load (%)', color='white')
    ax_cpu.legend()
    ax_cpu.tick_params(axis='x', colors='white', which='major')
    ax_cpu.tick_params(axis='y', colors='white')
    ax_cpu.tick_params(axis='x', which='minor', length=4, color='white')
    ax_cpu.tick_params(which='both', width=1)
    ax_cpu.tick_params(which='major', length=7)
    self.canvas_cpu.draw()

    # Plot Memory Load
    self.fig_memory.clear()
    ax_memory = self.fig_memory.add_subplot(111, facecolor='#243447')
    ax_memory.plot(timestamps, data['occupied_memory'], label='Occupied Memory', color='white')
    ax_memory.plot(timestamps, data['total_memory'], label='Total Memory', color='yellow')
    ax_memory.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax_memory.xaxis.set_major_locator(mdates.SecondLocator(interval=60))
    ax_memory.xaxis.set_minor_locator(mdates.SecondLocator(interval=10))
    ax_memory.set_title('Memory Load', color='white')
    ax_memory.set_xlabel('Timestamp', color='white')
    ax_memory.set_ylabel('Memory (GB)', color='white')
    ax_memory.legend()
    ax_memory.tick_params(axis='x', colors='white', which='major')
    ax_memory.tick_params(axis='y', colors='white')
    ax_memory.tick_params(axis='x', which='minor', length=4, color='white')
    ax_memory.tick_params(which='both', width=1)
    ax_memory.tick_params(which='major', length=7)
    self.canvas_memory.draw()

    # Plot GPU Load if available
    if any(data['gpu_load']):
      self.fig_gpu.clear()
      ax_gpu = self.fig_gpu.add_subplot(111, facecolor='#243447')
      ax_gpu.plot(timestamps, data['gpu_load'], label='GPU Load', color='white')
      ax_gpu.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
      ax_gpu.xaxis.set_major_locator(mdates.SecondLocator(interval=60))
      ax_gpu.xaxis.set_minor_locator(mdates.SecondLocator(interval=10))
      ax_gpu.set_title('GPU Load', color='white')
      ax_gpu.set_xlabel('Timestamp', color='white')
      ax_gpu.set_ylabel('Load (%)', color='white')
      ax_gpu.legend()
      ax_gpu.tick_params(axis='x', colors='white', which='major')
      ax_gpu.tick_params(axis='y', colors='white')
      ax_gpu.tick_params(axis='x', which='minor', length=4, color='white')
      ax_gpu.tick_params(which='both', width=1)
      ax_gpu.tick_params(which='major', length=7)
      self.canvas_gpu.draw()

    # Plot GPU Memory Load if available
    if any(data['gpu_occupied_memory']):
      self.fig_gpu_memory.clear()
      ax_gpu_memory = self.fig_gpu_memory.add_subplot(111, facecolor='#243447')
      ax_gpu_memory.plot(timestamps, data['gpu_occupied_memory'], label='Occupied GPU Memory', color='white')
      ax_gpu_memory.plot(timestamps, data['gpu_total_memory'], label='Total GPU Memory', color='yellow')
      ax_gpu_memory.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
      ax_gpu_memory.xaxis.set_major_locator(mdates.SecondLocator(interval=60))
      ax_gpu_memory.xaxis.set_minor_locator(mdates.SecondLocator(interval=10))
      ax_gpu_memory.set_title('GPU Memory Load', color='white')
      ax_gpu_memory.set_xlabel('Timestamp', color='white')
      ax_gpu_memory.set_ylabel('Memory (GB)', color='white')
      ax_gpu_memory.legend()
      ax_gpu_memory.tick_params(axis='x', colors='white', which='major')
      ax_gpu_memory.tick_params(axis='y', colors='white')
      ax_gpu_memory.tick_params(axis='x', which='minor', length=4, color='white')
      ax_gpu_memory.tick_params(which='both', width=1)
      ax_gpu_memory.tick_params(which='major', length=7)
      self.canvas_gpu_memory.draw()



    return

  def delete_and_restart(self):
    pem_path = os.path.join(self.volume_path, E2_PEM_FILE)
    try:
      os.remove(pem_path)
      self.stop_container()
      self.launch_container()
      QMessageBox.information(self, 'Restart Container', f'{E2_PEM_FILE} deleted and container restarted.')
    except FileNotFoundError:
      QMessageBox.warning(self, 'Restart Container', f'{E2_PEM_FILE} not found.')
    return

  def refresh_local_address(self):
    address_path = os.path.join(self.volume_path, LOCAL_ADDRESS_FILE)
    try:
      with open(address_path, 'r') as file:
        address_info = file.read().split(' ', 1)
        self.addressDisplay.setText(address_info[0])
        self.nameDisplay.setText(address_info[1] if len(address_info) > 1 else '')
    except FileNotFoundError:
      self.addressDisplay.setText('Address file not found.')
      self.nameDisplay.setText('')
    return

  def copy_address(self):
    clipboard = QApplication.clipboard()
    clipboard.setText(self.addressDisplay.text())

if __name__ == '__main__':
  app = QApplication(sys.argv)
  manager = EdgeNodeManager()
  manager.show()
  sys.exit(app.exec_())

import platform
import subprocess
import os
import subprocess
import re

from collections import OrderedDict
from uuid import uuid4
from time import sleep
from PyQt5.QtWidgets import QMessageBox, QInputDialog

from .const import *

from PyQt5.QtWidgets import (
  QApplication, QDialog, QVBoxLayout, QLabel, QProgressBar,
  QTextEdit
)
from PyQt5.QtCore import Qt

from PyQt5.QtCore import QThread, pyqtSignal

class DockerPullThread(QThread):
  progress_update = pyqtSignal(str, int)
  pull_finished = pyqtSignal(bool)

  def __init__(self, image_name):
    super().__init__()
    self.image_name = image_name
    self.total_layers = 0
    self.pulled_layers = 0
    return


  def run(self):
    try:
      process = subprocess.Popen(['docker', 'pull', self.image_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
      
      for line in iter(process.stdout.readline, ''):
        self.parse_output(line)
        self.progress_update.emit(line.strip(), self.calculate_progress())
      
      process.stdout.close()
      process.wait()

      if process.returncode == 0:
        self.pull_finished.emit(True)
      else:
        self.pull_finished.emit(False)

    except subprocess.CalledProcessError:
      self.pull_finished.emit(False)
    return


  def parse_output(self, line):    
    DONE = [
      'Image is up to date',
      'Pull complete',
      'Already exists',
    ]
    START = [
      'Already exists',
      'Pulling fs layer',
      'Image is up to date',
    ]
    for d in DONE:
      if d in line:
        self.pulled_layers += 1
    for s in START:
      if s in line:
        self.total_layers += 1
    return


  def calculate_progress(self):
    if self.total_layers == 0:
      return 0
    return int((self.pulled_layers / self.total_layers) * 100)
  

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QTextEdit
from PyQt5.QtCore import Qt

class ProgressBarWindow(QDialog):
  def __init__(self, message, icon_object):
    super().__init__()
    self.setWindowTitle("Progress")
    self.setWindowIcon(icon_object)
    self.setWindowModality(Qt.ApplicationModal)
    self.setGeometry(300, 300, 600, 400)  # Larger size
    layout = QVBoxLayout()

    self.label = QLabel(message)
    layout.addWidget(self.label)

    self.output_edit = QTextEdit()
    self.output_edit.setReadOnly(True)
    layout.addWidget(self.output_edit)

    self.progress_bar = QProgressBar(self)
    self.progress_bar.setMaximum(100)
    layout.addWidget(self.progress_bar)

    self.setLayout(layout)
    self.apply_stylesheet()
    
    screen_geometry = QApplication.desktop().screenGeometry()
    x = (screen_geometry.width() - self.width()) // 2
    y = (screen_geometry.height() - self.height()) // 2
    self.move(x, y)
    return
  
  
  def update_progress(self, output, progress):
    self.output_edit.append(output)
    self.output_edit.verticalScrollBar().setValue(self.output_edit.verticalScrollBar().maximum())
    self.progress_bar.setValue(progress)

  def apply_stylesheet(self):
    self.setStyleSheet(STYLESHEET)
    return
  
  def on_docker_pull_finished(self, success):
    if success:
      QMessageBox.information(self, 'Docker Pull', 'Docker image pulled successfully.')
    else:
      QMessageBox.warning(self, 'Docker Pull', 'Failed to pull Docker image.')
    self.accept()  # Close the progress dialog
    return  



class _DockerUtilsMixin:
  def __init__(self):
    super().__init__()
    self.volume_path = self.__get_volume_path()
    self.docker_container_name = DOCKER_CONTAINER_NAME
    self.docker_tag = DOCKER_TAG
    self.env_file = ENV_FILE
    self.node_id = self.get_node_id()
    self.mqtt_host = DEFAULT_MQTT_HOST
    self.mqtt_user = DEFAULT_MQTT_USER
    self.mqtt_password = DEFAULT_MQTT_PASSWORD
    self.__generate_env_file()
    self.__setup_docker_run()
    return
  
  def __setup_docker_run(self):
    self.docker_image = DOCKER_IMAGE + ":" + self.docker_tag
    self.CMD = [
        'docker', 'run', '--gpus=all', 
        '--env-file', self.env_file, 
        '-v', f'{DOCKER_VOLUME}:/edge_node/_local_cache', 
        '--name', self.docker_container_name, '-d', 
        self.docker_image
    ]
    return


  def __maybe_docker_pull(self):
    progress_dialog = ProgressBarWindow("Pulling Docker Image...", self._icon)
    self.docker_pull_thread = DockerPullThread(self.docker_image)
    self.docker_pull_thread.progress_update.connect(progress_dialog.update_progress)
    self.docker_pull_thread.pull_finished.connect(progress_dialog.on_docker_pull_finished)
    self.docker_pull_thread.start()
    
    self.progress_dialog = progress_dialog
    self.progress_dialog.exec_()
    return



  
  
  def get_node_id(self):
    return 'naeural_' + str(uuid4())[:8]
  

  def __check_env_keys(self):
    # Load the current .env file
    env_vars = OrderedDict()
    try:
      with open(self.env_file, 'r') as file:
        for line in file:
          if line.strip() and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            env_vars[key] = value
    except FileNotFoundError:
      QMessageBox.warning(self, 'Error', '.env file not found.')
      return False

    # Check if the EE_MQTT key is present and set
    if 'EE_MQTT' not in env_vars or not env_vars['EE_MQTT']:
      # Prompt the user for the MQTT password
      password, ok = QInputDialog.getText(self, 'MQTT Broker password Required', 'Enter MQTT broker password:')
      if ok and password:
        # Update the env_vars dictionary with the new password
        env_vars['EE_MQTT'] = password
        # Resave the .env file with the updated key
        with open(self.env_file, 'w') as file:
          for key, value in env_vars.items():
            file.write(f'{key}={value}\n')
        QMessageBox.information(self, 'Success', 'MQTT password set successfully.')
        return True
      else:
        QMessageBox.warning(self, 'Error', 'MQTT password is required to continue.')
        return False
    return True
    
    
  def __generate_env_file(self):
    if os.path.exists(self.env_file):
      pass
    else:
      str_env = ENV_TEMPLATE.format(
        self.node_id, 
        self.mqtt_host, 
        self.mqtt_user, 
        self.mqtt_password
      )
      with open(self.env_file, 'w') as f:
        f.write(str_env)
    return


  def __get_volume_path(self):
    if platform.system() == 'Windows':
      return WINDOWS_VOLUME_PATH
    else:
      return LINUX_VOLUME_PATH

  def check_docker(self):
    try:
      subprocess.check_output(['docker', '--version'])
      return True
    except (subprocess.CalledProcessError, FileNotFoundError):
      QMessageBox.warning(
         self, 'Docker Check', 
         'Docker is not installed. Please install Docker and restart the application.\n\nFor more information, visit: https://docs.docker.com/get-docker/'
      )
      return False


  def is_container_running(self):
    try:
      status = subprocess.check_output(['docker', 'inspect', '--format', '{{.State.Running}}', self.docker_container_name])
      return status.strip() == b'true'
    except subprocess.CalledProcessError:
      return False


  def launch_container(self):
    try:
      is_env_ok = self.__check_env_keys()
      if not is_env_ok:
        return
      self.__maybe_docker_pull()
      subprocess.check_call(self.CMD)
      sleep(2)
      QMessageBox.information(self, 'Container Launch', 'Container launched successfully.')
    except subprocess.CalledProcessError:
      QMessageBox.warning(self, 'Container Launch', 'Failed to launch container.')
    return


  def stop_container(self):
    try:
      subprocess.check_call(['docker', 'stop', self.docker_container_name])
      subprocess.check_call(['docker', 'rm', self.docker_container_name])
      sleep(2)
      QMessageBox.information(self, 'Container Stop', 'Container stopped successfully.')      
    except subprocess.CalledProcessError:
      QMessageBox.warning(self, 'Container Stop', 'Failed to stop container.')
    return


  def delete_and_restart(self):
    pem_path = os.path.join(self.volume_path, E2_PEM_FILE)
    if not self.is_container_running():
      QMessageBox.warning(self, 'Restart Edge Node', 'Edge Node is not running.')
    else:
      # now we ask for confirmation
      reply = QMessageBox.question(self, 'Restart Edge Node', 'Are you sure you want to reset the local node?', QMessageBox.Yes | QMessageBox.No)
      if reply == QMessageBox.Yes:
        try:
          self.stop_container()
          os.remove(pem_path)
          self.launch_container()
          QMessageBox.information(self, 'Restart Edge Node', f'{E2_PEM_FILE} deleted and Edge Node restarted.')
        except Exception as e:
          QMessageBox.warning(self, 'Restart Edge Node', f'Failed to reset Edge Node: {e}')
    return
  
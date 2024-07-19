import os
import platform
import subprocess
from collections import OrderedDict
from time import sleep
from uuid import uuid4

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QDialog, QInputDialog, QLabel,
                             QMessageBox, QProgressBar, QTextEdit, QVBoxLayout)

from .const import *


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
      process = subprocess.Popen(['docker', 'pull', self.image_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
      
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
  


class ProgressBarWindow(QDialog):
  def __init__(self, message, icon_object, sender):
    super().__init__()
    self.sender = sender
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
    self.setStyleSheet(self.sender._current_stylesheet)
    return

  
  def on_docker_pull_finished(self, success):
    if success:
      QMessageBox.information(self, 'Docker Pull', 'Docker image pulled successfully.')      
      self.sender.add_log('Docker image pulled successfully.')
    else:
      QMessageBox.warning(self, 'Docker Pull', 'Failed to pull Docker image.')
    self.accept()  # Close the progress dialog
    return  



class _DockerUtilsMixin:
  def __init__(self):
    super().__init__()
    self.node_addr = None
    self.container_last_run_status = None
    self.volume_path = self.__get_volume_path()
    self.docker_container_name = DOCKER_CONTAINER_NAME
    self.docker_tag = DOCKER_TAG
    self.env_file = ENV_FILE
    self.node_id = self.get_node_id()
    self.mqtt_host = DEFAULT_MQTT_HOST
    self.mqtt_user = DEFAULT_MQTT_USER
    self.mqtt_password = DEFAULT_MQTT_PASSWORD
    self._dev_mode = False
    
    self.config_startup_file = os.path.join(self.volume_path, CONFIG_STARTUP_FILE)
    self.config_app_file = os.path.join(self.volume_path, CONFIG_APP_FILE)
    self.addrs_file = os.path.join(self.volume_path, ADDRS_FILE)
    
    self.__generate_env_file()
    self.__setup_docker_run()
    return
  
  def __setup_docker_run(self):
    self.docker_image = DOCKER_IMAGE + ":" + self.docker_tag
    self.CMD_CLEAN = [
        'docker', 'rm', self.docker_container_name,
    ]
    self.__CMD = [
        'docker', 'run', '--gpus=all',  # use all GPUs
        '--rm', # remove the container when it exits
        '--env-file', self.env_file,  # pass the .env file to the container
        '-v', f'{DOCKER_VOLUME}:/edge_node/_local_cache', # mount the volume
        '--name', self.docker_container_name, '-d',  
    ]
    return
  
  def get_cmd(self):
    if self._dev_mode:
      result = self.__CMD + ['-p 80:80', self.docker_image]
    else:
      result = self.__CMD + [self.docker_image]
    self.add_log('Docker command: {}'.format(result))
    return result

  def __maybe_docker_pull(self):
    progress_dialog = ProgressBarWindow("Pulling Docker Image...", self._icon, self)
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
      output = subprocess.check_output(['docker', '--version'], stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
      self.add_log("Docker status: " + output)
      return True
    except (subprocess.CalledProcessError, FileNotFoundError):
      QMessageBox.warning(
         self, 'Docker Check', 
         'Docker is not installed. Please install Docker and restart the application.\n\nFor more information, visit: https://docs.docker.com/get-docker/'
      )
      return False


  def is_container_running(self):
    try:
      status = subprocess.check_output(
        ['docker', 'inspect', '--format', '{{.State.Running}}', self.docker_container_name],
        stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW
      )
      status = status.strip()
      container_running = status.split()[-1] == 'true'
      if container_running != self.container_last_run_status:
        self.add_log('Edge Node container status changed: {} -> {} (status: {})'.format(
          self.container_last_run_status, container_running, status
        ))
        self.container_last_run_status = container_running
      return container_running
    except subprocess.CalledProcessError:
      return False


  def launch_container(self):
    try:
      is_env_ok = self.__check_env_keys()
      if not is_env_ok:
        return
      self.add_log('Updating image...')
      self.__maybe_docker_pull()
      # first try to clean the container
      self.add_log("Attempting to clean up the container...")
      run_cmd = self.get_cmd()
      subprocess.call(run_cmd, creationflags=subprocess.CREATE_NO_WINDOW)
      self.add_log('Starting Edge Node container...')
      subprocess.check_call(self.CMD, creationflags=subprocess.CREATE_NO_WINDOW)
      sleep(2)
      QMessageBox.information(self, 'Container Launch', 'Container launched successfully.')
      self.add_log('Edge Node container launched successfully.')
    except subprocess.CalledProcessError as e:
      QMessageBox.warning(self, 'Container Launch', 'Failed to launch container.')
      self.add_log('Edge Node container start failed: {}'.format(e))
    return


  def stop_container(self):
    try:
      self.add_log('Stopping Edge Node container...')
      subprocess.check_call(['docker', 'stop', self.docker_container_name], creationflags=subprocess.CREATE_NO_WINDOW)
      subprocess.check_call(['docker', 'rm', self.docker_container_name], creationflags=subprocess.CREATE_NO_WINDOW)
      sleep(2)
      QMessageBox.information(self, 'Container Stop', 'Container stopped successfully.')      
      self.add_log('Edge Node container stopped successfully.')
    except subprocess.CalledProcessError:
      QMessageBox.warning(self, 'Container Stop', 'Failed to stop container.')
      self.add_log('Edge Node container stop failed.')
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
  
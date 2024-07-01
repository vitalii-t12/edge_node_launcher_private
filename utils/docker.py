import platform
import subprocess
import os

from uuid import uuid4
from time import sleep
from PyQt5.QtWidgets import QMessageBox

from .const import *

class _DockerUtilsMixin:
  def __init__(self):
    super().__init__()
    self.volume_path = self.get_volume_path()
    self.docker_image = DOCKER_IMAGE
    self.docker_container_name = DOCKER_CONTAINER_NAME
    self.env_file = ENV_FILE
    self.node_id = self.get_node_id()
    self.mqtt_host = DEFAULT_MQTT_HOST
    self.mqtt_user = DEFAULT_MQTT_USER
    self.mqtt_password = DEFAULT_MQTT_PASSWORD
    self.generate_env_file()
    return
  
  def get_node_id(self):
    return 'naeural_' + str(uuid4())[:8]
    
  def generate_env_file(self):
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


  def is_container_running(self):
    try:
      status = subprocess.check_output(['docker', 'inspect', '--format', '{{.State.Running}}', self.docker_container_name])
      return status.strip() == b'true'
    except subprocess.CalledProcessError:
      return False


  def launch_container(self):
    try:
      subprocess.check_call([
        'docker', 'run', '--gpus=all', '--env-file', self.env_file, '-v', 
        f'{self.volume_path}:/edge_node/_local_cache', '--name', self.docker_container_name, '-d', self.docker_image
      ])
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
    try:
      os.remove(pem_path)
      self.stop_container()
      self.launch_container()
      QMessageBox.information(self, 'Restart Container', f'{E2_PEM_FILE} deleted and container restarted.')
    except FileNotFoundError:
      QMessageBox.warning(self, 'Restart Container', f'{E2_PEM_FILE} not found.')
    return
  
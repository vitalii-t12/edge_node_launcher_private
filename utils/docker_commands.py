import os
import json
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal

from models.NodeInfo import NodeInfo
from models.NodeHistory import NodeHistory


class DockerCommandThread(QThread):
    """ Thread to run a Docker command """
    command_finished = pyqtSignal(dict)
    command_error = pyqtSignal(str)

    def __init__(self, container_name: str, command: str):
        super().__init__()
        self.container_name = container_name
        self.command = command

    def run(self):
        try:
            full_command = ['docker', 'exec', self.container_name] + self.command.split()
            if os.name == 'nt':
                result = subprocess.run(
                    full_command,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(full_command, capture_output=True, text=True)

            if result.returncode != 0:
                self.command_error.emit(f"Command failed: {result.stderr}")
                return

            try:
                data = json.loads(result.stdout)
                self.command_finished.emit(data)
            except json.JSONDecodeError:
                self.command_error.emit("Error decoding JSON response")
        except Exception as e:
            self.command_error.emit(str(e))

class DockerCommandHandler:
    """ Handles Docker commands """
    def __init__(self, container_name: str):
        self.container_name = container_name
        self.threads = []

    def _execute_threaded(self, command: str, callback, error_callback) -> None:
        thread = DockerCommandThread(self.container_name, command)
        thread.command_finished.connect(callback)
        thread.command_error.connect(error_callback)
        self.threads.append(thread)  # Keep reference to prevent GC
        thread.finished.connect(lambda: self.threads.remove(thread))
        thread.start()

    def get_node_info(self, callback, error_callback) -> None:
        def process_node_info(data: dict):
            try:
                node_info = NodeInfo.from_dict(data)
                callback(node_info)
            except Exception as e:
                error_callback(f"Failed to process node info: {str(e)}")

        self._execute_threaded('get_node_info', process_node_info, error_callback)

    def get_node_history(self, callback, error_callback) -> None:
        def process_metrics(data: dict):
            try:
                metrics = NodeHistory.from_dict(data)
                callback(metrics)
            except Exception as e:
                error_callback(f"Failed to process metrics: {str(e)}")

        self._execute_threaded('get_node_history', process_metrics, error_callback)

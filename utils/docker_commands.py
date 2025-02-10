import os
import json
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal

from models.NodeInfo import NodeInfo
from models.NodeHistory import NodeHistory
from models.StartupConfig import StartupConfig
from models.ConfigApp import ConfigApp


class DockerCommandThread(QThread):
    """ Thread to run a Docker command """
    command_finished = pyqtSignal(dict)
    command_error = pyqtSignal(str)

    def __init__(self, container_name: str, command: str, input_data: str = None):
        super().__init__()
        self.container_name = container_name
        self.command = command
        self.input_data = input_data

    def run(self):
        try:
            full_command = ['docker', 'exec']
            if self.input_data is not None:
                full_command.extend(['-i'])  # Add interactive flag when input is provided
            full_command.extend([self.container_name] + self.command.split())

            if os.name == 'nt':
                result = subprocess.run(
                    full_command,
                    input=self.input_data.encode() if self.input_data else None,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    full_command,
                    input=self.input_data,
                    capture_output=True,
                    text=True
                )

            if result.returncode != 0:
                self.command_error.emit(f"Command failed: {result.stderr}\nCommand: {' '.join(full_command)}\nInput data: {self.input_data}")
                return

            # TODO: Imrove output handling.
            # Maybe implement it in a way that the command itself can specify the output format.
            # For delete_e2_pem_file command, treat output as plain text
            if self.command == 'delete_e2_pem_file':
                self.command_finished.emit({'message': result.stdout.strip()})
                return

            try:
                data = json.loads(result.stdout)
                self.command_finished.emit(data)
            except json.JSONDecodeError:
                self.command_error.emit(f"Error decoding JSON response. Raw output: {result.stdout}")
            except Exception as e:
                self.command_error.emit(f"Error processing response: {str(e)}\nRaw output: {result.stdout}")
        except Exception as e:
            self.command_error.emit(f"Error executing command: {str(e)}\nCommand: {' '.join(full_command)}\nInput data: {self.input_data}")

class DockerCommandHandler:
    """ Handles Docker commands """
    def __init__(self, container_name: str):
        self.container_name = container_name
        self.threads = []

    def _execute_threaded(self, command: str, callback, error_callback, input_data: str = None) -> None:
        thread = DockerCommandThread(self.container_name, command, input_data)
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

    def get_allowed_addresses(self, callback, error_callback) -> None:
        def process_allowed_addresses(output: str):
            try:
                # Convert plain text output to dictionary
                allowed_dict = {}
                for line in output.strip().split('\n'):
                    if line.strip():  # Skip empty lines
                        address, alias = line.strip().split(None, 1)  # Split on whitespace, max 1 split
                        allowed_dict[address] = alias
                
                callback(allowed_dict)
            except Exception as e:
                error_callback(f"Failed to process allowed addresses: {str(e)}")

        try:
            full_command = ['docker', 'exec', self.container_name, 'get_allowed']
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
                error_callback(f"Command failed: {result.stderr}")
                return

            process_allowed_addresses(result.stdout)
        except Exception as e:
            error_callback(str(e))

    def update_allowed_batch(self, addresses_data: list, callback, error_callback) -> None:
        """Update allowed addresses in batch
        
        Args:
            addresses_data: List of dicts with 'address' and 'alias' keys
            callback: Success callback
            error_callback: Error callback
        """
        # Format data as required by the command
        batch_input = '\n'.join(f"{addr['address']} {addr['alias']}" 
                              for addr in addresses_data)
        
        self._execute_threaded(
            'update_allowed_batch',
            callback,
            error_callback,
            input_data=batch_input
        )

    def get_startup_config(self, callback, error_callback) -> None:
        def process_startup_config(data: dict):
            try:
                startup_config = StartupConfig.from_dict(data)
                callback(startup_config)
            except Exception as e:
                error_callback(f"Failed to process startup config: {str(e)}")

        self._execute_threaded('get_startup_config', process_startup_config, error_callback)

    def get_config_app(self, callback, error_callback) -> None:
        def process_config_app(data: dict):
            try:
                config_app = ConfigApp.from_dict(data)
                callback(config_app)
            except Exception as e:
                error_callback(f"Failed to process config app: {str(e)}")

        self._execute_threaded('get_config_app', process_config_app, error_callback)

    def delete_e2_pem_file(self, callback, error_callback) -> None:
        """Deletes the E2 PEM file using a Docker command
        
        Args:
            callback: Success callback
            error_callback: Error callback
        """
        def process_response(data: dict):
            try:
                # Extract the message from stdout
                message = data.get('stdout', '').strip()
                callback(message)
            except Exception as e:
                error_callback(f"Failed to process response: {str(e)}")

        self._execute_threaded('delete_e2_pem_file', process_response, error_callback)

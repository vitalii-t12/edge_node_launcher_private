import subprocess
import os
import json
from typing import Optional, List, Dict, Any, Tuple, Union
import platform
from utils.subprocess_utils import run_process_no_window

class _DockerUtilsMixin:
    """Docker utilities mixin class."""
    
    def _run_docker_command(self, command: List[str], capture_output: bool = True, check: bool = False) -> subprocess.CompletedProcess:
        """Run a docker command without showing terminal window."""
        # Prepend 'docker' to command if not already there
        if command[0] != 'docker':
            command = ['docker'] + command
        
        self.add_log(f"Running Docker command: {' '.join(command)}", debug=True)
        
        try:
            # Use our utility function to hide the console window
            result = run_process_no_window(
                command,
                capture_output=capture_output,
                check=check
            )
            
            if result.returncode != 0 and hasattr(result, 'stderr') and result.stderr:
                self.add_log(f"Docker command error: {result.stderr}", debug=True)
                
            return result
        except Exception as e:
            self.add_log(f"Docker command exception: {str(e)}", debug=True)
            # Return a fake CompletedProcess with error info
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr=str(e)
            )

    # Update your other Docker methods to use _run_docker_command
    def _check_docker_running(self) -> bool:
        """Check if Docker is running."""
        result = self._run_docker_command(['info'], capture_output=True)
        return result.returncode == 0

    def _get_local_containers(self) -> List[Dict[str, Any]]:
        """Get list of local containers."""
        result = self._run_docker_command(['ps', '-a', '--format', '{{json .}}'], capture_output=True)
        if result.returncode != 0:
            return []
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    self.add_log(f"Error parsing docker container info: {line}", debug=True)
        
        return containers

    # Implement other Docker utility methods using _run_docker_command
    # Replace any direct subprocess.run or subprocess.Popen calls 
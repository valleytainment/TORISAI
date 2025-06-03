"""
TORIS AI - Secure Code Execution
Implements Docker-based sandboxing for code execution
"""
from typing import Dict, Any, Optional
import subprocess
import os
import tempfile
import logging
import time
import uuid
import shutil

logger = logging.getLogger("torisai.tools.secure_code")

# Configuration
DEFAULT_TIMEOUT = 5  # seconds
DEFAULT_MEMORY_LIMIT = "256m"
DEFAULT_NETWORK = "none"
MAX_OUTPUT_SIZE = 4096  # characters

class SecureCodeExecutor:
    """
    Executes code securely in a Docker container with resource limits
    """
    
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        memory_limit: str = DEFAULT_MEMORY_LIMIT,
        network: str = DEFAULT_NETWORK,
        logs_dir: str = "./logs"
    ):
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.network = network
        self.logs_dir = logs_dir
        
        # Ensure logs directory exists
        os.makedirs(logs_dir, exist_ok=True)
    
    def execute_python(self, code: str) -> str:
        """Execute Python code in a sandboxed environment"""
        return self._execute_in_container(code, "python:3.11-alpine", "python", "py")
    
    def execute_javascript(self, code: str) -> str:
        """Execute JavaScript code in a sandboxed environment"""
        return self._execute_in_container(code, "node:18-alpine", "node", "js")
    
    def execute_shell(self, code: str) -> str:
        """Execute shell code in a sandboxed environment"""
        return self._execute_in_container(code, "alpine:latest", "sh", "sh")
    
    def _execute_in_container(self, code: str, image: str, interpreter: str, extension: str) -> str:
        """
        Execute code in a Docker container with resource limits
        
        Args:
            code: The code to execute
            image: Docker image to use
            interpreter: Command to run the code (python, node, sh)
            extension: File extension for the code
            
        Returns:
            Output from code execution
        """
        # Create a unique ID for this execution
        exec_id = str(uuid.uuid4())[:8]
        
        # Create a temporary file for the code
        temp_dir = tempfile.mkdtemp(prefix=f"torisai_exec_{exec_id}_")
        temp_file = os.path.join(temp_dir, f"code.{extension}")
        
        try:
            # Write code to temporary file
            with open(temp_file, "w") as f:
                f.write(code)
            
            # Make file executable if it's a shell script
            if extension == "sh":
                os.chmod(temp_file, 0o755)
            
            # Prepare Docker command
            docker_cmd = [
                "docker", "run",
                "--rm",  # Remove container after execution
                f"--memory={self.memory_limit}",  # Memory limit
                f"--network={self.network}",  # Network access
                "--cpus=0.5",  # CPU limit
                "--pids-limit=50",  # Process limit
                "-v", f"{temp_dir}:/code",  # Mount code directory
                "--workdir", "/code",  # Set working directory
                image,  # Docker image
                interpreter,  # Interpreter command
                f"code.{extension}"  # Code file
            ]
            
            # Log the execution
            logger.info(f"Executing code in container: {exec_id}")
            
            # Execute the command with timeout
            start_time = time.time()
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            execution_time = time.time() - start_time
            
            # Prepare output
            stdout = result.stdout
            stderr = result.stderr
            
            # Truncate output if too large
            if len(stdout) > MAX_OUTPUT_SIZE:
                stdout = stdout[:MAX_OUTPUT_SIZE] + "\n... (output truncated)"
            
            # Combine output
            output = stdout
            if stderr:
                output += f"\nErrors:\n{stderr}"
            
            # Log execution details
            logger.info(f"Code execution {exec_id} completed in {execution_time:.2f}s with return code {result.returncode}")
            
            return output
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Code execution {exec_id} timed out after {self.timeout}s")
            return f"Error: Code execution timed out after {self.timeout} seconds"
            
        except Exception as e:
            logger.error(f"Error in code execution {exec_id}: {str(e)}")
            return f"Error executing code: {str(e)}"
            
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Error cleaning up temporary directory: {str(e)}")

def execute_code(code: str, language: str = "python") -> str:
    """
    Execute code securely in a sandboxed environment
    
    Args:
        code: The code to execute
        language: The programming language (python, javascript, shell)
        
    Returns:
        Output from code execution
    """
    executor = SecureCodeExecutor()
    
    if language.lower() == "python":
        return executor.execute_python(code)
    elif language.lower() in ["javascript", "js"]:
        return executor.execute_javascript(code)
    elif language.lower() in ["shell", "bash", "sh"]:
        return executor.execute_shell(code)
    else:
        return f"Unsupported language: {language}"

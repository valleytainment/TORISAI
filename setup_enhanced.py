#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil
import time
import json
import requests

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}")

def print_step(text):
    print(f"{Colors.BLUE}➤ {text}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def check_python_version():
    print_step("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ is required. Found Python {version.major}.{version.minor}")
        print_warning("Please install Python 3.8 or higher and try again.")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_pip():
    print_step("Checking pip installation...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, stdout=subprocess.PIPE)
        print_success("pip is installed")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print_error("pip is not installed or not in PATH")
        print_warning("Please install pip and try again.")
        return False

def install_python_dependencies():
    print_step("Installing Python dependencies...")
    requirements = [
        "gradio>=5.0.0",
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "pillow>=9.0.0",
        "numpy>=1.20.0",
        "pandas>=1.0.0",
        "langchain>=0.1.0",
        "chromadb>=0.4.18",
        "sentence-transformers>=2.2.2",
        "open-interpreter>=0.2.0",
        "pydantic>=2.0.0"
    ]
    
    try:
        for req in requirements:
            print(f"Installing {req}...")
            subprocess.run([sys.executable, "-m", "pip", "install", req], check=True)
        print_success("All Python dependencies installed successfully")
        return True
    except subprocess.SubprocessError as e:
        print_error(f"Failed to install Python dependencies: {e}")
        return False

def check_ollama():
    print_step("Checking Ollama installation...")
    try:
        # Try to run ollama version
        result = subprocess.run(["ollama", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Ollama is installed: {version}")
            return True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    print_warning("Ollama is not installed or not in PATH")
    
    # Provide installation instructions based on platform
    system = platform.system().lower()
    if system == "linux":
        print_warning("To install Ollama on Linux, run:")
        print("curl -fsSL https://ollama.com/install.sh | sh")
    elif system == "darwin":  # macOS
        print_warning("To install Ollama on macOS, run:")
        print("curl -fsSL https://ollama.com/install.sh | sh")
        print("Or install via Homebrew: brew install ollama")
    elif system == "windows":
        print_warning("To install Ollama on Windows:")
        print("1. Download the installer from https://ollama.com/download/windows")
        print("2. Run the installer and follow the instructions")
    
    choice = input("Would you like to continue setup without Ollama? (y/n): ")
    return choice.lower() == 'y'

def check_docker():
    print_step("Checking Docker installation...")
    try:
        # Try to run docker version
        result = subprocess.run(["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Docker is installed: {version}")
            
            # Check docker-compose
            compose_result = subprocess.run(["docker-compose", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if compose_result.returncode == 0:
                compose_version = compose_result.stdout.strip()
                print_success(f"Docker Compose is installed: {compose_version}")
                return True
            else:
                print_warning("Docker is installed but Docker Compose is missing")
        else:
            print_warning("Docker is not installed or not in PATH")
    except (subprocess.SubprocessError, FileNotFoundError):
        print_warning("Docker is not installed or not in PATH")
    
    # Provide installation instructions based on platform
    system = platform.system().lower()
    if system == "linux":
        print_warning("To install Docker on Linux, visit:")
        print("https://docs.docker.com/engine/install/")
    elif system == "darwin":  # macOS
        print_warning("To install Docker on macOS, visit:")
        print("https://docs.docker.com/desktop/install/mac-install/")
    elif system == "windows":
        print_warning("To install Docker on Windows, visit:")
        print("https://docs.docker.com/desktop/install/windows-install/")
    
    choice = input("Would you like to continue setup without Docker? (y/n): ")
    return choice.lower() == 'y'

def check_models():
    print_step("Checking for required models...")
    try:
        # Check if Ollama is running
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                print_warning("Ollama is not running. Starting Ollama...")
                if platform.system().lower() == "windows":
                    subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait for Ollama to start
                for _ in range(30):  # Wait up to 30 seconds
                    try:
                        response = requests.get("http://localhost:11434/api/tags")
                        if response.status_code == 200:
                            print_success("Ollama started successfully")
                            break
                    except:
                        pass
                    time.sleep(1)
                else:
                    print_warning("Failed to start Ollama automatically")
        except:
            print_warning("Could not connect to Ollama")
        
        # Check for required models
        models_to_check = ["llama3:8b", "qwen:7b"]
        models_to_pull = []
        
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                available_models = [model["name"] for model in response.json().get("models", [])]
                
                for model in models_to_check:
                    if model not in available_models:
                        models_to_pull.append(model)
                
                if models_to_pull:
                    print_warning(f"The following models need to be pulled: {', '.join(models_to_pull)}")
                    choice = input("Would you like to pull these models now? (y/n): ")
                    
                    if choice.lower() == 'y':
                        for model in models_to_pull:
                            print(f"Pulling {model}... (this may take a while)")
                            subprocess.run(["ollama", "pull", model], check=True)
                        print_success("All required models pulled successfully")
                    else:
                        print_warning("Models will need to be pulled when running TORIS AI")
                else:
                    print_success("All required models are already available")
            else:
                print_warning("Could not check models. Ollama may not be running.")
        except:
            print_warning("Could not check models. Ollama may not be running.")
        
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print_warning("Could not check models. Ollama may not be installed or running.")
        print_warning("Models will need to be pulled when running TORIS AI")
        return True

def setup_superagi():
    print_step("Setting up SuperAGI...")
    
    # Check if git is installed
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE)
    except (subprocess.SubprocessError, FileNotFoundError):
        print_warning("Git is not installed or not in PATH")
        print_warning("SuperAGI setup requires Git. Please install Git and try again.")
        return False
    
    # Clone SuperAGI repository if it doesn't exist
    if not os.path.exists("SuperAGI"):
        try:
            print_step("Cloning SuperAGI repository...")
            subprocess.run(["git", "clone", "https://github.com/TransformerOptimus/SuperAGI.git"], check=True)
            print_success("SuperAGI repository cloned successfully")
        except subprocess.SubprocessError as e:
            print_error(f"Failed to clone SuperAGI repository: {e}")
            return False
    else:
        print_step("SuperAGI repository already exists, updating...")
        try:
            subprocess.run(["git", "-C", "SuperAGI", "pull"], check=True)
            print_success("SuperAGI repository updated successfully")
        except subprocess.SubprocessError as e:
            print_warning(f"Failed to update SuperAGI repository: {e}")
    
    # Create .env file with Ollama configuration
    env_file_path = os.path.join("SuperAGI", ".env")
    if not os.path.exists(env_file_path):
        print_step("Creating SuperAGI .env file...")
        with open(env_file_path, "w") as f:
            f.write("# SuperAGI .env file\n")
            f.write("LLM_PROVIDER=ollama\n")
            f.write("LLM_BASE_URL=http://host.docker.internal:11434\n")
            f.write("OPENAI_API_KEY=not-needed\n")
            f.write("ANTHROPIC_API_KEY=not-needed\n")
            f.write("GOOGLE_API_KEY=not-needed\n")
            f.write("WORKSPACE_DIR=workspace\n")
            f.write("RESOURCES_DIR=resources\n")
        print_success("SuperAGI .env file created successfully")
    else:
        print_step("Updating SuperAGI .env file...")
        with open(env_file_path, "r") as f:
            env_content = f.read()
        
        # Update or add Ollama configuration
        if "LLM_PROVIDER=ollama" not in env_content:
            with open(env_file_path, "a") as f:
                f.write("\n# Added by TORIS AI setup\n")
                f.write("LLM_PROVIDER=ollama\n")
                f.write("LLM_BASE_URL=http://host.docker.internal:11434\n")
            print_success("SuperAGI .env file updated successfully")
        else:
            print_success("SuperAGI .env file already configured for Ollama")
    
    print_success("SuperAGI setup completed")
    return True

def create_directories():
    print_step("Creating required directories...")
    directories = ["./memory", "./documents", "./chroma_db", "./screenshots", "./logs"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print_success("All required directories created")
    return True

def setup_environment():
    print_header("TORIS AI Enhanced Setup")
    print("This script will set up the environment for the enhanced TORIS AI.")
    
    # Check system requirements
    if not check_python_version():
        return False
    
    if not check_pip():
        return False
    
    # Install Python dependencies
    if not install_python_dependencies():
        return False
    
    # Check Ollama installation
    check_ollama()
    
    # Check Docker installation
    check_docker()
    
    # Check models (if Ollama is installed)
    try:
        check_models()
    except:
        print_warning("Skipping model check. Models will need to be pulled when running TORIS AI.")
    
    # Setup SuperAGI
    setup_superagi()
    
    # Create required directories
    create_directories()
    
    print_header("Setup Complete")
    print_success("Enhanced TORIS AI environment has been set up successfully!")
    print("\nTo run TORIS AI, use the following command:")
    print(f"{Colors.BOLD}python run_toris_enhanced.py{Colors.ENDC}")
    print("\nNote: If you skipped installing Ollama or Docker, you will need to install them before running TORIS AI.")
    
    return True

if __name__ == "__main__":
    setup_environment()

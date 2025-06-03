#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import time
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./logs/toris_runner.log") if os.path.exists("./logs") else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TORIS_RUNNER")

def print_header(text):
    print(f"\n=== {text} ===")

def print_step(text):
    print(f"➤ {text}")

def check_ollama_running():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Start Ollama if not running"""
    if not check_ollama_running():
        print_step("Starting Ollama...")
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for Ollama to start
            for _ in range(30):  # Wait up to 30 seconds
                if check_ollama_running():
                    print("Ollama started successfully")
                    return True
                time.sleep(1)
            
            print("Failed to start Ollama automatically.")
            print("Please start Ollama manually and try again.")
            return False
        except FileNotFoundError:
            print("Ollama not found. Please install Ollama first.")
            print("Visit https://ollama.com/download for installation instructions.")
            return False
    else:
        print("Ollama is already running")
        return True

def check_superagi():
    """Check if SuperAGI is available"""
    if os.path.exists("SuperAGI"):
        print("SuperAGI is available")
        return True
    else:
        print("SuperAGI is not available. Some features may be limited.")
        return False

def ensure_directories():
    """Ensure required directories exist"""
    directories = ["./memory", "./documents", "./chroma_db", "./screenshots", "./logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    return True

def run_toris():
    """Run TORIS AI"""
    print_header("Starting Enhanced TORIS AI")
    
    # Ensure directories exist
    ensure_directories()
    
    # Check if Ollama is installed and running
    try:
        subprocess.run(["ollama", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Ollama is not installed or not in PATH.")
        print("Please install Ollama first: https://ollama.com/download")
        return False
    
    # Start Ollama if not running
    if not start_ollama():
        return False
    
    # Check SuperAGI
    check_superagi()
    
    # Run the TORIS AI application
    try:
        print_step("Launching TORIS AI with enhanced GUI...")
        subprocess.run([sys.executable, "app_enhanced_gui.py"], check=True)
        return True
    except subprocess.SubprocessError as e:
        print(f"Error running TORIS AI: {e}")
        return False

if __name__ == "__main__":
    run_toris()

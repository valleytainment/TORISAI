import subprocess
import sys
import os
import time
import webbrowser
import threading
import platform

def check_ollama_running():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Start Ollama if not running"""
    if not check_ollama_running():
        print("Starting Ollama...")
        if platform.system() == "Windows":
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for Ollama to start
        for _ in range(30):  # Wait up to 30 seconds
            if check_ollama_running():
                print("Ollama started successfully")
                break
            time.sleep(1)
        else:
            print("Failed to start Ollama. Please start it manually.")
            return False
    else:
        print("Ollama is already running")
    return True

def ensure_models_pulled():
    """Ensure required models are pulled"""
    # For 12GB RAM system, use smaller models
    models = ["llama3:8b", "qwen:7b"]
    
    for model in models:
        print(f"Checking if {model} is available...")
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if model not in result.stdout:
            print(f"Pulling {model}...")
            subprocess.run(["ollama", "pull", model], check=True)
        else:
            print(f"{model} is already available")

def create_directories():
    """Create necessary directories"""
    directories = ["./memory", "./documents", "./chroma_db"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def start_ui():
    """Start the Gradio UI"""
    print("Starting TORIS AI interface...")
    subprocess.run([sys.executable, "app.py"])

def main():
    print("Initializing TORIS AI - Your Local AI Agent")
    
    # Check dependencies
    try:
        import gradio, requests, bs4
        print("All required Python packages are installed")
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please run: python setup.py")
        return
    
    # Start Ollama
    if not start_ollama():
        return
    
    # Ensure models are pulled
    ensure_models_pulled()
    
    # Create necessary directories
    create_directories()
    
    # Start the UI
    start_ui()

if __name__ == "__main__":
    main()

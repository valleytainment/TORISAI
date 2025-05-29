import subprocess
import sys
import os
import platform

def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"Python version {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")

def install_dependencies():
    """Install required Python packages"""
    packages = [
        "gradio",
        "requests",
        "beautifulsoup4",
        "sentence-transformers"
    ]
    
    print("Installing required Python packages...")
    subprocess.run([sys.executable, "-m", "pip", "install"] + packages, check=True)

def check_ollama():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(["ollama", "version"], capture_output=True, text=True)
        print(f"Ollama {result.stdout.strip()} detected")
        return True
    except:
        print("Ollama not found")
        return False

def install_ollama():
    """Provide instructions for installing Ollama"""
    print("\nOllama installation instructions:")
    
    if platform.system() == "Windows":
        print("Windows:")
        print("1. Download the installer from https://ollama.ai/download/OllamaSetup.exe")
        print("2. Run the installer and follow the instructions")
    
    elif platform.system() == "Darwin":  # macOS
        print("macOS:")
        print("Option 1: Install using Homebrew")
        print("  brew install ollama")
        print("Option 2: Install using curl")
        print("  curl -fsSL https://ollama.ai/download/ollama-darwin.tar.gz | tar -xzf - -C /usr/local/bin")
    
    else:  # Linux
        print("Linux:")
        print("  curl -fsSL https://ollama.ai/install.sh | sh")
    
    print("\nAfter installing Ollama, run this setup script again.")

def create_directories():
    """Create necessary directories"""
    directories = ["./memory", "./documents", "./chroma_db"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("Created necessary directories")

def main():
    print("TORIS AI Setup")
    print("==============")
    
    # Check Python version
    check_python_version()
    
    # Install Python dependencies
    install_dependencies()
    
    # Check for Ollama
    if not check_ollama():
        install_ollama()
        return
    
    # Create directories
    create_directories()
    
    print("\nSetup completed successfully!")
    print("To start TORIS AI, run: python app.py")

if __name__ == "__main__":
    main()

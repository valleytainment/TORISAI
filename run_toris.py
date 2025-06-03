"""
TORIS AI - Run Script
Launches the TORIS AI application with all features
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./logs/toris.log") if os.path.exists("./logs") else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("torisai.run")

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configuration
CONFIG = {
    "default_model": os.environ.get("TORIS_MODEL", "llama3:8b"),
    "ollama_host": os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
}

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        "gradio",
        "httpx",
        "pydantic",
        "PyPDF2",
        "chromadb"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning(f"Missing dependencies: {', '.join(missing_packages)}")
        logger.info("Installing missing dependencies...")
        
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            logger.info("Dependencies installed successfully")
        except Exception as e:
            logger.error(f"Error installing dependencies: {str(e)}")
            logger.error("Please install the missing dependencies manually:")
            logger.error(f"pip install {' '.join(missing_packages)}")
            return False
    
    return True

# --- Simplified sanity check (CLI only) -------------------------------
import shutil, sys
if shutil.which("ollama") is None:
    print("Ollama executable not found on PATH – aborting.")
    sys.exit(1)

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "documents", "memory"]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir()
            logger.info(f"Created directory: {directory}")

def main():
    """Main entry point"""
    logger.info("Starting TORIS AI")
    
    # Create necessary directories
    create_directories()
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Missing dependencies. Please install them and try again.")
        return 1
    
    try:
        # Import and run TORIS AI
        from torisai.main import TorisAI
        
        toris = TorisAI()
        toris.run()
        
        return 0
    
    except Exception as e:
        logger.error(f"Error running TORIS AI: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

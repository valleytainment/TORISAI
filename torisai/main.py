"""
TORIS AI - Main Entry Point
Implements the main application runner
"""
import os
import sys
import logging
import asyncio
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import TORIS AI modules
from torisai.api.main import app as api_app
import uvicorn

logger = logging.getLogger("torisai.main")

async def check_dependencies():
    """Check if all dependencies are installed and available"""
    try:
        # Check Ollama
        from torisai.core.ollama_client import get_client
        client = await get_client()
        ollama_status = await client.check_status()
        
        if not ollama_status:
            logger.warning("Ollama is not running. Some features may not work properly.")
            print("WARNING: Ollama is not running. Please start Ollama for full functionality.")
        else:
            logger.info("Ollama is running")
            
            # Check available models
            models = await client.list_models()
            if models:
                logger.info(f"Available models: {', '.join(models)}")
            else:
                logger.warning("No models found in Ollama")
                print("WARNING: No models found in Ollama. Please pull models for full functionality.")
                print("Recommended: Run 'ollama pull llama3:8b' or 'ollama pull qwen:7b'")
        
        # Check ChromaDB
        try:
            import chromadb
            logger.info("ChromaDB is available")
        except ImportError:
            logger.warning("ChromaDB is not installed. Memory features may not work properly.")
            print("WARNING: ChromaDB is not installed. Memory features may not work properly.")
        
        # Check Docker for secure code execution
        try:
            import docker
            client = docker.from_env()
            client.ping()
            logger.info("Docker is available for secure code execution")
        except Exception as e:
            logger.warning(f"Docker is not available: {str(e)}. Code execution will be limited.")
            print("WARNING: Docker is not available. Code execution will be limited.")
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking dependencies: {str(e)}")
        return False

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        "./memory",
        "./chroma_db",
        "./logs",
        "./documents",
        "./screenshots"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="TORIS AI - Local AI Agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to run the API server on")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the API server on")
    parser.add_argument("--ui-port", type=int, default=7860, help="Port to run the UI server on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    return parser.parse_args()

async def main():
    """Main entry point for TORIS AI"""
    print("Starting TORIS AI...")
    
    # Parse arguments
    args = parse_arguments()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("./logs/torisai.log"),
            logging.StreamHandler()
        ]
    )
    
    # Ensure directories exist
    ensure_directories()
    
    # Check dependencies
    deps_ok = await check_dependencies()
    if not deps_ok:
        print("WARNING: Some dependencies are missing. TORIS AI may not function properly.")
    
    # Start the API server
    print(f"Starting API server on http://{args.host}:{args.port}")
    
    # Run the API server
    uvicorn.run(
        api_app,
        host=args.host,
        port=args.port,
        log_level="debug" if args.debug else "info"
    )

if __name__ == "__main__":
    asyncio.run(main())

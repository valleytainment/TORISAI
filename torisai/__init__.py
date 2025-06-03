"""
TORIS AI - Package Initialization
Sets up the TORIS AI package structure
"""
from torisai.core.tool_protocol import registry
from torisai.agents.specialized import get_agent

__version__ = "2.0.0"

# Import tools to register them
import torisai.tools.secure_code
import torisai.tools.web
import torisai.tools.filesystem

# Initialize logging
import logging
import os

# Create logs directory if it doesn't exist
os.makedirs("./logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./logs/torisai.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("torisai")
logger.info(f"TORIS AI v{__version__} initialized")

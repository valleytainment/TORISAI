"""
TORIS AI - File System Tools
Implements secure file operations
"""
from typing import Dict, Any, List, Optional
import logging
import os
import json
import shutil
from pydantic import BaseModel, Field

from torisai.core.tool_protocol import registry, ToolDefinition

logger = logging.getLogger("torisai.tools.filesystem")

class FileInfo(BaseModel):
    """Model for file information"""
    name: str
    path: str
    size: int
    is_dir: bool
    modified: str

def list_files(directory: str = "./") -> List[FileInfo]:
    """
    List files in a directory
    
    Args:
        directory: Directory to list files from
        
    Returns:
        List of file information
    """
    try:
        logger.info(f"Listing files in: {directory}")
        
        # Ensure the directory is within the allowed workspace
        directory = os.path.abspath(directory)
        workspace_dir = os.path.abspath("./")
        
        if not directory.startswith(workspace_dir):
            logger.warning(f"Attempted to access directory outside workspace: {directory}")
            return []
        
        # List files
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            try:
                stat = os.stat(item_path)
                files.append(
                    FileInfo(
                        name=item,
                        path=item_path,
                        size=stat.st_size,
                        is_dir=os.path.isdir(item_path),
                        modified=stat.st_mtime
                    )
                )
            except Exception as e:
                logger.error(f"Error getting info for {item_path}: {str(e)}")
        
        return files
    
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return []

def read_file(file_path: str, max_size: int = 1024 * 1024) -> str:
    """
    Read a file
    
    Args:
        file_path: Path to the file
        max_size: Maximum file size to read
        
    Returns:
        File content
    """
    try:
        logger.info(f"Reading file: {file_path}")
        
        # Ensure the file is within the allowed workspace
        file_path = os.path.abspath(file_path)
        workspace_dir = os.path.abspath("./")
        
        if not file_path.startswith(workspace_dir):
            logger.warning(f"Attempted to access file outside workspace: {file_path}")
            return "Error: Cannot access files outside the workspace"
        
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"
        
        # Check if file is too large
        if os.path.getsize(file_path) > max_size:
            return f"Error: File is too large (max {max_size} bytes)"
        
        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return content
    
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return f"Error: {str(e)}"

def write_file(file_path: str, content: str, append: bool = False) -> str:
    """
    Write to a file
    
    Args:
        file_path: Path to the file
        content: Content to write
        append: Whether to append to the file
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Writing to file: {file_path}")
        
        # Ensure the file is within the allowed workspace
        file_path = os.path.abspath(file_path)
        workspace_dir = os.path.abspath("./")
        
        if not file_path.startswith(workspace_dir):
            logger.warning(f"Attempted to write to file outside workspace: {file_path}")
            return "Error: Cannot write to files outside the workspace"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write to file
        mode = "a" if append else "w"
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)
        
        return f"Successfully {'appended to' if append else 'wrote to'} {file_path}"
    
    except Exception as e:
        logger.error(f"Error writing to file: {str(e)}")
        return f"Error: {str(e)}"

def delete_file(file_path: str) -> str:
    """
    Delete a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Deleting file: {file_path}")
        
        # Ensure the file is within the allowed workspace
        file_path = os.path.abspath(file_path)
        workspace_dir = os.path.abspath("./")
        
        if not file_path.startswith(workspace_dir):
            logger.warning(f"Attempted to delete file outside workspace: {file_path}")
            return "Error: Cannot delete files outside the workspace"
        
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"
        
        # Delete file
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
        
        return f"Successfully deleted {file_path}"
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return f"Error: {str(e)}"

# Register tools with the registry
registry.register(
    ToolDefinition(
        name="list_files",
        description="List files in a directory",
        parameters={
            "directory": {
                "type": "string",
                "description": "Directory to list files from",
                "default": "./"
            }
        },
        function=list_files,
        requires_confirmation=False
    )
)

registry.register(
    ToolDefinition(
        name="read_file",
        description="Read a file",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Path to the file"
            },
            "max_size": {
                "type": "integer",
                "description": "Maximum file size to read",
                "default": 1048576  # 1MB
            }
        },
        function=read_file,
        requires_confirmation=False
    )
)

registry.register(
    ToolDefinition(
        name="write_file",
        description="Write to a file",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Path to the file"
            },
            "content": {
                "type": "string",
                "description": "Content to write"
            },
            "append": {
                "type": "boolean",
                "description": "Whether to append to the file",
                "default": False
            }
        },
        function=write_file,
        requires_confirmation=True
    )
)

registry.register(
    ToolDefinition(
        name="delete_file",
        description="Delete a file",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Path to the file"
            }
        },
        function=delete_file,
        requires_confirmation=True
    )
)

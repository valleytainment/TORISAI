"""
TORIS AI - Core Tool Protocol
Implements structured tool calls with Pydantic validation
"""
from typing import Dict, Any, List, Optional, Union, Callable
from pydantic import BaseModel, Field, validator
import json
import re
import logging

logger = logging.getLogger("torisai.tools")

class ToolCall(BaseModel):
    """Base model for structured tool calls"""
    name: str = Field(..., description="Name of the tool to call")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")

class ToolDefinition(BaseModel):
    """Definition of a tool that can be called by the agent"""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters the tool accepts")
    function: Callable = Field(..., description="Function to call when the tool is invoked")
    requires_confirmation: bool = Field(default=False, description="Whether this tool requires explicit user confirmation")

class ToolRegistry:
    """Registry for all available tools"""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(self, tool_def: ToolDefinition) -> None:
        """Register a tool in the registry"""
        if tool_def.name in self._tools:
            logger.warning(f"Tool {tool_def.name} already registered, overwriting")
        self._tools[tool_def.name] = tool_def
        logger.info(f"Registered tool: {tool_def.name}")
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools in a format suitable for LLM context"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self._tools.values()
        ]
    
    def execute(self, call: ToolCall) -> Any:
        """Execute a tool call"""
        tool = self.get(call.name)
        if not tool:
            raise ValueError(f"Unknown tool: {call.name}")
        
        logger.info(f"Executing tool: {call.name} with args: {call.args}")
        try:
            result = tool.function(**call.args)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {call.name}: {str(e)}")
            raise

def extract_tool_calls(text: str) -> List[ToolCall]:
    """
    Extract tool calls from LLM output text
    Uses regex to find JSON-like structures that might be tool calls
    """
    # Pattern to match potential JSON objects
    pattern = r'\{(?:[^{}]|(?R))*\}'
    
    potential_jsons = re.findall(pattern, text)
    tool_calls = []
    
    for json_str in potential_jsons:
        try:
            # Try to parse as JSON
            data = json.loads(json_str)
            
            # Check if it looks like a tool call
            if isinstance(data, dict) and "name" in data:
                # Try to parse as ToolCall
                tool_call = ToolCall(
                    name=data.get("name"),
                    args=data.get("args", {})
                )
                tool_calls.append(tool_call)
        except (json.JSONDecodeError, ValueError):
            # Not valid JSON or not a valid tool call, skip
            continue
    
    return tool_calls

# Create a global registry instance
registry = ToolRegistry()

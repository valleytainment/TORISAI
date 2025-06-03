"""
TORIS AI - Agent Base Class
Implements the foundation for all specialized agents
"""
from typing import Dict, Any, List, Optional, Union
import logging
import asyncio
from pydantic import BaseModel, Field

from torisai.core.tool_protocol import ToolCall, extract_tool_calls, registry
from torisai.memory.manager import get_memory_manager
from torisai.core.ollama_client import get_client

logger = logging.getLogger("torisai.agents")

class AgentConfig(BaseModel):
    """Configuration for agent behavior"""
    name: str = "BaseAgent"
    description: str = "Base agent for TORIS AI"
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000
    default_model: str = "llama3:8b"
    lightweight_model: str = "qwen:7b"

class Agent:
    """
    Base agent class for TORIS AI
    
    Provides common functionality for all specialized agents
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the agent
        
        Args:
            config: Agent configuration
        """
        self.config = config or AgentConfig()
        self.memory_manager = get_memory_manager()
        logger.info(f"Initialized {self.config.name}")
    
    async def process_query(
        self, 
        query: str, 
        model: Optional[str] = None,
        stream: bool = False
    ) -> Union[str, asyncio.StreamReader]:
        """
        Process a user query
        
        Args:
            query: User query
            model: Model to use, defaults to config.default_model
            stream: Whether to stream the response
            
        Returns:
            Response text or stream
        """
        try:
            # Get Ollama client
            ollama_client = await get_client()
            
            # Get recent conversation history
            history = self.memory_manager.get_conversation_history(limit=5)
            context = self._prepare_context(history)
            
            # Prepare full prompt
            full_prompt = f"{context}\n\nUser: {query}"
            
            # Use specified model or default
            model_name = model or self.config.default_model
            
            logger.info(f"{self.config.name} processing query with model {model_name}")
            
            if stream:
                # Return a stream of responses
                return ollama_client.stream_generate(
                    prompt=full_prompt,
                    model=model_name,
                    system_prompt=self.config.system_prompt,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
            else:
                # Generate response
                response = await ollama_client.generate(
                    prompt=full_prompt,
                    model=model_name,
                    system_prompt=self.config.system_prompt,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                
                # Save to memory
                self.memory_manager.save_interaction(query, response)
                
                # Process tool calls if any
                tool_calls = extract_tool_calls(response)
                if tool_calls:
                    # Execute tool calls and append results
                    tool_results = []
                    for call in tool_calls:
                        try:
                            tool = registry.get(call.name)
                            if tool:
                                result = registry.execute(call)
                                tool_results.append(f"Tool {call.name} result: {result}")
                        except Exception as e:
                            error_msg = f"Error executing tool {call.name}: {str(e)}"
                            logger.error(error_msg)
                            tool_results.append(error_msg)
                    
                    if tool_results:
                        response += "\n\n" + "\n".join(tool_results)
                
                return response
        
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def _prepare_context(self, history: List[Dict[str, Any]]) -> str:
        """
        Prepare context from conversation history
        
        Args:
            history: Conversation history
            
        Returns:
            Context string
        """
        if not history:
            return ""
        
        context = "Previous conversation:\n"
        for entry in history:
            context += f"User: {entry['user']}\nAssistant: {entry['ai']}\n\n"
        
        return context

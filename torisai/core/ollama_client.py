"""
TORIS AI - Async Ollama Client
Implements asynchronous communication with Ollama API
"""
from typing import Dict, Any, Optional, List
import httpx
import logging
import json
import asyncio
from pydantic import BaseModel

logger = logging.getLogger("torisai.core.ollama")

class OllamaConfig(BaseModel):
    """Configuration for Ollama client"""
    base_url: str = "http://localhost:11434"
    timeout: int = 30
    default_model: str = "llama3:8b"
    lightweight_model: str = "qwen:7b"

class OllamaClient:
    """
    Asynchronous client for Ollama API
    
    Handles communication with the Ollama API for model management
    and text generation without blocking the main thread.
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Initialize the Ollama client
        
        Args:
            config: Configuration for the client, uses default if not provided
        """
        self.config = config or OllamaConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )
        logger.info(f"Initialized Ollama client with base URL: {self.config.base_url}")
    
    async def check_status(self) -> bool:
        """
        Check if Ollama is running
        
        Returns:
            True if Ollama is running, False otherwise
        """
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking Ollama status: {str(e)}")
            return False
    
    async def list_models(self) -> List[str]:
        """
        List available models
        
        Returns:
            List of available model names
        """
        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                return [model.get("name") for model in response.json().get("models", [])]
            logger.warning(f"Failed to list models: {response.status_code} - {response.text}")
            return []
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        Generate text using Ollama
        
        Args:
            prompt: The prompt to generate text from
            model: The model to use, defaults to config.default_model
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response (not implemented yet)
            
        Returns:
            Generated text
        """
        if not model:
            model = self.config.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,  # We'll handle streaming separately
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            logger.info(f"Generating text with model: {model}")
            response = await self.client.post("/api/generate", json=payload)
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Error generating text: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    async def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Stream text generation from Ollama
        
        Args:
            prompt: The prompt to generate text from
            model: The model to use, defaults to config.default_model
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Yields:
            Generated text chunks
        """
        if not model:
            model = self.config.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            logger.info(f"Streaming text generation with model: {model}")
            async with self.client.stream("POST", "/api/generate", json=payload) as response:
                if response.status_code != 200:
                    error_msg = f"Ollama API error: {response.status_code}"
                    logger.error(error_msg)
                    yield f"Error: {error_msg}"
                    return
                
                async for chunk in response.aiter_text():
                    try:
                        # Each chunk is a JSON object with a "response" field
                        data = json.loads(chunk)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        # If we can't parse the JSON, just yield the raw chunk
                        yield chunk
        except Exception as e:
            error_msg = f"Error streaming text: {str(e)}"
            logger.error(error_msg)
            yield f"Error: {error_msg}"
    
    async def close(self):
        """Close the client session"""
        await self.client.aclose()

# Create a singleton instance
_client = None

async def get_client(config: Optional[OllamaConfig] = None) -> OllamaClient:
    """
    Get the Ollama client singleton
    
    Args:
        config: Optional configuration for the client
        
    Returns:
        OllamaClient instance
    """
    global _client
    if _client is None:
        _client = OllamaClient(config)
    return _client

# Cleanup function to be registered with atexit
async def _cleanup():
    global _client
    if _client is not None:
        await _client.close()
        _client = None

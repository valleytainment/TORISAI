"""
TORIS AI - FastAPI Backend
Implements async API with proper authentication and rate limiting
"""
from typing import Dict, Any, List, Optional
import logging
import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, HTTPException, Depends, Header, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from torisai.core.ollama_client import get_client, OllamaConfig
from torisai.memory.manager import get_memory_manager, MemoryConfig
from torisai.core.tool_protocol import ToolCall, extract_tool_calls, registry

# Configure logging
logger = logging.getLogger("torisai.api")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize security
security = HTTPBearer()

# Create FastAPI app
app = FastAPI(
    title="TORIS AI API",
    description="API for TORIS AI - A local alternative to Manus AI",
    version="2.0.0"
)

# Add rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7860"],  # Add production domains as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    agent_type: str = Field("General", description="Agent type (General, Planner, Coder, Researcher)")
    model: Optional[str] = Field(None, description="Model to use (defaults to config)")

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="AI response")
    agent_type: str = Field(..., description="Agent type used")
    status: str = Field(..., description="Status of the request")

class CodeExecutionRequest(BaseModel):
    """Code execution request model"""
    code: str = Field(..., description="Code to execute")
    language: str = Field("python", description="Programming language")

class CodeExecutionResponse(BaseModel):
    """Code execution response model"""
    output: str = Field(..., description="Execution output")
    language: str = Field(..., description="Language used")
    status: str = Field(..., description="Status of the execution")

class MemorySearchRequest(BaseModel):
    """Memory search request model"""
    query: str = Field(..., description="Search query")
    limit: int = Field(5, description="Maximum number of results")

class MemorySearchResponse(BaseModel):
    """Memory search response model"""
    results: List[Dict[str, Any]] = Field(..., description="Search results")

# Authentication dependency
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify the authentication token
    
    In a production environment, this would validate against a secure token store
    For local use, we're using a simple environment variable
    """
    # Get token from environment or use a default for local development
    correct_token = os.environ.get("TORIS_API_TOKEN", "local-development-token")
    
    if credentials.credentials != correct_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "TORIS AI API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check Ollama status
    ollama_client = await get_client()
    ollama_status = await ollama_client.check_status()
    
    return {
        "status": "healthy" if ollama_status else "degraded",
        "ollama": ollama_status,
        "version": "2.0.0"
    }

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: ChatRequest,
    token: str = Depends(verify_token)
):
    """
    Chat with the AI
    
    Args:
        request: Chat request with message and agent type
        token: Authentication token
        
    Returns:
        AI response
    """
    try:
        # Get Ollama client
        ollama_client = await get_client()
        
        # Get memory manager
        memory_manager = get_memory_manager()
        
        # Get system prompt based on agent type
        system_prompt = _get_system_prompt(request.agent_type)
        
        # Get recent conversation history
        history = memory_manager.get_conversation_history(limit=5)
        context = _prepare_context(history)
        
        # Prepare full prompt
        full_prompt = f"{context}\n\nUser: {request.message}"
        
        # Generate response
        response = await ollama_client.generate(
            prompt=full_prompt,
            model=request.model,
            system_prompt=system_prompt
        )
        
        # Save to memory
        memory_manager.save_interaction(request.message, response)
        
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
                    tool_results.append(f"Error executing tool {call.name}: {str(e)}")
            
            if tool_results:
                response += "\n\n" + "\n".join(tool_results)
        
        return ChatResponse(
            response=response,
            agent_type=request.agent_type,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat
    
    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()
    
    try:
        # Get Ollama client
        ollama_client = await get_client()
        
        # Get memory manager
        memory_manager = get_memory_manager()
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            try:
                # Parse request
                request = json.loads(data)
                message = request.get("message", "")
                agent_type = request.get("agent_type", "General")
                model = request.get("model")
                
                # Get system prompt
                system_prompt = _get_system_prompt(agent_type)
                
                # Get recent conversation history
                history = memory_manager.get_conversation_history(limit=5)
                context = _prepare_context(history)
                
                # Prepare full prompt
                full_prompt = f"{context}\n\nUser: {message}"
                
                # Send initial message
                await websocket.send_json({
                    "type": "start",
                    "agent_type": agent_type
                })
                
                # Stream response
                full_response = ""
                async for chunk in ollama_client.stream_generate(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt
                ):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })
                
                # Save to memory
                memory_manager.save_interaction(message, full_response)
                
                # Process tool calls if any
                tool_calls = extract_tool_calls(full_response)
                if tool_calls:
                    # Execute tool calls and append results
                    for call in tool_calls:
                        try:
                            await websocket.send_json({
                                "type": "tool_call",
                                "name": call.name,
                                "args": call.args
                            })
                            
                            tool = registry.get(call.name)
                            if tool:
                                result = registry.execute(call)
                                await websocket.send_json({
                                    "type": "tool_result",
                                    "name": call.name,
                                    "result": result
                                })
                        except Exception as e:
                            await websocket.send_json({
                                "type": "tool_error",
                                "name": call.name,
                                "error": str(e)
                            })
                
                # Send completion message
                await websocket.send_json({
                    "type": "end",
                    "agent_type": agent_type
                })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            except Exception as e:
                logger.error(f"Error in WebSocket: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

@app.post("/execute-code", response_model=CodeExecutionResponse)
@limiter.limit("10/minute")
async def execute_code(
    request: CodeExecutionRequest,
    token: str = Depends(verify_token)
):
    """
    Execute code securely
    
    Args:
        request: Code execution request
        token: Authentication token
        
    Returns:
        Execution output
    """
    try:
        # Import here to avoid circular imports
        from torisai.tools.secure_code import execute_code as exec_code
        
        # Execute code
        output = exec_code(request.code, request.language)
        
        return CodeExecutionResponse(
            output=output,
            language=request.language,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error in execute-code endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error executing code: {str(e)}"
        )

@app.post("/memory/search", response_model=MemorySearchResponse)
@limiter.limit("20/minute")
async def search_memory(
    request: MemorySearchRequest,
    token: str = Depends(verify_token)
):
    """
    Search memory for relevant conversations
    
    Args:
        request: Memory search request
        token: Authentication token
        
    Returns:
        Search results
    """
    try:
        # Get memory manager
        memory_manager = get_memory_manager()
        
        # Search memory
        results = memory_manager.search_memory(request.query, request.limit)
        
        return MemorySearchResponse(results=results)
    except Exception as e:
        logger.error(f"Error in memory/search endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching memory: {str(e)}"
        )

@app.delete("/memory/clear")
@limiter.limit("5/minute")
async def clear_memory(token: str = Depends(verify_token)):
    """
    Clear conversation history
    
    Args:
        token: Authentication token
        
    Returns:
        Success message
    """
    try:
        # Get memory manager
        memory_manager = get_memory_manager()
        
        # Clear memory
        success = memory_manager.clear_history()
        
        if success:
            return {"status": "success", "message": "Memory cleared"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to clear memory"
            )
    except Exception as e:
        logger.error(f"Error in memory/clear endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing memory: {str(e)}"
        )

# Helper functions
def _get_system_prompt(agent_type: str) -> str:
    """
    Get system prompt based on agent type
    
    Args:
        agent_type: Agent type (General, Planner, Coder, Researcher)
        
    Returns:
        System prompt
    """
    if agent_type.lower() == "planner":
        return """You are a planning assistant in the TORIS AI system. Your role is to help break down complex tasks into manageable steps.
When given a task, analyze it carefully and create a structured plan with numbered steps.
For each step, provide clear instructions and explain why it's important.
Consider dependencies between steps and potential challenges.
Your goal is to make complex tasks achievable through systematic planning."""
    
    elif agent_type.lower() == "coder":
        return """You are a coding assistant in the TORIS AI system. Your role is to help write, debug, and explain code.
Provide clean, well-commented code that follows best practices.
When explaining code, break down complex concepts into understandable parts.
Consider edge cases and potential errors in your solutions.
Your goal is to help users implement robust software solutions."""
    
    elif agent_type.lower() == "researcher":
        return """You are a research assistant in the TORIS AI system. Your role is to help find and analyze information.
When asked a question, provide comprehensive, accurate information with proper context.
Consider multiple perspectives and cite sources when possible.
Distinguish between facts, opinions, and uncertainties in your responses.
Your goal is to help users gain deeper understanding of topics through thorough research."""
    
    else:  # General
        return """You are TORIS AI, a helpful assistant running locally on the user's computer.
You can help with a wide range of tasks including answering questions, writing content, and solving problems.
You have access to various tools including code execution, file operations, and memory storage.
Your goal is to provide helpful, accurate, and thoughtful assistance."""

def _prepare_context(history: List[Dict[str, Any]]) -> str:
    """
    Prepare context from conversation history
    
    Args:
        history: Conversation history
        
    Returns:
        Context string
    """
    # Use the most recent exchanges for context
    recent_history = history[-5:] if len(history) > 5 else history
    
    context = "Previous conversation:\n"
    for entry in recent_history:
        context += f"User: {entry['user']}\nAssistant: {entry['ai']}\n\n"
    
    return context

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

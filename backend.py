import os
import sys
import subprocess
import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./logs/toris_backend.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TORIS_BACKEND")

# Configuration
CONFIG = {
    "ollama_url": "http://localhost:11434",
    "default_model": "llama3:8b",
    "lightweight_model": "qwen:7b",
    "memory_dir": "./memory",
    "documents_dir": "./documents",
    "chroma_db_dir": "./chroma_db",
    "logs_dir": "./logs",
    "screenshots_dir": "./screenshots"
}

# Ensure directories exist
for dir_path in [CONFIG["memory_dir"], CONFIG["documents_dir"], CONFIG["chroma_db_dir"], 
                CONFIG["logs_dir"], CONFIG["screenshots_dir"]]:
    os.makedirs(dir_path, exist_ok=True)

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    def check_status(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return [model.get("name") for model in response.json().get("models", [])]
            return []
        except:
            return []
    
    def generate(self, prompt: str, model: str, system_prompt: str = None, 
                 temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate text using Ollama"""
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return f"Error processing query: {str(e)}"

class MemoryManager:
    """Manager for conversation memory and vector storage"""
    
    def __init__(self, memory_dir: str = "./memory", chroma_db_dir: str = "./chroma_db"):
        self.memory_dir = memory_dir
        self.chroma_db_dir = chroma_db_dir
        self.conversation_file = os.path.join(memory_dir, "conversation_history.json")
        
        # Initialize memory file if it doesn't exist
        if not os.path.exists(self.conversation_file):
            with open(self.conversation_file, "w") as f:
                json.dump([], f)
    
    def save_interaction(self, user_message: str, ai_response: str) -> bool:
        """Save a user-AI interaction to memory"""
        try:
            # Load existing history
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, "r") as f:
                    history = json.load(f)
            else:
                history = []
            
            # Add new entry
            history.append({
                "user": user_message,
                "ai": ai_response,
                "timestamp": time.time()
            })
            
            # Save updated history
            with open(self.conversation_file, "w") as f:
                json.dump(history, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving to memory: {str(e)}")
            return False
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, "r") as f:
                    history = json.load(f)
                
                # Return most recent entries
                return history[-limit:] if limit > 0 else history
            return []
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return []
    
    def get_formatted_history(self, limit: int = 10) -> str:
        """Get formatted conversation history as text"""
        history = self.get_conversation_history(limit)
        
        if not history:
            return "No conversation history found."
        
        formatted_history = ""
        for entry in history:
            formatted_history += f"User: {entry['user']}\n"
            formatted_history += f"AI: {entry['ai']}\n\n"
        
        return formatted_history
    
    def clear_history(self) -> bool:
        """Clear conversation history"""
        try:
            with open(self.conversation_file, "w") as f:
                json.dump([], f)
            return True
        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}")
            return False

class CodeExecutor:
    """Executor for running code in various languages"""
    
    def __init__(self, logs_dir: str = "./logs"):
        self.logs_dir = logs_dir
    
    def execute(self, code: str, language: str = "python", timeout: int = 30) -> str:
        """Execute code in the specified language"""
        if not code.strip():
            return "No code to execute"
        
        try:
            if language.lower() == "python":
                # Create a temporary file
                temp_file = os.path.join(self.logs_dir, "temp_code.py")
                with open(temp_file, "w") as f:
                    f.write(code)
                
                # Execute the code and capture output
                result = subprocess.run([sys.executable, temp_file], 
                                       capture_output=True, text=True, timeout=timeout)
                
                output = result.stdout
                if result.stderr:
                    output += "\nErrors:\n" + result.stderr
                
                return output
            elif language.lower() == "javascript":
                # Create a temporary file
                temp_file = os.path.join(self.logs_dir, "temp_code.js")
                with open(temp_file, "w") as f:
                    f.write(code)
                
                # Check if Node.js is installed
                try:
                    # Execute the code and capture output
                    result = subprocess.run(["node", temp_file], 
                                           capture_output=True, text=True, timeout=timeout)
                    
                    output = result.stdout
                    if result.stderr:
                        output += "\nErrors:\n" + result.stderr
                    
                    return output
                except FileNotFoundError:
                    return "Error: Node.js is not installed or not in PATH"
            elif language.lower() == "shell" or language.lower() == "bash":
                # Create a temporary file
                temp_file = os.path.join(self.logs_dir, "temp_code.sh")
                with open(temp_file, "w") as f:
                    f.write(code)
                
                # Make the file executable
                os.chmod(temp_file, 0o755)
                
                # Execute the code and capture output
                if sys.platform == "win32":
                    result = subprocess.run(["powershell", "-Command", temp_file], 
                                           capture_output=True, text=True, timeout=timeout)
                else:
                    result = subprocess.run(["bash", temp_file], 
                                           capture_output=True, text=True, timeout=timeout)
                
                output = result.stdout
                if result.stderr:
                    output += "\nErrors:\n" + result.stderr
                
                return output
            else:
                return f"Unsupported language: {language}"
        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out ({timeout} seconds limit)"
        except Exception as e:
            return f"Error executing code: {str(e)}"

class CommandProcessor:
    """Processor for handling console commands"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def process_command(self, command: str) -> str:
        """Process a console command"""
        if not command.strip():
            return "No command to execute"
        
        try:
            if command.startswith("search:"):
                query = command[7:].strip()
                return self._handle_search(query)
            
            elif command.startswith("browse:"):
                url = command[7:].strip()
                return self._handle_browse(url)
            
            elif command.startswith("file:"):
                parts = command[5:].strip().split(" ", 1)
                if len(parts) < 2:
                    return "Invalid file command. Use: file:read|write|list path [content]"
                
                operation = parts[0]
                return self._handle_file_operation(operation, parts[1:])
            
            elif command.startswith("model:"):
                model = command[6:].strip()
                return self._handle_model_change(model)
            
            elif command.startswith("help"):
                return self._show_help()
            
            else:
                return f"Unknown command: {command}\n{self._show_help()}"
        
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def _handle_search(self, query: str) -> str:
        """Handle search command"""
        # In a full implementation, this would use a search API
        return f"Search results for '{query}':\nThis feature requires web search integration."
    
    def _handle_browse(self, url: str) -> str:
        """Handle browse command"""
        # In a full implementation, this would use a web browser
        return f"Web content from {url}:\nThis feature requires web browsing integration."
    
    def _handle_file_operation(self, operation: str, args: List[str]) -> str:
        """Handle file operations"""
        if operation == "list":
            path = args[0] if args else "."
            try:
                files = os.listdir(path)
                return f"Directory listing for {path}:\n" + "\n".join(files)
            except Exception as e:
                return f"Error listing directory: {str(e)}"
        
        elif operation == "read":
            if not args:
                return "Missing file path. Use: file:read path"
            path = args[0]
            try:
                with open(path, "r") as f:
                    content = f.read()
                return f"File content from {path}:\n{content}"
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        elif operation == "write":
            if len(args) < 2:
                return "Invalid write command. Use: file:write path content"
            path = args[0]
            content = args[1]
            try:
                with open(path, "w") as f:
                    f.write(content)
                return f"Successfully wrote to {path}"
            except Exception as e:
                return f"Error writing file: {str(e)}"
        
        else:
            return f"Unknown file operation: {operation}"
    
    def _handle_model_change(self, model: str) -> str:
        """Handle model change command"""
        available_models = [self.config["default_model"], self.config["lightweight_model"]]
        if model in available_models:
            return f"Switched to model: {model}"
        else:
            return f"Unknown model: {model}. Available models: {', '.join(available_models)}"
    
    def _show_help(self) -> str:
        """Show help text"""
        return """Available commands:
- search:query - Search the web for information
- browse:url - Browse a webpage
- file:list [path] - List files in directory
- file:read path - Read file content
- file:write path content - Write content to file
- model:name - Switch to a different model
- help - Show this help text"""

class AgentManager:
    """Manager for different agent types and roles"""
    
    def __init__(self, ollama_client: OllamaClient, memory_manager: MemoryManager):
        self.ollama_client = ollama_client
        self.memory_manager = memory_manager
        self.current_agent = "General"
        self.status = "ACTIVE"
        self.steps = 0
    
    def process_query(self, message: str, history: List[Tuple[str, str]], 
                     agent_type: str = None) -> Tuple[List[Tuple[str, str]], str, str, str]:
        """Process a user query with the appropriate agent"""
        if not message.strip():
            return history, self.status, self.current_agent, str(self.steps)
        
        # Update agent type if specified
        if agent_type and agent_type != self.current_agent:
            self.current_agent = agent_type
        
        # Update history with user message
        history = history + [(message, None)]
        self.steps += 1
        
        try:
            # Get system prompt based on agent type
            system_prompt = self._get_system_prompt(self.current_agent)
            
            # Prepare context from recent history
            context = self._prepare_context(history)
            
            # Get response from Ollama
            full_prompt = f"{context}\n\nUser: {message}"
            response = self.ollama_client.generate(
                prompt=full_prompt,
                model=CONFIG["default_model"],
                system_prompt=system_prompt
            )
            
            # Update history with AI response
            history[-1] = (message, response)
            
            # Save to memory
            self.memory_manager.save_interaction(message, response)
            
            return history, self.status, self.current_agent, str(self.steps)
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            # Update history with error message
            history[-1] = (message, f"Error: {str(e)}")
            self.status = "ERROR"
            return history, self.status, self.current_agent, str(self.steps)
    
    def _get_system_prompt(self, agent_type: str) -> str:
        """Get system prompt based on agent type"""
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
    
    def _prepare_context(self, history: List[Tuple[str, str]]) -> str:
        """Prepare context from conversation history"""
        # Use the most recent exchanges for context
        recent_history = history[-5:] if len(history) > 5 else history
        
        context = "Previous conversation:\n"
        for user_msg, ai_msg in recent_history:
            if user_msg and ai_msg:  # Only include complete exchanges
                context += f"User: {user_msg}\nAssistant: {ai_msg}\n\n"
        
        return context

class TorisBackend:
    """Main backend class for TORIS AI"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ollama_client = OllamaClient(config["ollama_url"])
        self.memory_manager = MemoryManager(config["memory_dir"], config["chroma_db_dir"])
        self.code_executor = CodeExecutor(config["logs_dir"])
        self.command_processor = CommandProcessor(config)
        self.agent_manager = AgentManager(self.ollama_client, self.memory_manager)
    
    def initialize(self) -> str:
        """Initialize the backend system"""
        # Check if Ollama is running
        if not self.ollama_client.check_status():
            logger.warning("Ollama is not running")
            return "Ollama is not running. Please start it manually."
        
        # Check for required models
        available_models = self.ollama_client.list_models()
        missing_models = []
        for model in [self.config["default_model"], self.config["lightweight_model"]]:
            if model not in available_models:
                missing_models.append(model)
        
        if missing_models:
            logger.warning(f"Missing models: {missing_models}")
            return f"Missing required models: {', '.join(missing_models)}. Please pull them using Ollama."
        
        logger.info("TORIS AI backend initialized successfully")
        return "TORIS AI backend initialized successfully"
    
    def process_query(self, message: str, history: List[Tuple[str, str]], 
                     agent_type: str = None) -> Tuple[List[Tuple[str, str]], str, str, str]:
        """Process a user query"""
        return self.agent_manager.process_query(message, history, agent_type)
    
    def execute_code(self, code: str, language: str = "python") -> str:
        """Execute code"""
        return self.code_executor.execute(code, language)
    
    def process_command(self, command: str) -> str:
        """Process a console command"""
        return self.command_processor.process_command(command)
    
    def get_memory_view(self) -> str:
        """Get memory view"""
        return self.memory_manager.get_formatted_history()

# Create a singleton instance
toris_backend = TorisBackend(CONFIG)

# Export functions for the GUI to use
def initialize_backend():
    return toris_backend.initialize()

def process_query(message, history, agent_type=None):
    return toris_backend.process_query(message, history, agent_type)

def execute_code(code, language="python"):
    return toris_backend.execute_code(code, language)

def process_command(command):
    return toris_backend.process_command(command)

def get_memory_view():
    return toris_backend.get_memory_view()

# For testing
if __name__ == "__main__":
    print(initialize_backend())
    history = []
    history, status, agent_type, steps = process_query("Hello, who are you?", history)
    print(f"Status: {status}, Agent: {agent_type}, Steps: {steps}")
    print(f"Response: {history[-1][1]}")
    
    code_result = execute_code("print('Hello, world!')")
    print(f"Code execution: {code_result}")
    
    command_result = process_command("help")
    print(f"Command result: {command_result}")
    
    memory_view = get_memory_view()
    print(f"Memory view: {memory_view}")

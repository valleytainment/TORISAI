# Implementation Guide for Local AI Agent (TORIS AI)

This guide provides step-by-step instructions for implementing a local AI agent with capabilities similar to Manus AI, using only open-source components and requiring no cloud costs.

## 1. Setting Up the Local LLM Backend (Ollama)

### Installation

#### Windows
```powershell
# Download and run the installer
Invoke-WebRequest -Uri "https://ollama.ai/download/OllamaSetup.exe" -OutFile "$env:TEMP\OllamaSetup.exe"
Start-Process "$env:TEMP\OllamaSetup.exe"
```

#### macOS
```bash
# Install using Homebrew
brew install ollama

# Or download from the website
curl -fsSL https://ollama.ai/download/ollama-darwin.tar.gz | tar -xzf - -C /usr/local/bin
```

#### Linux
```bash
# Install using curl
curl -fsSL https://ollama.ai/install.sh | sh
```

### Pulling Models

After installation, pull the recommended models:

```bash
# Primary model for general use
ollama pull llama3:8b

# Specialized model for coding tasks
ollama pull deepseek-coder:6.7b

# Lightweight alternative
ollama pull qwen:7b
```

### Starting the Ollama Server

```bash
# Start the Ollama server
ollama serve
```

This will start the Ollama server on http://localhost:11434 by default.

## 2. Implementing the Orchestration Layer (SuperAGI)

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.10+

### Installation

```bash
# Clone the SuperAGI repository
git clone https://github.com/TransformerOptimus/SuperAGI.git
cd SuperAGI

# Create a .env file
cp config/config.yaml.example config/config.yaml

# Edit the config.yaml file to use Ollama
# Set LLM_PROVIDER=ollama
# Set LLM_BASE_URL=http://host.docker.internal:11434
# For Linux, use LLM_BASE_URL=http://172.17.0.1:11434 instead

# Start SuperAGI using Docker Compose
docker compose up -d
```

### Accessing the Dashboard

Once running, access the SuperAGI dashboard at http://localhost:3000

## 3. Integrating Command Execution (Open Interpreter)

### Installation

```bash
# Install Open Interpreter
pip install open-interpreter

# Create a Python script to integrate Open Interpreter with our agent
```

Create a file named `interpreter_integration.py`:

```python
import interpreter
from langchain.tools import BaseTool
from typing import Optional, Type

class InterpreterTool(BaseTool):
    name = "code_interpreter"
    description = "Execute code in a secure environment. Input should be valid code in Python, JavaScript, or shell."
    
    def _run(self, code: str) -> str:
        interpreter.reset()
        return interpreter.interpret(code)
    
    def _arun(self, code: str) -> str:
        raise NotImplementedError("Async not implemented")

# Example usage
if __name__ == "__main__":
    tool = InterpreterTool()
    result = tool.run("print('Hello, world!')")
    print(result)
```

## 4. Setting Up Memory and Storage (Chroma)

### Installation

```bash
# Install Chroma and its dependencies
pip install chromadb langchain
```

Create a file named `memory_setup.py`:

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
import os

# Initialize embeddings model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Create a persistent Chroma vector store
def create_vector_store(documents_dir, persist_directory):
    documents = []
    for file in os.listdir(documents_dir):
        if file.endswith('.txt'):
            loader = TextLoader(os.path.join(documents_dir, file))
            documents.extend(loader.load())
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectorstore.persist()
    return vectorstore

# Example usage
if __name__ == "__main__":
    create_vector_store("./documents", "./chroma_db")
```

## 5. Integrating Skills and Tools Framework (LangChain)

### Installation

```bash
# Install LangChain and related packages
pip install langchain requests beautifulsoup4 playwright
playwright install
```

Create a file named `tools_setup.py`:

```python
from langchain.agents import Tool
from langchain.tools import BaseTool
from langchain.utilities import GoogleSearchAPIWrapper, WikipediaAPIWrapper
from langchain.tools.playwright.utils import create_sync_playwright_browser
from interpreter_integration import InterpreterTool
import requests
from bs4 import BeautifulSoup
from typing import Optional

# Web search tool
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for information. Input should be a search query."
    
    def _run(self, query: str) -> str:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        for g in soup.find_all('div', class_='g'):
            anchors = g.find_all('a')
            if anchors:
                link = anchors[0]['href']
                title = g.find('h3').text if g.find('h3') else "No title"
                snippet = g.find('div', class_='VwiC3b').text if g.find('div', class_='VwiC3b') else "No snippet"
                results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n")
        return "\n".join(results[:5])
    
    def _arun(self, query: str) -> str:
        raise NotImplementedError("Async not implemented")

# Web browsing tool
class WebBrowsingTool(BaseTool):
    name = "web_browse"
    description = "Browse a specific webpage and extract its content. Input should be a URL."
    
    def __init__(self):
        super().__init__()
        self.browser = create_sync_playwright_browser()
    
    def _run(self, url: str) -> str:
        page = self.browser.new_page()
        page.goto(url)
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract main content, removing scripts, styles, etc.
        for script in soup(["script", "style", "meta", "noscript"]):
            script.extract()
        
        text = soup.get_text(separator='\n', strip=True)
        return text[:10000]  # Limit to first 10000 chars
    
    def _arun(self, url: str) -> str:
        raise NotImplementedError("Async not implemented")

# File operations tool
class FileOperationsTool(BaseTool):
    name = "file_operations"
    description = "Perform file operations like reading, writing, and listing files. Input format: 'operation:path:content'. Operations: read, write, list."
    
    def _run(self, input_str: str) -> str:
        parts = input_str.split(':', 2)
        operation = parts[0].lower()
        
        if operation == "list":
            path = parts[1] if len(parts) > 1 else "."
            return str(os.listdir(path))
        
        elif operation == "read":
            if len(parts) < 2:
                return "Error: Path required for read operation"
            path = parts[1]
            try:
                with open(path, 'r') as file:
                    return file.read()
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        elif operation == "write":
            if len(parts) < 3:
                return "Error: Path and content required for write operation"
            path = parts[1]
            content = parts[2]
            try:
                with open(path, 'w') as file:
                    file.write(content)
                return f"Successfully wrote to {path}"
            except Exception as e:
                return f"Error writing file: {str(e)}"
        
        return f"Unknown operation: {operation}"
    
    def _arun(self, input_str: str) -> str:
        raise NotImplementedError("Async not implemented")

# Create a list of tools
def get_tools():
    return [
        InterpreterTool(),
        WebSearchTool(),
        WebBrowsingTool(),
        FileOperationsTool()
    ]

# Example usage
if __name__ == "__main__":
    tools = get_tools()
    for tool in tools:
        print(f"Tool: {tool.name} - {tool.description}")
```

## 6. Creating Specialized Agent Roles

Create a file named `agent_roles.py`:

```python
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOllama
from tools_setup import get_tools
from memory_setup import create_vector_store
import os

class AgentFactory:
    def __init__(self, model_name="llama3:8b"):
        self.llm = ChatOllama(model=model_name, base_url="http://localhost:11434")
        self.tools = get_tools()
        
        # Create memory if it doesn't exist
        if not os.path.exists("./chroma_db"):
            create_vector_store("./documents", "./chroma_db")
    
    def create_planner_agent(self):
        """Creates an agent specialized in planning and task decomposition"""
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
    
    def create_coder_agent(self):
        """Creates an agent specialized in writing and executing code"""
        # Use a coding-specific model if available
        coding_llm = ChatOllama(model="deepseek-coder:6.7b", base_url="http://localhost:11434")
        return initialize_agent(
            tools=self.tools,
            llm=coding_llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15
        )
    
    def create_researcher_agent(self):
        """Creates an agent specialized in information gathering"""
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=20
        )

# Example usage
if __name__ == "__main__":
    factory = AgentFactory()
    planner = factory.create_planner_agent()
    result = planner.run("Create a plan to build a simple website")
    print(result)
```

## 7. Developing the User Interface (Gradio)

### Installation

```bash
# Install Gradio
pip install gradio
```

Create a file named `app.py`:

```python
import gradio as gr
from agent_roles import AgentFactory
import os
import time

# Initialize agent factory
factory = AgentFactory()

# Create agents
planner_agent = factory.create_planner_agent()
coder_agent = factory.create_coder_agent()
researcher_agent = factory.create_researcher_agent()

def process_query(query, agent_type, history):
    # Update history with user message
    history.append(("You", query))
    
    # Select the appropriate agent
    if agent_type == "Planner":
        agent = planner_agent
    elif agent_type == "Coder":
        agent = coder_agent
    elif agent_type == "Researcher":
        agent = researcher_agent
    else:
        # Default to planner
        agent = planner_agent
    
    # Process the query
    try:
        # Add thinking indicator
        history.append(("TORIS AI", "Thinking..."))
        yield history
        
        # Run the agent
        result = agent.run(query)
        
        # Replace thinking indicator with actual response
        history[-1] = ("TORIS AI", result)
        yield history
    except Exception as e:
        # Replace thinking indicator with error message
        history[-1] = ("TORIS AI", f"Error: {str(e)}")
        yield history

# Create the Gradio interface
with gr.Blocks(title="TORIS AI - Local AI Agent") as demo:
    gr.Markdown("# TORIS AI - Your Local AI Agent")
    gr.Markdown("A cost-free alternative to Manus AI that runs entirely on your local machine.")
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Conversation", height=500)
            msg = gr.Textbox(label="Your message", placeholder="Ask me anything...", lines=3)
            
            with gr.Row():
                submit = gr.Button("Submit", variant="primary")
                clear = gr.Button("Clear")
        
        with gr.Column(scale=1):
            agent_type = gr.Radio(
                ["Planner", "Coder", "Researcher"], 
                label="Agent Type", 
                value="Planner",
                info="Select the type of agent best suited for your task"
            )
            
            gr.Markdown("### Agent Capabilities")
            gr.Markdown("- **Planner**: Task decomposition and planning")
            gr.Markdown("- **Coder**: Writing and executing code")
            gr.Markdown("- **Researcher**: Information gathering and research")
    
    # Set up event handlers
    submit.click(
        process_query, 
        inputs=[msg, agent_type, chatbot], 
        outputs=[chatbot]
    )
    
    msg.submit(
        process_query, 
        inputs=[msg, agent_type, chatbot], 
        outputs=[chatbot]
    )
    
    clear.click(lambda: None, None, chatbot, queue=False)

# Launch the app
if __name__ == "__main__":
    demo.launch()
```

## 8. Creating a Main Script to Run the Entire System

Create a file named `run_toris.py`:

```python
import subprocess
import os
import time
import sys
import webbrowser
import threading

def check_ollama_running():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Start Ollama if not running"""
    if not check_ollama_running():
        print("Starting Ollama...")
        if sys.platform == "win32":
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for Ollama to start
        for _ in range(30):  # Wait up to 30 seconds
            if check_ollama_running():
                print("Ollama started successfully")
                break
            time.sleep(1)
        else:
            print("Failed to start Ollama. Please start it manually.")
            return False
    else:
        print("Ollama is already running")
    return True

def ensure_models_pulled():
    """Ensure required models are pulled"""
    models = ["llama3:8b", "deepseek-coder:6.7b"]
    
    for model in models:
        print(f"Checking if {model} is available...")
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if model not in result.stdout:
            print(f"Pulling {model}...")
            subprocess.run(["ollama", "pull", model], check=True)
        else:
            print(f"{model} is already available")

def create_directories():
    """Create necessary directories"""
    directories = ["./documents", "./chroma_db"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def start_ui():
    """Start the Gradio UI"""
    print("Starting TORIS AI interface...")
    subprocess.run(["python", "app.py"])

def main():
    print("Initializing TORIS AI - Your Local AI Agent")
    
    # Check dependencies
    try:
        import gradio, langchain, requests, bs4, chromadb
        print("All required Python packages are installed")
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please run: pip install gradio langchain requests beautifulsoup4 chromadb playwright")
        return
    
    # Start Ollama
    if not start_ollama():
        return
    
    # Ensure models are pulled
    ensure_models_pulled()
    
    # Create necessary directories
    create_directories()
    
    # Start the UI
    start_ui()

if __name__ == "__main__":
    main()
```

## 9. Creating a Setup Script

Create a file named `setup.py`:

```python
import subprocess
import sys
import os

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
        "langchain",
        "requests",
        "beautifulsoup4",
        "chromadb",
        "playwright",
        "open-interpreter",
        "sentence-transformers"
    ]
    
    print("Installing required Python packages...")
    subprocess.run([sys.executable, "-m", "pip", "install"] + packages, check=True)
    
    # Install Playwright browsers
    print("Installing Playwright browsers...")
    subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)

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
    
    if sys.platform == "win32":
        print("Windows:")
        print("1. Download the installer from https://ollama.ai/download/OllamaSetup.exe")
        print("2. Run the installer and follow the instructions")
    
    elif sys.platform == "darwin":
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
    directories = ["./documents", "./chroma_db"]
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
    print("To start TORIS AI, run: python run_toris.py")

if __name__ == "__main__":
    main()
```

## 10. Creating a README File

Create a file named `README.md`:

```markdown
# TORIS AI - Your Local AI Agent

TORIS AI is a powerful, cost-free alternative to Manus AI that runs entirely on your local machine. It combines multiple open-source components to provide a comprehensive AI assistant with capabilities for planning, coding, research, and more.

## Features

- **100% Local Operation**: All processing happens on your machine with no cloud costs
- **Multiple Specialized Agents**: Planner, Coder, and Researcher agents for different tasks
- **Code Execution**: Safely run Python, JavaScript, and shell commands
- **Web Search and Browsing**: Find and extract information from the internet
- **Long-term Memory**: Store and retrieve information using vector databases
- **User-friendly Interface**: Simple web interface for interacting with the AI

## System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 50GB minimum
- **GPU**: Optional but recommended for better performance

## Installation

1. Install Python 3.8+ if not already installed
2. Install Ollama from [ollama.ai](https://ollama.ai)
3. Clone this repository:
   ```
   git clone https://github.com/yourusername/toris-ai.git
   cd toris-ai
   ```
4. Run the setup script:
   ```
   python setup.py
   ```

## Usage

1. Start TORIS AI:
   ```
   python run_toris.py
   ```
2. Open your web browser and navigate to http://localhost:7860
3. Select the appropriate agent type for your task
4. Enter your query and press Submit

## Components

TORIS AI integrates the following open-source components:

- **Ollama**: Local LLM backend
- **LangChain**: Tools and agent framework
- **Chroma**: Vector database for memory
- **Open Interpreter**: Code execution
- **Gradio**: User interface

## Customization

- Add new tools by extending the `tools_setup.py` file
- Add new agent types in `agent_roles.py`
- Modify the UI in `app.py`
- Add documents to the `./documents` directory for the AI to learn from

## Troubleshooting

- If Ollama fails to start, try starting it manually before running TORIS AI
- If you encounter memory errors, try using a smaller model like `qwen:7b`
- For GPU acceleration, ensure you have the appropriate CUDA drivers installed

## License

This project is open-source and available under the MIT License.
```

## 11. Final Integration and Testing

1. Ensure all files are in the same directory
2. Run the setup script:
   ```bash
   python setup.py
   ```
3. Start the system:
   ```bash
   python run_toris.py
   ```
4. Test the system with various queries to ensure all components are working correctly

## 12. Optimization and Customization

### Performance Optimization

- For systems with limited RAM, use smaller models like `qwen:7b`
- For systems with GPUs, ensure Ollama is configured to use GPU acceleration
- Adjust the `max_iterations` parameter in agent creation to balance thoroughness with speed

### Adding Custom Tools

To add custom tools, extend the `tools_setup.py` file with new tool classes that inherit from `BaseTool`.

### Adding Custom Knowledge

Place text files in the `./documents` directory to provide domain-specific knowledge to the AI.

## Conclusion

This implementation guide provides a comprehensive approach to building a local AI agent with capabilities similar to Manus AI, using only open-source components and requiring no cloud costs. The modular architecture allows for easy customization and extension to meet specific needs.

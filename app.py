import gradio as gr
import os
import subprocess
import sys
import time
import threading
import requests
from bs4 import BeautifulSoup
import json

# Configuration
CONFIG = {
    "ollama_url": "http://localhost:11434",
    "default_model": "llama3:8b",
    "code_model": "deepseek-coder:6.7b",
    "memory_dir": "./memory",
    "documents_dir": "./documents",
    "chroma_db_dir": "./chroma_db"
}

# Ensure directories exist
for dir_path in [CONFIG["memory_dir"], CONFIG["documents_dir"], CONFIG["chroma_db_dir"]]:
    os.makedirs(dir_path, exist_ok=True)

# Check if Ollama is running
def check_ollama_running():
    try:
        response = requests.get(f"{CONFIG['ollama_url']}/api/tags")
        return response.status_code == 200
    except:
        return False

# Start Ollama if not running
def start_ollama():
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

# Check if required models are available
def check_models():
    try:
        response = requests.get(f"{CONFIG['ollama_url']}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            
            missing_models = []
            for model in [CONFIG["default_model"], CONFIG["code_model"]]:
                if model not in model_names:
                    missing_models.append(model)
            
            return missing_models
        return [CONFIG["default_model"], CONFIG["code_model"]]
    except:
        return [CONFIG["default_model"], CONFIG["code_model"]]

# Pull missing models
def pull_models(missing_models):
    for model in missing_models:
        print(f"Pulling {model}...")
        subprocess.run(["ollama", "pull", model], check=True)

# LLM interaction
def query_llm(prompt, model=None, system=None, temperature=0.7):
    if model is None:
        model = CONFIG["default_model"]
    
    url = f"{CONFIG['ollama_url']}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False
    }
    
    if system:
        payload["system"] = system
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

# Web search tool
def web_search(query):
    try:
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
        
        return "\n".join(results[:5]) if results else "No results found"
    except Exception as e:
        return f"Error performing web search: {str(e)}"

# Web browsing tool
def web_browse(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main content, removing scripts, styles, etc.
        for script in soup(["script", "style", "meta", "noscript"]):
            script.extract()
        
        text = soup.get_text(separator='\n', strip=True)
        return text[:10000]  # Limit to first 10000 chars
    except Exception as e:
        return f"Error browsing webpage: {str(e)}"

# Code execution tool
def execute_code(code, language="python"):
    try:
        if language.lower() == "python":
            # Create a temporary file
            temp_file = os.path.join(CONFIG["memory_dir"], "temp_code.py")
            with open(temp_file, "w") as f:
                f.write(code)
            
            # Execute the code and capture output
            result = subprocess.run([sys.executable, temp_file], 
                                   capture_output=True, 
                                   text=True)
            
            # Return the output or error
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
        else:
            return f"Language {language} not supported yet"
    except Exception as e:
        return f"Error executing code: {str(e)}"

# File operations tool
def file_operations(operation, path, content=None):
    try:
        if operation.lower() == "list":
            return str(os.listdir(path))
        
        elif operation.lower() == "read":
            with open(path, 'r') as file:
                return file.read()
        
        elif operation.lower() == "write":
            if content is None:
                return "Error: Content required for write operation"
            with open(path, 'w') as file:
                file.write(content)
            return f"Successfully wrote to {path}"
        
        else:
            return f"Unknown operation: {operation}"
    except Exception as e:
        return f"Error with file operation: {str(e)}"

# Memory management
class Memory:
    def __init__(self, memory_file=os.path.join(CONFIG["memory_dir"], "conversation_history.json")):
        self.memory_file = memory_file
        self.ensure_memory_file()
    
    def ensure_memory_file(self):
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w') as f:
                json.dump([], f)
    
    def add_interaction(self, user_message, ai_response):
        try:
            # Load existing memory
            with open(self.memory_file, 'r') as f:
                memory = json.load(f)
            
            # Add new interaction
            memory.append({
                "timestamp": time.time(),
                "user": user_message,
                "ai": ai_response
            })
            
            # Save updated memory
            with open(self.memory_file, 'w') as f:
                json.dump(memory, f, indent=2)
        except Exception as e:
            print(f"Error adding to memory: {str(e)}")
    
    def get_recent_history(self, limit=5):
        try:
            with open(self.memory_file, 'r') as f:
                memory = json.load(f)
            
            # Return the most recent interactions
            recent = memory[-limit:] if len(memory) > limit else memory
            
            # Format for context
            context = ""
            for item in recent:
                context += f"User: {item['user']}\nAI: {item['ai']}\n\n"
            
            return context
        except Exception as e:
            print(f"Error retrieving memory: {str(e)}")
            return ""

# Initialize memory
memory = Memory()

# Agent types and their system prompts
AGENT_PROMPTS = {
    "Planner": """You are TORIS AI's Planning Agent. Your role is to help users break down complex tasks into manageable steps.
Focus on:
1. Understanding the user's overall goal
2. Decomposing tasks into logical sequences
3. Identifying dependencies between steps
4. Estimating time and resources needed
5. Creating clear, actionable plans

Always be thorough, methodical, and consider potential obstacles. When appropriate, use tools like web search for research, code execution for calculations, and file operations for documentation.""",
    
    "Coder": """You are TORIS AI's Coding Agent. Your role is to help users with programming and development tasks.
Focus on:
1. Writing clean, efficient, and well-documented code
2. Debugging and fixing issues in existing code
3. Explaining technical concepts clearly
4. Following best practices for the language/framework
5. Testing and validating solutions

Always provide complete, working solutions that can be executed directly. Use tools like code execution to test your solutions, web search for documentation, and file operations to save and manage code files.""",
    
    "Researcher": """You are TORIS AI's Research Agent. Your role is to help users gather and analyze information.
Focus on:
1. Finding accurate, relevant information from reliable sources
2. Synthesizing data from multiple sources
3. Evaluating the credibility of information
4. Organizing findings in a clear, structured way
5. Identifying gaps in available information

Always cite your sources and provide balanced perspectives. Use tools like web search to find information, web browsing to explore specific pages, and file operations to save and organize research findings."""
}

# Process user query
def process_query(query, agent_type, history):
    if not query.strip():
        return history
    
    # Update history with user message
    history.append(("You", query))
    
    # Add thinking indicator
    history.append(("TORIS AI", "Thinking..."))
    
    try:
        # Select the appropriate model and system prompt
        if agent_type == "Coder":
            model = CONFIG["code_model"]
        else:
            model = CONFIG["default_model"]
        
        system_prompt = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS["Planner"])
        
        # Get recent conversation history for context
        context = memory.get_recent_history(3)
        
        # Prepare the full prompt with tools information
        full_prompt = f"""
{context}

You have access to the following tools:
1. web_search(query): Search the web for information
2. web_browse(url): Browse and extract content from a webpage
3. execute_code(code, language): Execute code and return the result
4. file_operations(operation, path, content): Perform file operations (list, read, write)

When you need to use a tool, use the format:
TOOL: tool_name(parameters)
Example: TOOL: web_search("latest AI developments")

User: {query}
"""
        
        # Get response from LLM
        response = query_llm(full_prompt, model=model, system=system_prompt)
        
        # Process tool calls in the response
        if "TOOL:" in response:
            # Extract tool calls
            tool_calls = []
            lines = response.split("\n")
            for line in lines:
                if line.strip().startswith("TOOL:"):
                    tool_calls.append(line.strip()[6:].strip())
            
            # Execute tool calls and append results
            tool_results = []
            for call in tool_calls:
                try:
                    # Parse the tool call
                    if "web_search(" in call:
                        query = call.split("web_search(")[1].split(")")[0].strip('"\'')
                        result = web_search(query)
                        tool_results.append(f"Web Search Result for '{query}':\n{result}")
                    
                    elif "web_browse(" in call:
                        url = call.split("web_browse(")[1].split(")")[0].strip('"\'')
                        result = web_browse(url)
                        tool_results.append(f"Web Browse Result for {url}:\n{result}")
                    
                    elif "execute_code(" in call:
                        # Simple parsing for demonstration
                        parts = call.split("execute_code(")[1].split(")")[0].split(",")
                        if len(parts) > 1:
                            code = parts[0].strip('"\'')
                            language = parts[1].strip('"\'')
                            result = execute_code(code, language)
                        else:
                            code = parts[0].strip('"\'')
                            result = execute_code(code)
                        tool_results.append(f"Code Execution Result:\n{result}")
                    
                    elif "file_operations(" in call:
                        # Simple parsing for demonstration
                        parts = call.split("file_operations(")[1].split(")")[0].split(",")
                        operation = parts[0].strip('"\'')
                        path = parts[1].strip('"\'')
                        content = parts[2].strip('"\'') if len(parts) > 2 else None
                        result = file_operations(operation, path, content)
                        tool_results.append(f"File Operation Result:\n{result}")
                
                except Exception as e:
                    tool_results.append(f"Error executing tool call: {str(e)}")
            
            # Get a final response that incorporates the tool results
            tool_results_text = "\n\n".join(tool_results)
            final_prompt = f"""
{context}

User: {query}

You used the following tools and got these results:
{tool_results_text}

Based on these results, provide a final comprehensive response to the user's query.
"""
            response = query_llm(final_prompt, model=model, system=system_prompt)
        
        # Add to memory
        memory.add_interaction(query, response)
        
        # Replace thinking indicator with actual response
        history[-1] = ("TORIS AI", response)
        
    except Exception as e:
        # Replace thinking indicator with error message
        history[-1] = ("TORIS AI", f"Error: {str(e)}")
    
    return history

# Initialize the system
def initialize_system():
    # Start Ollama if not running
    if not start_ollama():
        return "Failed to start Ollama. Please start it manually."
    
    # Check for required models
    missing_models = check_models()
    if missing_models:
        try:
            pull_models(missing_models)
        except Exception as e:
            return f"Error pulling models: {str(e)}"
    
    return "System initialized successfully"

# Create the Gradio interface
with gr.Blocks(title="TORIS AI - Local AI Agent") as demo:
    gr.Markdown("# TORIS AI - Your Local AI Agent")
    gr.Markdown("A cost-free alternative to Manus AI that runs entirely on your local machine.")
    
    # System initialization
    init_status = gr.Textbox(label="Initialization Status", value="Initializing...", interactive=False)
    
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
    
    # Initialize the system on startup
    demo.load(lambda: initialize_system(), None, init_status)

# Launch the app
if __name__ == "__main__":
    demo.launch()

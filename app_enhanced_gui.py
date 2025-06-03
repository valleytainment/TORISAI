import gradio as gr
import os
import subprocess
import sys
import time
import threading
import requests
from bs4 import BeautifulSoup
import json
import base64
from PIL import Image
import io

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

# Initialize logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(CONFIG["logs_dir"], "toris_ai.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TORIS_AI")

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
        logger.info("Starting Ollama...")
        if sys.platform == "win32":
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for Ollama to start
        for _ in range(30):  # Wait up to 30 seconds
            if check_ollama_running():
                logger.info("Ollama started successfully")
                return True
            time.sleep(1)
        
        logger.error("Failed to start Ollama. Please start it manually.")
        return False
    else:
        logger.info("Ollama is already running")
        return True

# Check SuperAGI status
def check_superagi_status():
    try:
        # This is a simplified check - in production we would check the actual API
        if os.path.exists("SuperAGI"):
            return True
        return False
    except:
        return False

# Process user query through Ollama
def process_query_ollama(message, model=None):
    if not model:
        model = CONFIG["default_model"]
    
    try:
        url = f"{CONFIG['ollama_url']}/api/generate"
        
        payload = {
            "model": model,
            "prompt": message,
            "stream": False
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error processing query: {str(e)}"

# Process user query with agent type selection
def process_query(message, history, agent_type="General"):
    if not message.strip():
        return history, "ACTIVE", agent_type, str(len(history) if history else 0)
    
    # Update history with user message
    history = history + [(message, None)]
    
    try:
        # Process based on agent type
        if agent_type.lower() == "planner":
            system_prompt = "You are a planning assistant. Help break down complex tasks into manageable steps."
        elif agent_type.lower() == "coder":
            system_prompt = "You are a coding assistant. Help write, debug, and explain code."
        elif agent_type.lower() == "researcher":
            system_prompt = "You are a research assistant. Help find and analyze information."
        else:  # General
            system_prompt = "You are TORIS AI, a helpful assistant."
        
        # Prepare the full prompt with context
        full_prompt = f"{system_prompt}\n\nUser: {message}"
        
        # Get response from Ollama
        response = process_query_ollama(full_prompt)
        
        # Update history with AI response
        history[-1] = (message, response)
        
        # Update agent status
        agent_status = "ACTIVE"
        steps_value = str(len(history))
        
        return history, agent_status, agent_type, steps_value
    except Exception as e:
        # Update history with error message
        history[-1] = (message, f"Error: {str(e)}")
        return history, "ERROR", agent_type, str(len(history))

# Execute code
def execute_code(code, language="python"):
    if not code.strip():
        return "No code to execute"
    
    try:
        if language.lower() == "python":
            # Create a temporary file
            temp_file = os.path.join(CONFIG["logs_dir"], "temp_code.py")
            with open(temp_file, "w") as f:
                f.write(code)
            
            # Execute the code and capture output
            result = subprocess.run([sys.executable, temp_file], 
                                   capture_output=True, text=True, timeout=30)
            
            output = result.stdout
            if result.stderr:
                output += "\nErrors:\n" + result.stderr
            
            return output
        elif language.lower() == "javascript":
            # Create a temporary file
            temp_file = os.path.join(CONFIG["logs_dir"], "temp_code.js")
            with open(temp_file, "w") as f:
                f.write(code)
            
            # Check if Node.js is installed
            try:
                # Execute the code and capture output
                result = subprocess.run(["node", temp_file], 
                                       capture_output=True, text=True, timeout=30)
                
                output = result.stdout
                if result.stderr:
                    output += "\nErrors:\n" + result.stderr
                
                return output
            except FileNotFoundError:
                return "Error: Node.js is not installed or not in PATH"
        elif language.lower() == "shell" or language.lower() == "bash":
            # Create a temporary file
            temp_file = os.path.join(CONFIG["logs_dir"], "temp_code.sh")
            with open(temp_file, "w") as f:
                f.write(code)
            
            # Make the file executable
            os.chmod(temp_file, 0o755)
            
            # Execute the code and capture output
            if sys.platform == "win32":
                result = subprocess.run(["powershell", "-Command", temp_file], 
                                       capture_output=True, text=True, timeout=30)
            else:
                result = subprocess.run(["bash", temp_file], 
                                       capture_output=True, text=True, timeout=30)
            
            output = result.stdout
            if result.stderr:
                output += "\nErrors:\n" + result.stderr
            
            return output
        else:
            return f"Unsupported language: {language}"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (30 seconds limit)"
    except Exception as e:
        return f"Error executing code: {str(e)}"

# Get memory view
def get_memory_view():
    try:
        # In a full implementation, this would retrieve from Chroma DB
        # For now, we'll simulate with a simple file read
        memory_file = os.path.join(CONFIG["memory_dir"], "conversation_history.json")
        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
                history = json.load(f)
            
            # Format the history for display
            formatted_history = ""
            for entry in history:
                formatted_history += f"User: {entry['user']}\n"
                formatted_history += f"AI: {entry['ai']}\n\n"
            
            return formatted_history
        else:
            return "No conversation history found."
    except Exception as e:
        return f"Error retrieving memory: {str(e)}"

# Save to memory
def save_to_memory(user_message, ai_response):
    try:
        memory_file = os.path.join(CONFIG["memory_dir"], "conversation_history.json")
        
        # Load existing history or create new
        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
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
        with open(memory_file, "w") as f:
            json.dump(history, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Error saving to memory: {str(e)}")
        return False

# Execute console command
def execute_command(command):
    if not command.strip():
        return "No command to execute"
    
    try:
        if command.startswith("search:"):
            query = command[7:].strip()
            return f"Search results for '{query}':\nThis feature requires web search integration."
        
        elif command.startswith("browse:"):
            url = command[7:].strip()
            return f"Web content from {url}:\nThis feature requires web browsing integration."
        
        elif command.startswith("file:"):
            parts = command[5:].strip().split(" ", 1)
            if len(parts) < 2:
                return "Invalid file command. Use: file:read|write|list path [content]"
            
            operation = parts[0]
            if operation == "list":
                path = parts[1] if len(parts) > 1 else "."
                try:
                    files = os.listdir(path)
                    return f"Directory listing for {path}:\n" + "\n".join(files)
                except Exception as e:
                    return f"Error listing directory: {str(e)}"
            
            elif operation == "read":
                path = parts[1]
                try:
                    with open(path, "r") as f:
                        content = f.read()
                    return f"File content from {path}:\n{content}"
                except Exception as e:
                    return f"Error reading file: {str(e)}"
            
            elif operation == "write":
                parts = command[5:].strip().split(" ", 2)
                if len(parts) < 3:
                    return "Invalid write command. Use: file:write path content"
                path = parts[1]
                content = parts[2]
                try:
                    with open(path, "w") as f:
                        f.write(content)
                    return f"Successfully wrote to {path}"
                except Exception as e:
                    return f"Error writing file: {str(e)}"
        
        elif command.startswith("model:"):
            model = command[6:].strip()
            if model in ["llama3:8b", "qwen:7b"]:
                return f"Switched to model: {model}"
            else:
                return f"Unknown model: {model}. Available models: llama3:8b, qwen:7b"
        
        else:
            return f"Unknown command: {command}\nAvailable commands: search:query, browse:url, file:operation path [content], model:name"
    
    except Exception as e:
        return f"Error executing command: {str(e)}"

# Custom CSS for the new UI
css = """
:root {
    --primary-color: #4a55af;
    --background-color: #121212;
    --sidebar-color: #1a1a1a;
    --text-color: #ffffff;
    --border-color: #2a2a2a;
    --active-tab: #4a55af;
    --inactive-tab: #2a2a2a;
    --input-bg: #1e1e1e;
    --button-color: #4a55af;
    --button-hover: #5a65bf;
    --status-active: #4CAF50;
    --status-inactive: #F44336;
}

body {
    background-color: var(--background-color);
    color: var(--text-color);
    font-family: 'Inter', sans-serif;
}

.container {
    display: flex;
    height: 100vh;
    max-width: 100%;
    margin: 0;
    padding: 0;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 10px 20px rgba(0,0,0,0.3);
}

.sidebar {
    width: 250px;
    background-color: var(--sidebar-color);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    padding: 20px 0;
}

.sidebar-header {
    padding: 0 20px;
    margin-bottom: 30px;
    font-size: 24px;
    font-weight: bold;
    color: var(--text-color);
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 20px;
}

.sidebar-menu {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.menu-item {
    display: flex;
    align-items: center;
    padding: 12px 20px;
    cursor: pointer;
    border-radius: 8px;
    margin: 0 10px;
    transition: background-color 0.2s;
}

.menu-item:hover {
    background-color: rgba(255,255,255,0.1);
}

.menu-item.active {
    background-color: var(--active-tab);
}

.menu-item-icon {
    margin-right: 12px;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    background-color: var(--background-color);
}

.chat-container {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.message-container {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.message {
    max-width: 80%;
    padding: 12px 16px;
    border-radius: 18px;
    line-height: 1.5;
}

.user-message {
    background-color: var(--primary-color);
    color: white;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
}

.bot-message {
    background-color: var(--sidebar-color);
    color: var(--text-color);
    align-self: flex-start;
    border-bottom-left-radius: 4px;
}

.input-container {
    padding: 20px;
    border-top: 1px solid var(--border-color);
    display: flex;
    gap: 10px;
}

.message-input {
    flex: 1;
    padding: 12px 16px;
    border-radius: 24px;
    border: 1px solid var(--border-color);
    background-color: var(--input-bg);
    color: var(--text-color);
    font-size: 14px;
    resize: none;
}

.send-button {
    background-color: var(--button-color);
    color: white;
    border: none;
    border-radius: 24px;
    padding: 0 20px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
}

.send-button:hover {
    background-color: var(--button-hover);
}

.right-panel {
    width: 350px;
    background-color: var(--sidebar-color);
    border-left: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
}

.agent-status {
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
}

.status-header {
    font-size: 18px;
    font-weight: 500;
    margin-bottom: 15px;
}

.status-indicator {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}

.status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 10px;
}

.status-dot.active {
    background-color: var(--status-active);
}

.status-dot.inactive {
    background-color: var(--status-inactive);
}

.status-text {
    font-weight: 500;
}

.status-details {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 15px;
}

.status-item {
    background-color: var(--input-bg);
    padding: 10px;
    border-radius: 8px;
}

.status-label {
    font-size: 12px;
    color: #888;
    margin-bottom: 5px;
}

.status-value {
    font-weight: 500;
}

.tabs {
    display: flex;
    border-bottom: 1px solid var(--border-color);
}

.tab {
    flex: 1;
    text-align: center;
    padding: 15px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.tab.active {
    border-bottom: 2px solid var(--active-tab);
    color: var(--active-tab);
}

.tab-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.code-area, .memory-area {
    background-color: var(--input-bg);
    border-radius: 8px;
    padding: 15px;
    height: 100%;
    overflow-y: auto;
    font-family: monospace;
    white-space: pre-wrap;
}

.command-input {
    display: flex;
    padding: 10px;
    border-top: 1px solid var(--border-color);
}

.command-prefix {
    padding: 8px 10px;
    color: var(--primary-color);
    font-weight: bold;
}

.command-field {
    flex: 1;
    background-color: transparent;
    border: none;
    color: var(--text-color);
    padding: 8px 0;
    font-family: monospace;
}

.command-field:focus {
    outline: none;
}

.command-button {
    background-color: transparent;
    border: none;
    color: var(--primary-color);
    cursor: pointer;
    padding: 0 10px;
    font-size: 18px;
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--background-color);
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #555;
}

/* Gradio overrides */
.dark .gr-button-primary {
    background-color: var(--button-color) !important;
}

.dark .gr-button-primary:hover {
    background-color: var(--button-hover) !important;
}

.dark .gr-input, .dark .gr-textarea {
    background-color: var(--input-bg) !important;
    border-color: var(--border-color) !important;
}

.dark .gr-panel {
    background-color: var(--sidebar-color) !important;
    border-color: var(--border-color) !important;
}

.dark .gr-box {
    background-color: var(--background-color) !important;
    border-color: var(--border-color) !important;
}

/* Custom layout */
#custom-container {
    display: flex;
    height: 100vh;
    width: 100%;
    max-width: 100%;
    margin: 0;
    padding: 0;
}

#sidebar {
    width: 250px;
    background-color: var(--sidebar-color);
    border-right: 1px solid var(--border-color);
}

#main-content {
    flex: 1;
    background-color: var(--background-color);
}

#right-panel {
    width: 350px;
    background-color: var(--sidebar-color);
    border-left: 1px solid var(--border-color);
}
"""

# Initialize the system
def initialize_system():
    # Start Ollama if not running
    if not start_ollama():
        return "Failed to start Ollama. Please start it manually."
    
    # Check for required models
    try:
        response = requests.get(f"{CONFIG['ollama_url']}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            
            missing_models = []
            for model in [CONFIG["default_model"], CONFIG["lightweight_model"]]:
                if model not in model_names:
                    missing_models.append(model)
            
            if missing_models:
                logger.warning(f"Missing models: {missing_models}")
                logger.info("Models will need to be pulled when running TORIS AI")
    except Exception as e:
        logger.error(f"Error checking models: {str(e)}")
    
    # Check SuperAGI status
    if check_superagi_status():
        logger.info("SuperAGI is available")
    else:
        logger.warning("SuperAGI is not available. Some features may be limited.")
    
    return "System initialized successfully"

# Create the Gradio interface with custom HTML/CSS
with gr.Blocks(css=css, theme=gr.themes.Soft(primary_hue="indigo", neutral_hue="zinc")) as demo:
    # Initialize state variables
    agent_type_state = gr.State("General")
    agent_status_state = gr.State("ACTIVE")
    mode_state = gr.State("General")
    steps_state = gr.State("0")
    
    # Create the layout
    with gr.Row(elem_id="custom-container"):
        # Sidebar
        with gr.Column(elem_id="sidebar", scale=1):
            gr.Markdown("# TORISAI", elem_id="sidebar-header")
            
            with gr.Group(elem_id="sidebar-menu"):
                chat_btn = gr.Button("💬 Chat", elem_id="chat-menu-item", variant="primary")
                memory_btn = gr.Button("🧠 Memory", elem_id="memory-menu-item")
                code_btn = gr.Button("📝 Code", elem_id="code-menu-item")
                console_btn = gr.Button("🖥️ Console", elem_id="console-menu-item")
                settings_btn = gr.Button("⚙️ Settings", elem_id="settings-menu-item")
        
        # Main content
        with gr.Column(elem_id="main-content", scale=3):
            chatbot = gr.Chatbot(
                value=[("Hello!", "Hello! How can I assist you today?")],
                elem_id="chatbot",
                height=500,
                show_label=False
            )
            
            with gr.Row(elem_id="input-container"):
                msg = gr.Textbox(
                    placeholder="Enter your message...",
                    elem_id="message-input",
                    show_label=False
                )
                send = gr.Button("Send", elem_id="send-button")
        
        # Right panel
        with gr.Column(elem_id="right-panel", scale=2):
            with gr.Group(elem_id="agent-status"):
                gr.Markdown("## Agent Status")
                
                with gr.Row(elem_id="status-indicator"):
                    status_indicator = gr.Markdown("🟢 **ACTIVE**", elem_id="status-text")
                
                with gr.Row(elem_id="status-details"):
                    with gr.Column(scale=1):
                        gr.Markdown("**Mode**", elem_id="mode-label")
                        mode_display = gr.Markdown("General", elem_id="mode-value")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("**Steps**", elem_id="steps-label")
                        steps_display = gr.Markdown("2", elem_id="steps-value")
            
            with gr.Tabs(elem_id="right-tabs"):
                with gr.TabItem("Memory View", elem_id="memory-tab"):
                    memory_view = gr.Textbox(
                        value=get_memory_view(),
                        elem_id="memory-area",
                        lines=15,
                        max_lines=30,
                        show_label=False,
                        interactive=False
                    )
                    refresh_memory = gr.Button("Refresh Memory")
                
                with gr.TabItem("Code Execution", elem_id="code-tab"):
                    code_input = gr.Code(
                        language="python",
                        elem_id="code-input",
                        lines=10,
                        label="Code"
                    )
                    with gr.Row():
                        language_dropdown = gr.Dropdown(
                            choices=["python", "javascript", "shell"],
                            value="python",
                            label="Language"
                        )
                        run_code = gr.Button("Run Code")
                    code_output = gr.Textbox(
                        elem_id="code-output",
                        lines=10,
                        max_lines=30,
                        label="Output",
                        interactive=False
                    )
            
            with gr.Row(elem_id="command-input"):
                gr.Markdown(">", elem_id="command-prefix")
                command_input = gr.Textbox(
                    placeholder="Enter command...",
                    elem_id="command-field",
                    show_label=False
                )
                run_command = gr.Button("→", elem_id="command-button")
                command_output = gr.Textbox(visible=False)
    
    # Event handlers
    def process_and_save(message, history, agent_type):
        # Process the query
        new_history, status, mode, steps = process_query(message, history, agent_type)
        
        # Save to memory if there's a response
        if new_history and len(new_history) > 0 and new_history[-1][1]:
            save_to_memory(message, new_history[-1][1])
        
        return new_history, status, mode, steps
    
    send.click(
        process_and_save,
        inputs=[msg, chatbot, agent_type_state],
        outputs=[chatbot, agent_status_state, mode_state, steps_state]
    ).then(
        lambda status, mode, steps: (
            f"{'🟢' if status == 'ACTIVE' else '🔴'} **{status}**",
            f"{mode}",
            f"{steps}"
        ),
        inputs=[agent_status_state, mode_state, steps_state],
        outputs=[status_indicator, mode_display, steps_display]
    ).then(
        lambda: "",
        outputs=[msg]
    )
    
    msg.submit(
        process_and_save,
        inputs=[msg, chatbot, agent_type_state],
        outputs=[chatbot, agent_status_state, mode_state, steps_state]
    ).then(
        lambda status, mode, steps: (
            f"{'🟢' if status == 'ACTIVE' else '🔴'} **{status}**",
            f"{mode}",
            f"{steps}"
        ),
        inputs=[agent_status_state, mode_state, steps_state],
        outputs=[status_indicator, mode_display, steps_display]
    ).then(
        lambda: "",
        outputs=[msg]
    )
    
    run_code.click(
        execute_code,
        inputs=[code_input, language_dropdown],
        outputs=[code_output]
    )
    
    run_command.click(
        execute_command,
        inputs=[command_input],
        outputs=[command_output]
    ).then(
        lambda output: gr.update(value=""),
        inputs=[command_output],
        outputs=[command_input]
    )
    
    refresh_memory.click(
        get_memory_view,
        inputs=[],
        outputs=[memory_view]
    )
    
    # Menu button handlers
    chat_btn.click(lambda: [gr.update(variant="primary"), gr.update(variant="secondary"), gr.update(variant="secondary"), gr.update(variant="secondary"), gr.update(variant="secondary")], 
                  outputs=[chat_btn, memory_btn, code_btn, console_btn, settings_btn])
    
    memory_btn.click(lambda: [gr.update(variant="secondary"), gr.update(variant="primary"), gr.update(variant="secondary"), gr.update(variant="secondary"), gr.update(variant="secondary")], 
                    outputs=[chat_btn, memory_btn, code_btn, console_btn, settings_btn])
    
    code_btn.click(lambda: [gr.update(variant="secondary"), gr.update(variant="secondary"), gr.update(variant="primary"), gr.update(variant="secondary"), gr.update(variant="secondary")], 
                  outputs=[chat_btn, memory_btn, code_btn, console_btn, settings_btn])
    
    console_btn.click(lambda: [gr.update(variant="secondary"), gr.update(variant="secondary"), gr.update(variant="secondary"), gr.update(variant="primary"), gr.update(variant="secondary")], 
                     outputs=[chat_btn, memory_btn, code_btn, console_btn, settings_btn])
    
    settings_btn.click(lambda: [gr.update(variant="secondary"), gr.update(variant="secondary"), gr.update(variant="secondary"), gr.update(variant="secondary"), gr.update(variant="primary")], 
                      outputs=[chat_btn, memory_btn, code_btn, console_btn, settings_btn])
    
    # Agent type selector (hidden in settings tab in full implementation)
    agent_selector = gr.Radio(
        ["General", "Planner", "Coder", "Researcher"], 
        label="Agent Type", 
        value="General",
        visible=False
    )
    
    agent_selector.change(
        lambda agent_type: agent_type,
        inputs=[agent_selector],
        outputs=[agent_type_state]
    ).then(
        lambda agent_type: agent_type,
        inputs=[agent_type_state],
        outputs=[mode_display]
    )

# Launch the app
if __name__ == "__main__":
    # Initialize the system
    init_status = initialize_system()
    logger.info(init_status)
    
    # Launch the Gradio interface
    demo.launch()

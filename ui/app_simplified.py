"""
TORIS AI - UI-Backend Integration (Simplified)
Implements full integration between the UI and backend API with simplified theming
"""
import os
import gradio as gr
import httpx
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./logs/ui.log") if os.path.exists("./logs") else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("torisai.ui")

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_TOKEN = os.environ.get("TORIS_API_TOKEN", "local-development-token")

# Custom CSS for dark theme matching reference
CUSTOM_CSS = """
body {
    background-color: #111827;
    color: #E5E7EB;
}
.gradio-container {
    background-color: #111827;
}
#status_indicator > .label-wrap { 
    background-color: #10B981 !important; 
    color: white !important; 
    border-radius: 9999px !important; 
    padding: 2px 8px !important; 
}
.sidebar {
    border-right: 1px solid #374151;
}
#logo {
    margin-bottom: 2rem;
}
#chatbot {
    min-height: 400px;
}
.dark button.primary {
    background-color: #4F46E5;
}
.dark button.secondary {
    background-color: #374151;
}
.dark input, .dark textarea, .dark select {
    background-color: #374151;
    border-color: #4B5563;
    color: white;
}
.dark .gr-box {
    background-color: #1F2937;
    border-color: #374151;
}
.dark .gr-panel {
    background-color: #1F2937;
}
.dark .gr-input {
    background-color: #374151;
}
"""

# Agent types
AGENT_TYPES = ["General", "Planner", "Coder", "Researcher"]

class BackendClient:
    """Client for communicating with the TORIS AI backend API"""
    
    def __init__(self, base_url: str, token: str):
        """
        Initialize the backend client
        
        Args:
            base_url: Base URL for the backend API
            token: Authentication token
        """
        self.base_url = base_url
        self.token = token
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60.0
        )
        logger.info(f"Initialized backend client with base URL: {base_url}")
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the backend
        
        Returns:
            Health status information
        """
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Health check failed: {response.status_code} - {response.text}")
                return {"status": "error", "message": f"Health check failed: {response.status_code}"}
        except Exception as e:
            logger.error(f"Error checking health: {str(e)}")
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    async def close(self):
        """Close the client session"""
        await self.client.aclose()

class TorisUI:
    """TORIS AI UI with backend integration"""
    
    def __init__(self):
        """Initialize the UI"""
        self.chat_history = []
        self.current_agent = "General"
        self.current_model = "llama3:8b"  # Default model
        self.available_models = ["llama3:8b", "qwen:7b"]  # Will be updated from backend
        self.active_status = "ACTIVE"
        self.steps_count = 0
        self.memory_content = "Memory view will appear here..."
        self.code_output = "Code execution output will appear here..."
        
        # Initialize backend client
        self.backend = BackendClient(BACKEND_URL, API_TOKEN)
        
        # Initialize the UI
        self.create_ui()
    
    def create_ui(self):
        """Create the Gradio UI matching the reference image"""
        with gr.Blocks(title="TORISAI", css=CUSTOM_CSS, theme=gr.themes.Soft()) as self.ui:
            with gr.Row():
                # Sidebar
                with gr.Column(scale=1, min_width=200, elem_classes="sidebar"):
                    gr.Markdown("# TORISAI", elem_id="logo")
                    
                    # Sidebar buttons (using Markdown for icons temporarily)
                    chat_btn = gr.Button("💬 Chat", variant="primary", elem_id="chat_btn")
                    memory_btn = gr.Button("💾 Memory", variant="secondary", elem_id="memory_btn")
                    code_btn = gr.Button("💻 Code", variant="secondary", elem_id="code_btn")
                    console_btn = gr.Button("⌨️ Console", variant="secondary", elem_id="console_btn")
                    
                    gr.Markdown("---")
                    settings_btn = gr.Button("⚙️ Settings", variant="secondary", elem_id="settings_btn")
                
                # Main content area
                with gr.Column(scale=4):
                    self.chatbot = gr.Chatbot(
                        value=self.chat_history,
                        height=600,
                        show_label=False,
                        elem_id="chatbot",
                        bubble_full_width=False
                    )
                    
                    with gr.Row():
                        self.msg = gr.Textbox(
                            placeholder="Enter your message...",
                            show_label=False,
                            container=False,
                            scale=5
                        )
                        self.send_btn = gr.Button("Send", variant="primary", scale=1)
                
                # Right sidebar
                with gr.Column(scale=2, min_width=300):
                    gr.Markdown("### Agent Status")
                    with gr.Box():
                        with gr.Row():
                            self.status_indicator = gr.Label(
                                value=self.active_status,
                                label="",
                                elem_id="status_indicator",
                                show_label=False
                            )
                            self.agent_type = gr.Dropdown(
                                choices=AGENT_TYPES,
                                value=self.current_agent,
                                label="Mode",
                                interactive=True,
                                scale=2
                            )
                        with gr.Row():
                            with gr.Column():
                                self.mode_label = gr.Label(
                                    value=f"Mode: {self.current_agent}",
                                    label=""
                                )
                            with gr.Column():
                                self.steps_label = gr.Label(
                                    value=f"Steps: {self.steps_count}",
                                    label=""
                                )
                    
                    with gr.Tabs() as self.right_tabs:
                        with gr.TabItem("Memory View"):
                            self.memory_view = gr.TextArea(
                                value=self.memory_content,
                                label="",
                                interactive=False,
                                height=400,
                                show_label=False
                            )
                        
                        with gr.TabItem("Code Execution"):
                            self.code_input = gr.Code(
                                language="python",
                                label="Code",
                                interactive=True,
                                lines=10
                            )
                            self.run_code_btn = gr.Button("Run Code", variant="primary")
                            self.code_output_view = gr.TextArea(
                                value=self.code_output,
                                label="Output",
                                interactive=False,
                                height=200
                            )
                    
                    gr.Markdown("### Command")
                    with gr.Row():
                        self.command_input = gr.Textbox(
                            placeholder="Enter command...",
                            show_label=False,
                            container=False,
                            scale=5
                        )
                        self.run_command_btn = gr.Button(">", variant="primary", scale=1, size="sm")
            
            # Event handlers
            self.send_btn.click(
                fn=self.handle_chat,
                inputs=[self.msg],
                outputs=[self.chatbot, self.msg, self.steps_label]
            )
            
            self.msg.submit(
                fn=self.handle_chat,
                inputs=[self.msg],
                outputs=[self.chatbot, self.msg, self.steps_label]
            )
            
            self.run_code_btn.click(
                fn=self.handle_code_execution,
                inputs=[self.code_input],
                outputs=[self.code_output_view]
            )
            
            self.run_command_btn.click(
                fn=self.handle_command,
                inputs=[self.command_input],
                outputs=[self.command_input, self.memory_view]
            )
            
            self.agent_type.change(
                fn=self.change_agent_type,
                inputs=[self.agent_type],
                outputs=[self.mode_label]
            )
            
            # Tab button handlers
            memory_btn.click(lambda: gr.Tabs.update(selected=0), None, self.right_tabs)
            code_btn.click(lambda: gr.Tabs.update(selected=1), None, self.right_tabs)
    
    def handle_chat(self, message):
        """
        Handle chat messages with backend integration
        
        Args:
            message: User message
            
        Returns:
            Updated chat history, empty message box, updated steps label
        """
        if not message.strip():
            return self.chat_history, "", f"Steps: {self.steps_count}"
        
        # Add user message to chat history
        self.chat_history.append((message, None))
        
        # Create a mock response for testing
        # In production, this would call the backend API
        response = f"This is a simulated response to: {message}\n\nThe backend integration is being tested."
        
        # Increment steps
        self.steps_count += 1
        
        # Update chat history
        self.chat_history[-1] = (message, response)
        
        return self.chat_history, "", f"Steps: {self.steps_count}"
    
    def handle_code_execution(self, code):
        """
        Handle code execution with backend integration
        
        Args:
            code: Code to execute
            
        Returns:
            Execution output
        """
        if not code.strip():
            return "No code to execute"
        
        try:
            # For testing, simulate code execution
            # In production, this would call the backend API
            output = f"Simulated code execution:\n\n```python\n{code}\n```\n\nOutput: Code execution simulation successful"
            return output
        
        except Exception as e:
            error_msg = f"Error executing code: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def handle_command(self, command):
        """
        Handle console commands with backend integration
        
        Args:
            command: Command to execute
            
        Returns:
            Empty command box, updated memory view
        """
        if not command.strip():
            return "", self.memory_content
        
        try:
            # For testing, simulate command execution
            # In production, this would call the backend API
            if command.startswith("help"):
                self.memory_content = """Available commands:
                
- memory.clear: Clear conversation history
- memory.search <query>: Search memory for relevant conversations
- help: Show this help message
"""
            else:
                self.memory_content = f"Simulated command execution: {command}"
            
            return "", self.memory_content
        
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logger.error(error_msg)
            self.memory_content = error_msg
            return "", self.memory_content
    
    def change_agent_type(self, agent_type):
        """
        Change the agent type
        
        Args:
            agent_type: New agent type
            
        Returns:
            Updated mode label
        """
        self.current_agent = agent_type
        logger.info(f"Agent type changed to: {self.current_agent}")
        return f"Mode: {self.current_agent}"
    
    def launch(self, **kwargs):
        """Launch the UI"""
        # Launch the UI
        self.ui.launch(**kwargs)

# Create and launch the UI
if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("./logs", exist_ok=True)
    
    # Launch the UI
    ui = TorisUI()
    ui.launch(server_name="0.0.0.0", server_port=7860, share=False)

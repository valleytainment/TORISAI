"""
TORIS AI - UI Application
Implements secure Gradio interface with backend integration
"""
import os
import gradio as gr
import httpx
import asyncio
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_TOKEN = os.environ.get("TORIS_API_TOKEN", "local-development-token")

# Theme configuration
THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="gray",
    radius_size=gr.themes.sizes.radius_sm,
    text_size=gr.themes.sizes.text_md,
).set(
    body_background_fill="rgb(17, 24, 39)",
    body_background_fill_dark="rgb(17, 24, 39)",
    body_text_color="white",
    body_text_color_dark="white",
    button_primary_background_fill="rgb(79, 70, 229)",
    button_primary_background_fill_hover="rgb(99, 102, 241)",
    block_background_fill="rgb(31, 41, 55)",
    block_background_fill_dark="rgb(31, 41, 55)",
    block_label_background_fill="rgb(55, 65, 81)",
    block_label_background_fill_dark="rgb(55, 65, 81)",
    block_label_text_color="white",
    block_label_text_color_dark="white",
    input_background_fill="rgb(55, 65, 81)",
    input_background_fill_dark="rgb(55, 65, 81)",
    input_border_color="rgb(75, 85, 99)",
    input_border_color_dark="rgb(75, 85, 99)",
    input_placeholder_color="rgb(156, 163, 175)",
    input_placeholder_color_dark="rgb(156, 163, 175)",
)

# HTTP client
client = httpx.AsyncClient(
    base_url=BACKEND_URL,
    headers={"Authorization": f"Bearer {API_TOKEN}"},
    timeout=60.0
)

# Agent types
AGENT_TYPES = ["General", "Planner", "Coder", "Researcher"]

class TorisUI:
    def __init__(self):
        self.chat_history = []
        self.current_agent = "General"
        self.current_model = "llama3:8b"
        self.available_models = ["llama3:8b", "qwen:7b"]
        self.active_status = "ACTIVE"
        self.steps_count = 0
        self.memory_content = ""
        self.code_output = ""
        
        # Initialize the UI
        self.create_ui()
    
    def create_ui(self):
        """Create the Gradio UI"""
        with gr.Blocks(theme=THEME, title="TORISAI") as self.ui:
            with gr.Row():
                # Sidebar
                with gr.Column(scale=1, min_width=250):
                    gr.Markdown("# TORISAI")
                    
                    with gr.Row():
                        with gr.Column(scale=1, min_width=50):
                            gr.Image(value="icon.png", show_label=False, height=50, width=50)
                        with gr.Column(scale=4):
                            chat_btn = gr.Button("Chat", variant="primary")
                    
                    with gr.Row():
                        with gr.Column(scale=1, min_width=50):
                            gr.Image(value="memory_icon.png", show_label=False, height=50, width=50)
                        with gr.Column(scale=4):
                            memory_btn = gr.Button("Memory", variant="secondary")
                    
                    with gr.Row():
                        with gr.Column(scale=1, min_width=50):
                            gr.Image(value="code_icon.png", show_label=False, height=50, width=50)
                        with gr.Column(scale=4):
                            code_btn = gr.Button("Code", variant="secondary")
                    
                    with gr.Row():
                        with gr.Column(scale=1, min_width=50):
                            gr.Image(value="console_icon.png", show_label=False, height=50, width=50)
                        with gr.Column(scale=4):
                            console_btn = gr.Button("Console", variant="secondary")
                    
                    gr.Markdown("---")
                    
                    with gr.Row():
                        with gr.Column(scale=1, min_width=50):
                            gr.Image(value="settings_icon.png", show_label=False, height=50, width=50)
                        with gr.Column(scale=4):
                            settings_btn = gr.Button("Settings", variant="secondary")
                
                # Main content
                with gr.Column(scale=4):
                    # Chat interface
                    self.chatbot = gr.Chatbot(
                        value=self.chat_history,
                        height=500,
                        show_label=False,
                        elem_id="chatbot"
                    )
                    
                    with gr.Row():
                        self.msg = gr.Textbox(
                            placeholder="Enter your message...",
                            show_label=False,
                            container=False
                        )
                        self.send_btn = gr.Button("Send", variant="primary")
                
                # Right sidebar
                with gr.Column(scale=2):
                    gr.Markdown("## Agent Status")
                    
                    with gr.Box():
                        with gr.Row():
                            with gr.Column(scale=1):
                                self.status_indicator = gr.Label(
                                    value=self.active_status,
                                    label="",
                                    elem_id="status_indicator"
                                )
                            with gr.Column(scale=3):
                                self.agent_type = gr.Dropdown(
                                    choices=AGENT_TYPES,
                                    value=self.current_agent,
                                    label="Mode",
                                    interactive=True
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
                    
                    with gr.Tabs() as tabs:
                        with gr.TabItem("Memory View"):
                            self.memory_view = gr.TextArea(
                                value=self.memory_content,
                                label="",
                                interactive=False,
                                height=300
                            )
                        
                        with gr.TabItem("Code Execution"):
                            self.code_input = gr.Code(
                                language="python",
                                label="Code",
                                interactive=True
                            )
                            self.run_code_btn = gr.Button("Run", variant="primary")
                            self.code_output_view = gr.TextArea(
                                value=self.code_output,
                                label="Output",
                                interactive=False,
                                height=200
                            )
                    
                    with gr.Row():
                        self.command_input = gr.Textbox(
                            placeholder="Command...",
                            label="Command:",
                            interactive=True
                        )
                        self.run_command_btn = gr.Button(">", variant="primary", size="sm")
            
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
            memory_btn.click(lambda: gr.Tabs.update(selected=0), None, tabs)
            code_btn.click(lambda: gr.Tabs.update(selected=1), None, tabs)
    
    async def handle_chat(self, message):
        """Handle chat messages"""
        if not message.strip():
            return self.chat_history, "", f"Steps: {self.steps_count}"
        
        # Add user message to chat history
        self.chat_history.append((message, None))
        
        try:
            # Increment steps
            self.steps_count += 1
            
            # Call backend API
            response = await client.post(
                "/chat",
                json={
                    "message": message,
                    "agent_type": self.current_agent,
                    "model": self.current_model
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data["response"]
                
                # Update chat history
                self.chat_history[-1] = (message, ai_response)
                
                # Update memory view
                await self.update_memory_view()
                
                return self.chat_history, "", f"Steps: {self.steps_count}"
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                self.chat_history[-1] = (message, error_msg)
                return self.chat_history, "", f"Steps: {self.steps_count}"
        
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.chat_history[-1] = (message, error_msg)
            return self.chat_history, "", f"Steps: {self.steps_count}"
    
    async def handle_code_execution(self, code):
        """Handle code execution"""
        if not code.strip():
            return "No code to execute"
        
        try:
            # Call backend API
            response = await client.post(
                "/execute-code",
                json={
                    "code": code,
                    "language": "python"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["output"]
            else:
                return f"Error: {response.status_code} - {response.text}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def handle_command(self, command):
        """Handle console commands"""
        if not command.strip():
            return "", self.memory_content
        
        if command.startswith("memory.clear"):
            try:
                response = await client.delete("/memory/clear")
                if response.status_code == 200:
                    self.memory_content = "Memory cleared"
                    return "", self.memory_content
                else:
                    return "", f"Error: {response.status_code} - {response.text}"
            except Exception as e:
                return "", f"Error: {str(e)}"
        
        elif command.startswith("memory.search"):
            try:
                query = command.replace("memory.search", "").strip()
                if not query:
                    return "", "Usage: memory.search <query>"
                
                response = await client.post(
                    "/memory/search",
                    json={
                        "query": query,
                        "limit": 5
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data["results"]
                    
                    if not results:
                        return "", "No results found"
                    
                    formatted_results = "Search results:\n\n"
                    for i, result in enumerate(results):
                        formatted_results += f"{i+1}. User: {result['user']}\n"
                        formatted_results += f"   AI: {result['ai']}\n\n"
                    
                    self.memory_content = formatted_results
                    return "", self.memory_content
                else:
                    return "", f"Error: {response.status_code} - {response.text}"
            except Exception as e:
                return "", f"Error: {str(e)}"
        
        elif command.startswith("help"):
            help_text = """Available commands:
            
- memory.clear: Clear conversation history
- memory.search <query>: Search memory for relevant conversations
- help: Show this help message
"""
            self.memory_content = help_text
            return "", self.memory_content
        
        else:
            return "", f"Unknown command: {command}\nType 'help' for available commands"
    
    def change_agent_type(self, agent_type):
        """Change the agent type"""
        self.current_agent = agent_type
        return f"Mode: {self.current_agent}"
    
    async def update_memory_view(self):
        """Update the memory view with recent conversations"""
        try:
            # Get recent conversation history
            history = self.chat_history[-5:] if len(self.chat_history) > 5 else self.chat_history
            
            formatted_history = "Recent conversation:\n\n"
            for user_msg, ai_msg in history:
                formatted_history += f"User: {user_msg}\n"
                if ai_msg:
                    formatted_history += f"AI: {ai_msg[:100]}...\n" if len(ai_msg) > 100 else f"AI: {ai_msg}\n"
                formatted_history += "\n"
            
            self.memory_content = formatted_history
            return self.memory_content
        except Exception as e:
            return f"Error updating memory view: {str(e)}"
    
    def launch(self, **kwargs):
        """Launch the UI"""
        return self.ui.launch(**kwargs)

# Create and launch the UI
if __name__ == "__main__":
    ui = TorisUI()
    ui.launch(server_name="0.0.0.0", server_port=7860, share=False)

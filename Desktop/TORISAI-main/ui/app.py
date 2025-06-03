"""
TORIS AI - UI Application (Refactored)
Implements secure Gradio interface matching reference design
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

# Theme configuration (Dark theme matching reference)
THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="gray",
    radius_size=gr.themes.sizes.radius_sm,
    text_size=gr.themes.sizes.text_md,
).set(
    body_background_fill="#111827",  # Dark background
    body_background_fill_dark="#111827",
    body_text_color="#E5E7EB",  # Light text
    body_text_color_dark="#E5E7EB",
    button_primary_background_fill="#4F46E5",  # Indigo button
    button_primary_background_fill_hover="#6366F1",
    button_primary_text_color="white",
    button_secondary_background_fill="#374151",  # Gray button
    button_secondary_background_fill_hover="#4B5563",
    button_secondary_text_color="white",
    block_background_fill="#1F2937",  # Darker block background
    block_background_fill_dark="#1F2937",
    block_label_background_fill="#374151",
    block_label_background_fill_dark="#374151",
    block_label_text_color="white",
    block_label_text_color_dark="white",
    input_background_fill="#374151",
    input_background_fill_dark="#374151",
    input_border_color="#4B5563",
    input_border_color_dark="#4B5563",
    input_placeholder_color="#9CA3AF",
    input_placeholder_color_dark="#9CA3AF",
    input_text_color="white",
    input_text_color_dark="white",
    chatbot_code_background_color="#374151",
    chatbot_code_background_color_dark="#374151",
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
        self.current_model = "llama3:8b"  # Default model
        self.available_models = ["llama3:8b", "qwen:7b"] # Placeholder, fetch from backend later
        self.active_status = "ACTIVE"
        self.steps_count = 0
        self.memory_content = "Memory view will appear here..."
        self.code_output = "Code execution output will appear here..."
        
        # Initialize the UI
        self.create_ui()
    
    def create_ui(self):
        """Create the Gradio UI matching the reference image"""
        with gr.Blocks(theme=THEME, title="TORISAI", css="#status_indicator > .label-wrap { background-color: #10B981 !important; color: white !important; border-radius: 9999px !important; padding: 2px 8px !important; }") as self.ui:
            with gr.Row():
                # Sidebar
                with gr.Column(scale=1, min_width=200, elem_classes="sidebar"):
                    gr.Markdown("## TORISAI", elem_id="logo")
                    
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
                            self.steps_label = gr.Label(
                                value=f"Steps: {self.steps_count}",
                                label="",
                                show_label=False
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
                outputs=[] # Update internal state only for now
            )
            
            # Tab button handlers (placeholder - need actual tab switching logic)
            memory_btn.click(lambda: gr.Tabs.update(selected=0), None, self.right_tabs)
            code_btn.click(lambda: gr.Tabs.update(selected=1), None, self.right_tabs)
    
    async def handle_chat(self, message):
        """Handle chat messages (placeholder for backend integration)"""
        if not message.strip():
            return self.chat_history, "", f"Steps: {self.steps_count}"
        
        # Add user message to chat history
        self.chat_history.append((message, None))
        yield self.chat_history, "", f"Steps: {self.steps_count}" # Update UI immediately
        
        # Simulate backend call
        await asyncio.sleep(1) 
        ai_response = f"Received: 
{message}
 (Backend integration pending)"
        self.steps_count += 1
        
        # Update chat history
        self.chat_history[-1] = (message, ai_response)
        
        # Update memory view (placeholder)
        await self.update_memory_view()
        
        yield self.chat_history, "", f"Steps: {self.steps_count}"
    
    async def handle_code_execution(self, code):
        """Handle code execution (placeholder for backend integration)"""
        if not code.strip():
            return "No code to execute"
        
        # Simulate backend call
        await asyncio.sleep(0.5)
        output = f"Executing code:
{code}

(Backend integration pending)"
        return output
    
    async def handle_command(self, command):
        """Handle console commands (placeholder for backend integration)"""
        if not command.strip():
            return "", self.memory_content
        
        # Simulate backend call
        await asyncio.sleep(0.5)
        output = f"Command 
`{command}`
 received. (Backend integration pending)"
        self.memory_content = output
        return "", self.memory_content
    
    def change_agent_type(self, agent_type):
        """Change the agent type (updates internal state)"""
        self.current_agent = agent_type
        print(f"Agent type changed to: {self.current_agent}") # Log change
        # No UI output needed here, status label might be updated elsewhere
    
    async def update_memory_view(self):
        """Update the memory view (placeholder)"""
        history_text = "Recent conversation:\n\n"
        for user_msg, ai_msg in self.chat_history[-5:]:
            history_text += f"User: {user_msg}\n"
            if ai_msg:
                history_text += f"AI: {ai_msg[:100]}{'...' if len(ai_msg) > 100 else ''}\n"
            history_text += "\n"
        self.memory_content = history_text
        # In a real implementation, this would likely update the Gradio component directly
        # For now, it just updates the internal state
    
    def launch(self, **kwargs):
        """Launch the UI"""
        return self.ui.launch(**kwargs)

# Create and launch the UI
if __name__ == "__main__":
    # Ensure necessary icon files exist (create dummy files if needed)
    icons = ["icon.png", "memory_icon.png", "code_icon.png", "console_icon.png", "settings_icon.png"]
    for icon in icons:
        if not os.path.exists(icon):
            # Create a dummy 1x1 pixel PNG
            from PIL import Image
            img = Image.new("RGB", (1, 1))
            img.save(icon)
            print(f"Created dummy icon: {icon}")
            
    ui = TorisUI()
    ui.launch(server_name="0.0.0.0", server_port=7860, share=False)

# TORIS AI - Windows Quick Start Guide

This guide provides a streamlined approach to get TORIS AI running on Windows quickly, addressing the specific issues you've encountered.

## Fix for "No module named 'torisai.ui'" Error

### Step 1: Create the Missing UI Module

1. Open Command Prompt as Administrator
2. Navigate to your TORIS AI directory:
```
cd C:\Users\Ahazia\Downloads\TORISAI-main (2)\TORISAI-main
```

3. Create a simple UI module with the necessary files:
```
mkdir -p torisai\ui
echo # UI package for TORIS AI > torisai\ui\__init__.py
```

4. Create a launch_ui function in the __init__.py file:
```
echo from torisai.ui.app import create_ui >> torisai\ui\__init__.py
echo import os >> torisai\ui\__init__.py
echo. >> torisai\ui\__init__.py
echo def launch_ui(): >> torisai\ui\__init__.py
echo     from torisai.main import TorisAI >> torisai\ui\__init__.py
echo     toris = TorisAI() >> torisai\ui\__init__.py
echo     ui = create_ui(toris) >> torisai\ui\__init__.py
echo     ui.launch(server_name="0.0.0.0", server_port=int(os.environ.get("GRADIO_SERVER_PORT", 7860)), share=False) >> torisai\ui\__init__.py
```

5. Create a minimal app.py file:
```
echo import gradio as gr > torisai\ui\app.py
echo. >> torisai\ui\app.py
echo def create_ui(toris_instance): >> torisai\ui\app.py
echo     with gr.Blocks(theme=gr.themes.Soft()) as ui: >> torisai\ui\app.py
echo         gr.Markdown("# TORIS AI") >> torisai\ui\app.py
echo         with gr.Tab("Chat"): >> torisai\ui\app.py
echo             chatbot = gr.Chatbot() >> torisai\ui\app.py
echo             msg = gr.Textbox(label="Message") >> torisai\ui\app.py
echo             send = gr.Button("Send") >> torisai\ui\app.py
echo         with gr.Tab("Documents"): >> torisai\ui\app.py
echo             gr.Markdown("Document tools will appear here") >> torisai\ui\app.py
echo         with gr.Tab("Web"): >> torisai\ui\app.py
echo             gr.Markdown("Web tools will appear here") >> torisai\ui\app.py
echo     return ui >> torisai\ui\app.py
```

### Step 2: Fix Dependencies

Ensure all required packages are installed:
```
pip install gradio httpx pydantic PyPDF2 chromadb
```

### Step 3: Run TORIS AI with a Different Port

```
set GRADIO_SERVER_PORT=7861
python run_toris.py
```

## Troubleshooting Common Issues

### If you see "No module named 'torisai'" error:

This means Python can't find the torisai package at all. Fix with:
```
set PYTHONPATH=%CD%
python run_toris.py
```

### If Ollama isn't connecting:

Make sure Ollama is running in the background:
```
C:\Users\Ahazia\AppData\Local\Programs\Ollama\ollama.EXE serve
```

### If you get port conflicts:

Try different ports until you find one that works:
```
set GRADIO_SERVER_PORT=7862
python run_toris.py
```

## Next Steps

Once TORIS AI is running:
1. Access the UI at http://localhost:7861 (or whatever port you specified)
2. Test the chat functionality
3. Try loading a document
4. Explore the web navigation features

If you continue to experience issues, please refer to the more detailed troubleshooting guides provided earlier.

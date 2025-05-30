# TORIS AI - Windows Installation Guide

This guide provides detailed instructions for installing and running TORIS AI on Windows systems, including troubleshooting common issues.

## Prerequisites

- Windows 10 or 11 (64-bit)
- Python 3.9+ installed and added to PATH
- Git (optional, for cloning the repository)
- At least 8GB RAM recommended
- 2GB free disk space

## Step 1: Install Ollama

Ollama is required for the LLM functionality in TORIS AI.

1. Download Ollama from [https://ollama.ai/download](https://ollama.ai/download)
2. Run the installer and follow the prompts
3. After installation, Ollama will start automatically

## Step 2: Download TORIS AI

### Option A: Using Git
```
git clone https://github.com/valleytainment/TORIS-A.I.git
cd TORIS-A.I
```

### Option B: Download ZIP
1. Go to [https://github.com/valleytainment/TORIS-A.I](https://github.com/valleytainment/TORIS-A.I)
2. Click the "Code" button and select "Download ZIP"
3. Extract the ZIP file to a location of your choice

## Step 3: Set Up Python Environment

It's recommended to use a virtual environment:

```
cd TORIS-A.I
python -m venv venv
venv\Scripts\activate
```

## Step 4: Install Dependencies

Install all required packages:

```
pip install -r requirements.txt
```

If you encounter memory issues during installation, try installing packages in smaller batches:

```
pip install gradio httpx pydantic
pip install PyPDF2 chromadb
pip install langchain
```

## Step 5: Run TORIS AI

With Ollama running in the background:

```
python run_toris.py
```

The UI should be accessible at http://localhost:7860 (or the port specified in your environment variables).

## Troubleshooting Common Issues

### ModuleNotFoundError: No module named 'chromadb'

This error occurs when the ChromaDB package is missing:

```
pip install chromadb
```

### ModuleNotFoundError for other packages

Install the specific missing package:

```
pip install [package_name]
```

### Port Conflict Errors

If you see an error about port 7860 being in use:

1. Set a different port using an environment variable:
   ```
   set GRADIO_SERVER_PORT=7861
   python run_toris.py
   ```

2. Or modify the port in code:
   - Open `torisai/main.py`
   - Find the line with `ui.launch(server_name="0.0.0.0", server_port=7860, share=False)`
   - Change 7860 to another port (e.g., 7861)

### Ollama Connection Errors

If TORIS AI can't connect to Ollama:

1. Ensure Ollama is running:
   ```
   ollama serve
   ```

2. Check if Ollama is accessible:
   ```
   curl http://localhost:11434/api/tags
   ```

3. If using WSL2, ensure proper network configuration between Windows and WSL2

### Windows-Specific Path Issues

Windows uses backslashes (`\`) in paths, while the code might expect forward slashes (`/`). If you encounter path-related errors:

1. Modify any hardcoded paths in the code to use `os.path.join()` instead of string concatenation
2. Or replace forward slashes with backslashes in configuration files

## Performance Optimization

For better performance on Windows:

1. Use a dedicated GPU if available
2. Reduce model size in settings if performance is slow
3. Close other resource-intensive applications
4. Increase the page file size if RAM is limited

## Getting Help

If you encounter issues not covered in this guide:

1. Check the GitHub repository issues section
2. Look for error messages in the console output
3. Create a new issue on GitHub with detailed information about your problem

## Next Steps

After successful installation:

1. Explore the different tabs and features
2. Try loading a PDF document
3. Test the web navigation capabilities
4. Experiment with different agent modes

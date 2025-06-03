# TORIS AI - Windows Module Structure Troubleshooting Guide

This guide addresses the `ModuleNotFoundError: No module named 'torisai.ui'` error that can occur when running TORIS AI on Windows systems.

## Common Causes and Solutions

### 1. Incorrect Directory Structure

The most common cause of this error is running the script from the wrong directory or having an incomplete extraction of the ZIP file.

**Solution:**
- Ensure you have the complete directory structure:
```
TORISAI/
├── run_toris.py
├── requirements.txt
├── torisai/
│   ├── __init__.py
│   ├── main.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── ...
│   └── ...
└── ...
```

- Verify that all `__init__.py` files exist in each directory and subdirectory
- Make sure you're running the script from the root directory of the project

### 2. Running from the Wrong Location

**Solution:**
- Open a command prompt
- Navigate to the root directory of the TORIS AI project
- Run the script from there:
```
cd C:\path\to\TORISAI-main
python run_toris.py
```

### 3. Python Path Issues

**Solution:**
- Create a simple verification script to check your Python path:

```python
# save as check_modules.py in the TORIS AI root directory
import sys
import os

# Print the current directory
print(f"Current directory: {os.getcwd()}")

# Print the Python path
print(f"Python path: {sys.path}")

# Check if torisai is importable
try:
    import torisai
    print(f"torisai module found at: {torisai.__file__}")
    
    # Try to import the UI module
    try:
        import torisai.ui
        print(f"torisai.ui module found at: {torisai.ui.__file__}")
    except ImportError as e:
        print(f"Error importing torisai.ui: {e}")
        
except ImportError as e:
    print(f"Error importing torisai: {e}")
```

Run this script from the TORIS AI root directory:
```
python check_modules.py
```

### 4. Missing or Incomplete Installation

**Solution:**
- Reinstall from a fresh download:
```
git clone https://github.com/valleytainment/TORIS-A.I.git
cd TORIS-A.I
pip install -r requirements.txt
```

- Or download the ZIP file again, extract it completely, and ensure all files are present

### 5. Manual Fix for Missing UI Module

If the UI module is still missing, you can create the necessary files:

1. Create the directory structure if it doesn't exist:
```
mkdir -p torisai\ui
```

2. Create the `__init__.py` file in the UI directory:
```python
# torisai/ui/__init__.py
"""
UI package for TORIS AI
"""

def launch_ui():
    """
    Launch the TORIS AI UI
    This is a placeholder function that will be replaced by the actual UI launch code
    """
    from torisai.ui.app import create_ui
    from torisai.main import TorisAI
    
    toris = TorisAI()
    ui = create_ui(toris)
    ui.launch(server_name="0.0.0.0", server_port=int(os.environ.get("GRADIO_SERVER_PORT", 7860)), share=False)
```

### 6. Verify Python Version Compatibility

TORIS AI requires Python 3.9 or higher. Verify your Python version:

```
python --version
```

If you're using an older version, upgrade to a compatible version.

## Advanced Troubleshooting

### Check for Circular Imports

The error might be caused by circular imports in the codebase. To debug:

1. Add print statements to track the import sequence:
```python
# At the top of run_toris.py
print("Starting run_toris.py")

# Before the problematic import
print("About to import from torisai.ui")
from torisai.ui import launch_ui
print("Successfully imported from torisai.ui")
```

2. Run the script and observe the output to identify where the import fails

### Package Installation Method

Try installing TORIS AI as a package:

```
pip install -e .
```

This will install the package in development mode, making all modules available in the Python path.

## Getting Help

If you continue to experience issues:

1. Create a detailed bug report including:
   - Your Windows version
   - Python version
   - Complete error message
   - Steps you've already tried

2. Submit the bug report to the GitHub repository issues section

# TORIS AI - README.md

# TORIS AI: Your Local AI Agent

TORIS AI is a powerful, cost-free alternative to Manus AI that runs entirely on your local machine. It combines multiple open-source components to provide a comprehensive AI assistant with capabilities for planning, coding, research, and more.

## Features

- **100% Local Operation**: All processing happens on your machine with no cloud costs
- **Multiple Specialized Agents**: Planner, Coder, and Researcher agents for different tasks
- **Code Execution**: Safely run Python, JavaScript, and shell commands
- **Web Search and Browsing**: Find and extract information from the internet
- **Long-term Memory**: Store and retrieve information using vector databases
- **GUI Automation**: Control your desktop applications (optional)
- **User-friendly Interface**: Simple web interface for interacting with the AI

## System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **RAM**: 12GB minimum (optimized for your system)
- **CPU**: Intel Core i5 or equivalent (compatible with your i5-8400)
- **Storage**: 10GB minimum

## Installation

1. Install Python 3.8+ if not already installed
2. Install Ollama from [ollama.ai](https://ollama.ai)
3. Clone this repository:
   ```
   git clone https://github.com/valleytainment/TORISAI.git
   cd TORISAI
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
- **Gradio**: User interface
- **PyAutoGUI**: GUI automation (optional)
- **BeautifulSoup**: Web content extraction
- **Requests**: HTTP client for web interactions

## Customization

- Add new tools by extending the `tools.py` file
- Add new agent types in `agent.py`
- Modify the UI in `app.py`
- Add documents to the `./documents` directory for the AI to learn from

## Troubleshooting

- If Ollama fails to start, try starting it manually before running TORIS AI
- If you encounter memory errors, try using a smaller model like `qwen:7b`
- For better performance, close other memory-intensive applications while using TORIS AI

## License

This project is open-source and available under the MIT License.

## Acknowledgements

- Inspired by the architecture described in the original guide
- GUI automation module inspired by Agent-S framework
- Thanks to all the open-source projects that made this possible

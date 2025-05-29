# TORIS AI - Tools Module

import requests
from bs4 import BeautifulSoup
import subprocess
import sys
import os
import json
import time

class Tools:
    """
    Collection of tools for TORIS AI to interact with external systems.
    Includes web search, web browsing, code execution, and file operations.
    """
    
    def __init__(self, memory_dir="./memory", temp_dir="./temp"):
        """Initialize tools with specified directories"""
        self.memory_dir = memory_dir
        self.temp_dir = temp_dir
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def web_search(self, query):
        """
        Search the web for information
        
        Args:
            query (str): Search query
            
        Returns:
            str: Search results
        """
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
    
    def web_browse(self, url):
        """
        Browse a webpage and extract its content
        
        Args:
            url (str): URL to browse
            
        Returns:
            str: Extracted content
        """
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
            
            # Save a copy of the extracted content
            timestamp = int(time.time())
            content_file = os.path.join(self.memory_dir, f"webpage_{timestamp}.txt")
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n\n")
                f.write(text[:50000])  # Limit to 50000 chars
            
            return text[:10000]  # Return first 10000 chars
        except Exception as e:
            return f"Error browsing webpage: {str(e)}"
    
    def execute_code(self, code, language="python"):
        """
        Execute code and return the result
        
        Args:
            code (str): Code to execute
            language (str): Programming language
            
        Returns:
            str: Execution result
        """
        try:
            if language.lower() == "python":
                # Create a temporary file
                timestamp = int(time.time())
                temp_file = os.path.join(self.temp_dir, f"code_{timestamp}.py")
                with open(temp_file, "w") as f:
                    f.write(code)
                
                # Execute the code and capture output
                result = subprocess.run([sys.executable, temp_file], 
                                       capture_output=True, 
                                       text=True,
                                       timeout=30)  # 30 second timeout for safety
                
                # Return the output or error
                if result.returncode == 0:
                    return result.stdout
                else:
                    return f"Error: {result.stderr}"
            
            elif language.lower() == "javascript":
                # Create a temporary file
                timestamp = int(time.time())
                temp_file = os.path.join(self.temp_dir, f"code_{timestamp}.js")
                with open(temp_file, "w") as f:
                    f.write(code)
                
                # Check if Node.js is available
                try:
                    subprocess.run(["node", "--version"], capture_output=True, check=True)
                    # Execute the code and capture output
                    result = subprocess.run(["node", temp_file], 
                                           capture_output=True, 
                                           text=True,
                                           timeout=30)  # 30 second timeout for safety
                    
                    # Return the output or error
                    if result.returncode == 0:
                        return result.stdout
                    else:
                        return f"Error: {result.stderr}"
                except:
                    return "Node.js is not available. Please install Node.js to execute JavaScript code."
            
            elif language.lower() in ["shell", "bash", "cmd"]:
                # For security reasons, shell execution is limited
                return "Shell execution is disabled for security reasons."
            
            else:
                return f"Language {language} not supported yet"
        except subprocess.TimeoutExpired:
            return "Execution timed out (30 second limit)"
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
    def file_operations(self, operation, path, content=None):
        """
        Perform file operations
        
        Args:
            operation (str): Operation type (list, read, write)
            path (str): File or directory path
            content (str, optional): Content for write operation
            
        Returns:
            str: Operation result
        """
        try:
            # Sanitize path to prevent directory traversal
            # Only allow operations within memory_dir and temp_dir
            abs_path = os.path.abspath(path)
            if not (abs_path.startswith(os.path.abspath(self.memory_dir)) or 
                    abs_path.startswith(os.path.abspath(self.temp_dir))):
                return "Error: Access denied. Operations are restricted to memory and temp directories."
            
            if operation.lower() == "list":
                if os.path.isdir(path):
                    return str(os.listdir(path))
                else:
                    return f"Error: {path} is not a directory"
            
            elif operation.lower() == "read":
                if os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as file:
                        return file.read()
                else:
                    return f"Error: {path} is not a file"
            
            elif operation.lower() == "write":
                if content is None:
                    return "Error: Content required for write operation"
                
                # Ensure directory exists
                dir_path = os.path.dirname(path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                return f"Successfully wrote to {path}"
            
            else:
                return f"Unknown operation: {operation}"
        except Exception as e:
            return f"Error with file operation: {str(e)}"

# Example usage
if __name__ == "__main__":
    tools = Tools()
    print(tools.web_search("Python programming"))

# TORIS AI - Agent Module

import os
import json
import time
from memory_manager import Memory
from tools import Tools

class Agent:
    """
    Agent class for TORIS AI.
    Handles different agent types and their specific behaviors.
    """
    
    def __init__(self, agent_type="planner", model="llama3:8b", memory_dir="./memory"):
        """Initialize agent with specified type and model"""
        self.agent_type = agent_type
        self.model = model
        self.memory = Memory(memory_dir)
        self.tools = Tools(memory_dir)
        
        # System prompts for different agent types
        self.system_prompts = {
            "planner": """You are TORIS AI's Planning Agent. Your role is to help users break down complex tasks into manageable steps.
Focus on:
1. Understanding the user's overall goal
2. Decomposing tasks into logical sequences
3. Identifying dependencies between steps
4. Estimating time and resources needed
5. Creating clear, actionable plans

Always be thorough, methodical, and consider potential obstacles. When appropriate, use tools like web search for research, code execution for calculations, and file operations for documentation.""",
            
            "coder": """You are TORIS AI's Coding Agent. Your role is to help users with programming and development tasks.
Focus on:
1. Writing clean, efficient, and well-documented code
2. Debugging and fixing issues in existing code
3. Explaining technical concepts clearly
4. Following best practices for the language/framework
5. Testing and validating solutions

Always provide complete, working solutions that can be executed directly. Use tools like code execution to test your solutions, web search for documentation, and file operations to save and manage code files.""",
            
            "researcher": """You are TORIS AI's Research Agent. Your role is to help users gather and analyze information.
Focus on:
1. Finding accurate, relevant information from reliable sources
2. Synthesizing data from multiple sources
3. Evaluating the credibility of information
4. Organizing findings in a clear, structured way
5. Identifying gaps in available information

Always cite your sources and provide balanced perspectives. Use tools like web search to find information, web browsing to explore specific pages, and file operations to save and organize research findings."""
        }
    
    def get_system_prompt(self):
        """Get the system prompt for the current agent type"""
        return self.system_prompts.get(self.agent_type.lower(), self.system_prompts["planner"])
    
    def process_query(self, query, ollama_url="http://localhost:11434"):
        """
        Process a user query and generate a response
        
        Args:
            query (str): User query
            ollama_url (str): URL for Ollama API
            
        Returns:
            str: Agent response
        """
        import requests
        
        # Get recent conversation history for context
        context = self.memory.get_recent_history(3)
        
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
        try:
            url = f"{ollama_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "system": self.get_system_prompt(),
                "temperature": 0.7,
                "stream": False
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                llm_response = response.json().get("response", "")
            else:
                return f"Error: {response.status_code} - {response.text}"
            
            # Process tool calls in the response
            if "TOOL:" in llm_response:
                # Extract tool calls
                tool_calls = []
                lines = llm_response.split("\n")
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
                            result = self.tools.web_search(query)
                            tool_results.append(f"Web Search Result for '{query}':\n{result}")
                        
                        elif "web_browse(" in call:
                            url = call.split("web_browse(")[1].split(")")[0].strip('"\'')
                            result = self.tools.web_browse(url)
                            tool_results.append(f"Web Browse Result for {url}:\n{result}")
                        
                        elif "execute_code(" in call:
                            # Simple parsing for demonstration
                            parts = call.split("execute_code(")[1].split(")")[0].split(",")
                            if len(parts) > 1:
                                code = parts[0].strip('"\'')
                                language = parts[1].strip('"\'')
                                result = self.tools.execute_code(code, language)
                            else:
                                code = parts[0].strip('"\'')
                                result = self.tools.execute_code(code)
                            tool_results.append(f"Code Execution Result:\n{result}")
                        
                        elif "file_operations(" in call:
                            # Simple parsing for demonstration
                            parts = call.split("file_operations(")[1].split(")")[0].split(",")
                            operation = parts[0].strip('"\'')
                            path = parts[1].strip('"\'')
                            content = parts[2].strip('"\'') if len(parts) > 2 else None
                            result = self.tools.file_operations(operation, path, content)
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
                
                # Get final response
                payload["prompt"] = final_prompt
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    final_response = response.json().get("response", "")
                else:
                    final_response = f"Error: {response.status_code} - {response.text}"
                
                # Add to memory
                self.memory.add_interaction(query, final_response, self.agent_type)
                
                return final_response
            
            # If no tool calls, just return the response
            self.memory.add_interaction(query, llm_response, self.agent_type)
            return llm_response
            
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def change_agent_type(self, new_type):
        """Change the agent type"""
        if new_type.lower() in ["planner", "coder", "researcher"]:
            self.agent_type = new_type.lower()
            return f"Agent type changed to {new_type}"
        else:
            return f"Invalid agent type: {new_type}. Available types: planner, coder, researcher"
    
    def change_model(self, new_model):
        """Change the model"""
        self.model = new_model
        return f"Model changed to {new_model}"

# Example usage
if __name__ == "__main__":
    agent = Agent()
    response = agent.process_query("What is the capital of France?")
    print(response)

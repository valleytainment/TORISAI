# TORIS AI - Memory Management Module

import os
import json
import time
from datetime import datetime

class Memory:
    """
    Memory management for TORIS AI.
    Handles conversation history storage and retrieval.
    """
    
    def __init__(self, memory_dir="./memory"):
        """Initialize memory manager with specified directory"""
        self.memory_dir = memory_dir
        self.conversation_file = os.path.join(memory_dir, "conversation_history.json")
        self.ensure_memory_dir()
        self.ensure_conversation_file()
    
    def ensure_memory_dir(self):
        """Ensure memory directory exists"""
        os.makedirs(self.memory_dir, exist_ok=True)
    
    def ensure_conversation_file(self):
        """Ensure conversation history file exists"""
        if not os.path.exists(self.conversation_file):
            with open(self.conversation_file, 'w') as f:
                json.dump([], f)
    
    def add_interaction(self, user_message, ai_response, agent_type="general"):
        """
        Add a user-AI interaction to memory
        
        Args:
            user_message (str): The user's message
            ai_response (str): The AI's response
            agent_type (str): The type of agent used (planner, coder, researcher, etc.)
        """
        try:
            # Load existing memory
            with open(self.conversation_file, 'r') as f:
                memory = json.load(f)
            
            # Add new interaction
            memory.append({
                "timestamp": time.time(),
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "agent_type": agent_type,
                "user": user_message,
                "ai": ai_response
            })
            
            # Save updated memory
            with open(self.conversation_file, 'w') as f:
                json.dump(memory, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error adding to memory: {str(e)}")
            return False
    
    def get_recent_history(self, limit=5, agent_type=None):
        """
        Get recent conversation history
        
        Args:
            limit (int): Maximum number of interactions to retrieve
            agent_type (str, optional): Filter by agent type
            
        Returns:
            str: Formatted conversation history
        """
        try:
            with open(self.conversation_file, 'r') as f:
                memory = json.load(f)
            
            # Filter by agent type if specified
            if agent_type:
                memory = [m for m in memory if m.get("agent_type") == agent_type]
            
            # Get the most recent interactions
            recent = memory[-limit:] if len(memory) > limit else memory
            
            # Format for context
            context = ""
            for item in recent:
                context += f"User: {item['user']}\nAI: {item['ai']}\n\n"
            
            return context
        except Exception as e:
            print(f"Error retrieving memory: {str(e)}")
            return ""
    
    def search_memory(self, query, limit=5):
        """
        Simple keyword search in memory
        
        Args:
            query (str): Search terms
            limit (int): Maximum number of results
            
        Returns:
            list: Matching interactions
        """
        try:
            with open(self.conversation_file, 'r') as f:
                memory = json.load(f)
            
            # Simple keyword search
            results = []
            query_terms = query.lower().split()
            
            for item in memory:
                user_text = item['user'].lower()
                ai_text = item['ai'].lower()
                
                # Check if any query term is in the texts
                if any(term in user_text or term in ai_text for term in query_terms):
                    results.append(item)
            
            # Return limited results, most recent first
            return results[-limit:] if len(results) > limit else results
            
        except Exception as e:
            print(f"Error searching memory: {str(e)}")
            return []
    
    def clear_memory(self):
        """Clear all memory"""
        try:
            with open(self.conversation_file, 'w') as f:
                json.dump([], f)
            return True
        except Exception as e:
            print(f"Error clearing memory: {str(e)}")
            return False
    
    def export_memory(self, output_file=None):
        """
        Export memory to a file
        
        Args:
            output_file (str, optional): Output file path
            
        Returns:
            str: Path to the exported file
        """
        if not output_file:
            output_file = os.path.join(self.memory_dir, f"memory_export_{int(time.time())}.json")
        
        try:
            with open(self.conversation_file, 'r') as f:
                memory = json.load(f)
            
            with open(output_file, 'w') as f:
                json.dump(memory, f, indent=2)
            
            return output_file
        except Exception as e:
            print(f"Error exporting memory: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    memory = Memory()
    memory.add_interaction("Hello, how are you?", "I'm doing well, thank you for asking!")
    print(memory.get_recent_history())

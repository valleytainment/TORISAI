"""
TORIS AI - Memory Manager
Implements vector-based memory storage with proper cleanup
"""
from typing import Dict, Any, List, Optional, Tuple
import os
import json
import time
import logging
import atexit
import chromadb
from chromadb.config import Settings
from pydantic import BaseModel

logger = logging.getLogger("torisai.memory")

class MemoryConfig(BaseModel):
    """Configuration for memory manager"""
    memory_dir: str = "./memory"
    chroma_db_dir: str = "./chroma_db"
    conversation_file: str = "conversation_history.json"
    embedding_model: str = "all-MiniLM-L6-v2"
    ttl: int = 60 * 60 * 24 * 7  # 7 days in seconds

class ConversationEntry(BaseModel):
    """A single conversation entry"""
    user: str
    ai: str
    timestamp: float
    metadata: Dict[str, Any] = {}

class MemoryManager:
    """
    Manager for conversation memory and vector storage
    
    Handles storing and retrieving conversation history,
    with vector-based semantic search capabilities.
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize the memory manager
        
        Args:
            config: Configuration for the memory manager
        """
        self.config = config or MemoryConfig()
        
        # Ensure directories exist
        os.makedirs(self.config.memory_dir, exist_ok=True)
        os.makedirs(self.config.chroma_db_dir, exist_ok=True)
        
        # Initialize conversation file
        self.conversation_file = os.path.join(
            self.config.memory_dir, 
            self.config.conversation_file
        )
        if not os.path.exists(self.conversation_file):
            with open(self.conversation_file, "w") as f:
                json.dump([], f)
        
        # Initialize Chroma client
        self._initialize_chroma()
        
        # Register cleanup handler
        atexit.register(self._cleanup)
        
        logger.info("Memory manager initialized")
    
    def _initialize_chroma(self):
        """Initialize the Chroma client and collection"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=self.config.chroma_db_dir,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            # Create or get the conversation collection
            self.conversation_collection = self.chroma_client.get_or_create_collection(
                name="conversations",
                embedding_function=self._get_embedding_function()
            )
            
            logger.info("Chroma client initialized")
        except Exception as e:
            logger.error(f"Error initializing Chroma: {str(e)}")
            # Fallback to None if Chroma initialization fails
            self.chroma_client = None
            self.conversation_collection = None
    
    def _get_embedding_function(self):
        """Get the embedding function for Chroma"""
        try:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            return SentenceTransformerEmbeddingFunction(model_name=self.config.embedding_model)
        except ImportError:
            logger.warning("SentenceTransformer not available, using default embedding")
            return None
    
    def save_interaction(self, user_message: str, ai_response: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Save a user-AI interaction to memory
        
        Args:
            user_message: The user's message
            ai_response: The AI's response
            metadata: Optional metadata about the interaction
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create entry
            entry = ConversationEntry(
                user=user_message,
                ai=ai_response,
                timestamp=time.time(),
                metadata=metadata or {}
            )
            
            # Load existing history
            history = self.get_conversation_history(limit=0)
            
            # Add new entry
            history.append(entry.dict())
            
            # Save updated history
            with open(self.conversation_file, "w") as f:
                json.dump(history, f, indent=2)
            
            # Add to vector store if available
            if self.conversation_collection is not None:
                try:
                    # Create a combined text for embedding
                    combined_text = f"User: {user_message}\nAI: {ai_response}"
                    
                    # Generate a unique ID
                    entry_id = f"entry_{int(entry.timestamp * 1000)}"
                    
                    # Add to collection
                    self.conversation_collection.add(
                        documents=[combined_text],
                        metadatas=[entry.dict()],
                        ids=[entry_id]
                    )
                except Exception as e:
                    logger.error(f"Error adding to vector store: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving to memory: {str(e)}")
            return False
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation history
        
        Args:
            limit: Maximum number of entries to return (0 for all)
            
        Returns:
            List of conversation entries
        """
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, "r") as f:
                    history = json.load(f)
                
                # Return most recent entries
                return history[-limit:] if limit > 0 else history
            return []
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return []
    
    def get_formatted_history(self, limit: int = 10) -> str:
        """
        Get formatted conversation history as text
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            Formatted conversation history
        """
        history = self.get_conversation_history(limit)
        
        if not history:
            return "No conversation history found."
        
        formatted_history = ""
        for entry in history:
            formatted_history += f"User: {entry['user']}\n"
            formatted_history += f"AI: {entry['ai']}\n\n"
        
        return formatted_history
    
    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search memory for relevant conversations
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of relevant conversation entries
        """
        if self.conversation_collection is None:
            logger.warning("Vector store not available, falling back to recent history")
            return self.get_conversation_history(limit)
        
        try:
            results = self.conversation_collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            # Extract and return the metadata
            if results and "metadatas" in results and results["metadatas"]:
                return results["metadatas"][0]
            
            return []
        except Exception as e:
            logger.error(f"Error searching memory: {str(e)}")
            return []
    
    def clear_history(self) -> bool:
        """
        Clear conversation history
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear file
            with open(self.conversation_file, "w") as f:
                json.dump([], f)
            
            # Clear vector store if available
            if self.conversation_collection is not None:
                try:
                    self.conversation_collection.delete(where={})
                except Exception as e:
                    logger.error(f"Error clearing vector store: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}")
            return False
    
    def _cleanup(self):
        """Clean up resources"""
        try:
            if self.chroma_client is not None:
                # Persist changes
                self.chroma_client.persist()
                logger.info("Memory manager cleaned up")
        except Exception as e:
            logger.error(f"Error during memory cleanup: {str(e)}")

# Create a singleton instance
_memory_manager = None

def get_memory_manager(config: Optional[MemoryConfig] = None) -> MemoryManager:
    """
    Get the memory manager singleton
    
    Args:
        config: Optional configuration for the memory manager
        
    Returns:
        MemoryManager instance
    """
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(config)
    return _memory_manager

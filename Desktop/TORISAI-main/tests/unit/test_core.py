"""
TORIS AI - Basic Unit Tests
Implements tests for core functionality
"""
import pytest
import os
import sys
import asyncio
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import TORIS AI modules
from torisai.core.tool_protocol import ToolCall, extract_tool_calls, registry
from torisai.agents.base import Agent, AgentConfig
from torisai.agents.specialized import get_agent

class TestToolProtocol:
    """Tests for the tool protocol module"""
    
    def test_tool_call_parsing(self):
        """Test parsing tool calls from text"""
        # Test with valid JSON
        text = 'I need to search for something. {"name": "web_search", "args": {"query": "test query"}}'
        calls = extract_tool_calls(text)
        
        assert len(calls) == 1
        assert calls[0].name == "web_search"
        assert calls[0].args["query"] == "test query"
        
        # Test with multiple calls
        text = '''
        Here are two tools:
        {"name": "web_search", "args": {"query": "first query"}}
        And another one:
        {"name": "read_file", "args": {"file_path": "test.txt"}}
        '''
        calls = extract_tool_calls(text)
        
        assert len(calls) == 2
        assert calls[0].name == "web_search"
        assert calls[1].name == "read_file"
        
        # Test with invalid JSON
        text = 'This is not a valid tool call'
        calls = extract_tool_calls(text)
        
        assert len(calls) == 0
    
    def test_tool_registry(self):
        """Test the tool registry"""
        # Create a test tool
        def test_tool(arg1, arg2=None):
            return f"Test tool called with {arg1} and {arg2}"
        
        # Register the tool
        registry.register(
            ToolDefinition(
                name="test_tool",
                description="A test tool",
                parameters={
                    "arg1": {"type": "string"},
                    "arg2": {"type": "string", "default": None}
                },
                function=test_tool,
                requires_confirmation=False
            )
        )
        
        # Get the tool
        tool = registry.get("test_tool")
        
        assert tool is not None
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        
        # Execute the tool
        call = ToolCall(name="test_tool", args={"arg1": "value1", "arg2": "value2"})
        result = registry.execute(call)
        
        assert result == "Test tool called with value1 and value2"
        
        # List tools
        tools = registry.list_tools()
        
        assert len(tools) > 0
        assert any(t["name"] == "test_tool" for t in tools)

class TestAgents:
    """Tests for the agent modules"""
    
    @pytest.mark.asyncio
    async def test_base_agent(self):
        """Test the base agent"""
        # Create a mock Ollama client
        with patch('torisai.core.ollama_client.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate.return_value = "Test response"
            mock_get_client.return_value = mock_client
            
            # Create a mock memory manager
            with patch('torisai.memory.manager.get_memory_manager') as mock_get_memory:
                mock_memory = MagicMock()
                mock_memory.get_conversation_history.return_value = []
                mock_get_memory.return_value = mock_memory
                
                # Create an agent
                config = AgentConfig(
                    name="TestAgent",
                    description="Test agent",
                    system_prompt="You are a test agent"
                )
                agent = Agent(config)
                
                # Process a query
                response = await agent.process_query("Test query")
                
                # Check that the client was called
                mock_client.generate.assert_called_once()
                
                # Check that the memory was updated
                mock_memory.save_interaction.assert_called_once()
                
                # Check the response
                assert response == "Test response"
    
    def test_get_agent(self):
        """Test getting different agent types"""
        # Test general agent
        agent = get_agent("general")
        assert agent.config.name == "GeneralAgent"
        
        # Test planner agent
        agent = get_agent("planner")
        assert agent.config.name == "PlannerAgent"
        
        # Test coder agent
        agent = get_agent("coder")
        assert agent.config.name == "CoderAgent"
        
        # Test researcher agent
        agent = get_agent("researcher")
        assert agent.config.name == "ResearcherAgent"
        
        # Test default agent
        agent = get_agent("unknown")
        assert agent.config.name == "GeneralAgent"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

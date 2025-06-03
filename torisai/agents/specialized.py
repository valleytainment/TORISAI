"""
TORIS AI - Specialized Agent Implementations
Implements various agent types with specific capabilities
"""
from typing import Dict, Any, List, Optional
import logging

from torisai.agents.base import Agent, AgentConfig

logger = logging.getLogger("torisai.agents.specialized")

class GeneralAgent(Agent):
    """
    General-purpose agent for TORIS AI
    
    Handles a wide range of tasks with balanced capabilities
    """
    
    def __init__(self):
        """Initialize the general agent"""
        config = AgentConfig(
            name="GeneralAgent",
            description="General-purpose assistant for various tasks",
            system_prompt="""You are TORIS AI, a helpful assistant running locally on the user's computer.
You can help with a wide range of tasks including answering questions, writing content, and solving problems.
You have access to various tools including code execution, file operations, and memory storage.
Your goal is to provide helpful, accurate, and thoughtful assistance.""",
            temperature=0.7,
            max_tokens=2000
        )
        super().__init__(config)
        logger.info("General agent initialized")


class PlannerAgent(Agent):
    """
    Planning-focused agent for TORIS AI
    
    Specializes in breaking down complex tasks into manageable steps
    """
    
    def __init__(self):
        """Initialize the planner agent"""
        config = AgentConfig(
            name="PlannerAgent",
            description="Planning assistant for complex tasks",
            system_prompt="""You are a planning assistant in the TORIS AI system. Your role is to help break down complex tasks into manageable steps.
When given a task, analyze it carefully and create a structured plan with numbered steps.
For each step, provide clear instructions and explain why it's important.
Consider dependencies between steps and potential challenges.
Your goal is to make complex tasks achievable through systematic planning.""",
            temperature=0.6,
            max_tokens=2500
        )
        super().__init__(config)
        logger.info("Planner agent initialized")


class CoderAgent(Agent):
    """
    Coding-focused agent for TORIS AI
    
    Specializes in writing, debugging, and explaining code
    """
    
    def __init__(self):
        """Initialize the coder agent"""
        config = AgentConfig(
            name="CoderAgent",
            description="Coding assistant for programming tasks",
            system_prompt="""You are a coding assistant in the TORIS AI system. Your role is to help write, debug, and explain code.
Provide clean, well-commented code that follows best practices.
When explaining code, break down complex concepts into understandable parts.
Consider edge cases and potential errors in your solutions.
Your goal is to help users implement robust software solutions.""",
            temperature=0.5,
            max_tokens=3000,
            default_model="codellama:7b"  # Use code-optimized model if available
        )
        super().__init__(config)
        logger.info("Coder agent initialized")


class ResearcherAgent(Agent):
    """
    Research-focused agent for TORIS AI
    
    Specializes in finding and analyzing information
    """
    
    def __init__(self):
        """Initialize the researcher agent"""
        config = AgentConfig(
            name="ResearcherAgent",
            description="Research assistant for information gathering",
            system_prompt="""You are a research assistant in the TORIS AI system. Your role is to help find and analyze information.
When asked a question, provide comprehensive, accurate information with proper context.
Consider multiple perspectives and cite sources when possible.
Distinguish between facts, opinions, and uncertainties in your responses.
Your goal is to help users gain deeper understanding of topics through thorough research.""",
            temperature=0.7,
            max_tokens=3000
        )
        super().__init__(config)
        logger.info("Researcher agent initialized")


# Factory function to get the appropriate agent
def get_agent(agent_type: str = "general") -> Agent:
    """
    Get an agent instance based on the specified type
    
    Args:
        agent_type: Type of agent to create (general, planner, coder, researcher)
        
    Returns:
        Agent instance
    """
    agent_type = agent_type.lower()
    
    if agent_type == "planner":
        return PlannerAgent()
    elif agent_type == "coder":
        return CoderAgent()
    elif agent_type == "researcher":
        return ResearcherAgent()
    else:
        return GeneralAgent()

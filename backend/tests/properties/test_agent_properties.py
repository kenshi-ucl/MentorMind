"""Property-based tests for agent orchestrator.

Feature: mentormind-ai-tutor
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.services.agent_orchestrator import AgentOrchestrator
from app.models.agent_prompt import AgentPrompt


# Strategy for agent names
agent_name_strategy = st.sampled_from(["TutorAgent", "QuizAgent", "ContentAgent"])

# Strategy for non-empty question strings
non_empty_question_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Z')),
    min_size=1,
    max_size=500
).filter(lambda x: x.strip())

# Strategy for optional content context
content_context_strategy = st.lists(
    st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    min_size=0,
    max_size=5
)


class TestAgentProperties:
    """Property-based tests for agent orchestrator service."""
    
    @settings(max_examples=100, deadline=None)
    @given(agent_name=agent_name_strategy)
    def test_property_16_agent_prompt_loading_and_validation(self, agent_name):
        """
        Property 16: Agent Prompt Loading and Validation
        
        For any agent (TutorAgent, QuizAgent, ContentAgent), loading the prompt 
        configuration should return a valid AgentPrompt object containing: 
        name, role, description, system_prompt, example_format, and context_guidance fields.
        
        Validates: Requirements 8.4, 8.5
        """
        # Create fresh orchestrator for each test
        orchestrator = AgentOrchestrator()
        
        # Load the agent
        agent = orchestrator.get_agent(agent_name)
        
        # Agent should be loaded successfully
        assert agent is not None, f"Failed to load {agent_name}"
        assert isinstance(agent, AgentPrompt), f"{agent_name} is not an AgentPrompt instance"
        
        # Verify all required fields are present and non-empty
        assert agent.name, f"{agent_name} has empty name"
        assert agent.role, f"{agent_name} has empty role"
        assert agent.description, f"{agent_name} has empty description"
        assert agent.system_prompt, f"{agent_name} has empty system_prompt"
        
        # Verify example_format is a dict
        assert isinstance(agent.example_format, dict), \
            f"{agent_name} example_format is not a dict"
        
        # Verify context_guidance is a list
        assert isinstance(agent.context_guidance, list), \
            f"{agent_name} context_guidance is not a list"
        
        # Verify the agent passes its own validation
        assert agent.is_valid(), f"{agent_name} failed validation"
        
        # Verify the agent name matches the requested name
        assert agent.name == agent_name, \
            f"Agent name mismatch: expected {agent_name}, got {agent.name}"

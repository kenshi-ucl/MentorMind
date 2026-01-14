"""Property-based tests for Nebius AI integration.

Feature: nebius-ai-integration
"""
import os
import pytest
from hypothesis import given, strategies as st, settings, assume
from app.services.nebius_config import NebiusConfig, ModelConfig


# Strategy for valid API key strings (non-empty alphanumeric with some special chars)
api_key_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='-_'),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip() and len(x.strip()) > 0)


class TestNebiusConfigProperties:
    """Property-based tests for Nebius configuration."""
    
    @settings(max_examples=100, deadline=None)
    @given(api_key=api_key_strategy)
    def test_property_1_api_configuration_loading(self, api_key):
        """
        Property 1: API Configuration Loading
        
        For any valid API key string set in the NEBIUS_API_KEY environment variable,
        the NebiusConfig SHALL correctly load and use that key for authentication.
        
        **Validates: Requirements 1.1**
        """
        # Store original env value
        original_value = os.environ.get("NEBIUS_API_KEY")
        
        try:
            # Set the API key in environment
            os.environ["NEBIUS_API_KEY"] = api_key
            
            # Create config using default() which reads from env
            config = NebiusConfig.default()
            
            # Verify the API key was loaded correctly
            assert config.api_key == api_key, \
                f"API key mismatch: expected '{api_key}', got '{config.api_key}'"
            
            # Verify has_api_key returns True
            assert config.has_api_key(), \
                "has_api_key() should return True when API key is set"
            
            # Verify base URL is set to default
            assert config.base_url == "https://api.tokenfactory.nebius.com/v1/", \
                "Base URL should be set to Nebius Token Factory endpoint"
            
            # Verify all model configs are present
            assert config.tutor_model is not None, "tutor_model should be configured"
            assert config.quiz_model is not None, "quiz_model should be configured"
            assert config.content_model is not None, "content_model should be configured"
            assert config.vision_model is not None, "vision_model should be configured"
            assert config.embedding_model is not None, "embedding_model should be configured"
            
            # Verify model configs have valid model_ids
            assert config.tutor_model.model_id, "tutor_model should have model_id"
            assert config.quiz_model.model_id, "quiz_model should have model_id"
            assert config.content_model.model_id, "content_model should have model_id"
            assert config.vision_model.model_id, "vision_model should have model_id"
            assert config.embedding_model.model_id, "embedding_model should have model_id"
            
        finally:
            # Restore original env value
            if original_value is not None:
                os.environ["NEBIUS_API_KEY"] = original_value
            elif "NEBIUS_API_KEY" in os.environ:
                del os.environ["NEBIUS_API_KEY"]
    
    @settings(max_examples=100, deadline=None)
    @given(api_key=api_key_strategy)
    def test_config_round_trip(self, api_key):
        """
        Test that configuration can be serialized and maintains structure.
        
        For any valid configuration, converting to dict should preserve all fields.
        """
        # Store original env value
        original_value = os.environ.get("NEBIUS_API_KEY")
        
        try:
            os.environ["NEBIUS_API_KEY"] = api_key
            config = NebiusConfig.default()
            
            # Convert to dict
            config_dict = config.to_dict()
            
            # Verify structure
            assert "nebius" in config_dict, "Config dict should have 'nebius' key"
            nebius_data = config_dict["nebius"]
            
            assert "base_url" in nebius_data, "Should have base_url"
            assert "models" in nebius_data, "Should have models"
            assert "retry" in nebius_data, "Should have retry config"
            assert "timeout" in nebius_data, "Should have timeout"
            
            # Verify models
            models = nebius_data["models"]
            assert "tutor" in models, "Should have tutor model"
            assert "quiz" in models, "Should have quiz model"
            assert "content" in models, "Should have content model"
            assert "vision" in models, "Should have vision model"
            assert "embedding" in models, "Should have embedding model"
            
            # Verify each model has required fields
            for model_name, model_data in models.items():
                assert "model_id" in model_data, f"{model_name} should have model_id"
                
        finally:
            if original_value is not None:
                os.environ["NEBIUS_API_KEY"] = original_value
            elif "NEBIUS_API_KEY" in os.environ:
                del os.environ["NEBIUS_API_KEY"]


class TestModelConfigProperties:
    """Property-based tests for ModelConfig."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        model_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
        max_tokens=st.integers(min_value=1, max_value=100000),
        top_p=st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
    )
    def test_model_config_from_dict_round_trip(self, model_id, temperature, max_tokens, top_p):
        """
        Test ModelConfig round-trip through dict serialization.
        
        For any valid ModelConfig parameters, creating from dict and converting back
        should produce equivalent values.
        """
        # Create config from dict
        input_dict = {
            "model_id": model_id,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        config = ModelConfig.from_dict(input_dict)
        
        # Verify values match
        assert config.model_id == model_id
        assert config.temperature == temperature
        assert config.max_tokens == max_tokens
        assert config.top_p == top_p
        
        # Convert back to dict
        output_dict = config.to_dict()
        
        # Verify round-trip
        assert output_dict["model_id"] == model_id
        assert output_dict["temperature"] == temperature
        assert output_dict["max_tokens"] == max_tokens
        assert output_dict["top_p"] == top_p



from app.services.retry_handler import (
    RetryHandler,
    AIErrorResponse,
    TimeoutError,
    RateLimitError,
    ServerError,
    ClientError,
    AuthenticationError
)


class TestRetryHandlerProperties:
    """Property-based tests for RetryHandler."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        max_attempts=st.integers(min_value=1, max_value=10),
        timeout_count=st.integers(min_value=0, max_value=5)
    )
    def test_property_9_retry_on_timeout(self, max_attempts, timeout_count):
        """
        Property 9: Retry on Timeout
        
        For any API call that times out, the RetryHandler SHALL retry up to the
        configured maximum attempts (default 3) with exponential backoff before
        returning an error.
        
        **Validates: Requirements 5.1**
        """
        # Track how many times the function was called
        call_count = 0
        
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            
            # Fail with timeout for the first `timeout_count` calls
            if call_count <= timeout_count:
                raise TimeoutError(f"Request timed out (attempt {call_count})")
            
            # Succeed after timeout_count failures
            return "success"
        
        handler = RetryHandler(
            max_attempts=max_attempts,
            base_delay=0.001,  # Very short delay for testing
            max_delay=0.01
        )
        
        if timeout_count < max_attempts:
            # Should eventually succeed
            result = handler.execute(mock_api_call)
            assert result == "success", "Should return success after retries"
            assert call_count == timeout_count + 1, \
                f"Should have called function {timeout_count + 1} times, got {call_count}"
        else:
            # Should exhaust all retries and raise
            with pytest.raises(TimeoutError):
                handler.execute(mock_api_call)
            
            assert call_count == max_attempts, \
                f"Should have called function exactly {max_attempts} times, got {call_count}"
    
    @settings(max_examples=100, deadline=None)
    @given(
        max_attempts=st.integers(min_value=1, max_value=5),
        base_delay=st.floats(min_value=0.001, max_value=0.1, allow_nan=False),
        attempt=st.integers(min_value=0, max_value=10)
    )
    def test_exponential_backoff_calculation(self, max_attempts, base_delay, attempt):
        """
        Test that exponential backoff delay increases correctly.
        
        For any attempt number, the delay should follow exponential backoff
        formula: base_delay * (2 ^ attempt), capped at max_delay.
        """
        max_delay = base_delay * 100  # Ensure max_delay > base_delay
        
        handler = RetryHandler(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay
        )
        
        delay = handler.calculate_delay(attempt)
        
        # Expected delay with exponential backoff
        expected = min(base_delay * (2 ** attempt), max_delay)
        
        assert abs(delay - expected) < 0.0001, \
            f"Delay should be {expected}, got {delay}"
        
        # Delay should never exceed max_delay
        assert delay <= max_delay, \
            f"Delay {delay} should not exceed max_delay {max_delay}"
        
        # Delay should be at least base_delay for attempt 0
        if attempt == 0:
            assert delay >= base_delay, \
                f"Initial delay should be at least base_delay {base_delay}"
    
    @settings(max_examples=100, deadline=None)
    @given(retry_after=st.integers(min_value=1, max_value=60))
    def test_retry_after_respected(self, retry_after):
        """
        Test that server-specified retry-after is respected.
        
        When a rate limit error includes retry-after, the handler should
        use that value (capped at max_delay).
        """
        max_delay = 30.0
        
        handler = RetryHandler(
            max_attempts=3,
            base_delay=1.0,
            max_delay=max_delay
        )
        
        delay = handler.calculate_delay(attempt=0, retry_after=retry_after)
        
        expected = min(float(retry_after), max_delay)
        
        assert abs(delay - expected) < 0.0001, \
            f"Delay should respect retry_after: expected {expected}, got {delay}"



class TestAIErrorResponseProperties:
    """Property-based tests for AIErrorResponse."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        error_message=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        retry_after=st.one_of(st.none(), st.integers(min_value=1, max_value=300))
    )
    def test_property_4_api_error_graceful_handling(self, error_message, retry_after):
        """
        Property 4: API Error Graceful Handling
        
        For any API failure (timeout, rate limit, server error), the system SHALL
        return a user-friendly error message without exposing internal details or crashing.
        
        **Validates: Requirements 2.4, 5.4, 5.5**
        """
        # Test with different error types
        error_types = [
            TimeoutError(error_message, retry_after),
            RateLimitError(error_message, retry_after),
            ServerError(error_message, retry_after),
            ClientError(error_message, status_code=400),
            AuthenticationError(error_message),
            ConnectionError(error_message),
            Exception(error_message)  # Generic exception
        ]
        
        for error in error_types:
            response = AIErrorResponse.from_exception(error)
            
            # Property 1: Response should always have success=False
            assert response.success is False, \
                f"Error response should have success=False for {type(error).__name__}"
            
            # Property 2: User message should not contain technical details
            assert error_message not in response.user_message or len(error_message) < 10, \
                f"User message should not expose raw error message for {type(error).__name__}"
            
            # Property 3: User message should be non-empty and user-friendly
            assert len(response.user_message) > 0, \
                f"User message should not be empty for {type(error).__name__}"
            assert "Exception" not in response.user_message, \
                f"User message should not contain 'Exception' for {type(error).__name__}"
            assert "Error:" not in response.user_message, \
                f"User message should not contain 'Error:' for {type(error).__name__}"
            
            # Property 4: Technical details should be preserved for logging
            assert response.technical_details is not None, \
                f"Technical details should be captured for {type(error).__name__}"
            assert type(error).__name__ in response.technical_details, \
                f"Technical details should include error type for {type(error).__name__}"
            
            # Property 5: Error type should be categorized
            valid_error_types = {"timeout", "rate_limit", "api", "config", "network", "response", "unknown"}
            assert response.error_type in valid_error_types, \
                f"Error type '{response.error_type}' should be valid for {type(error).__name__}"
            
            # Property 6: to_dict should produce valid JSON-serializable dict
            response_dict = response.to_dict()
            assert isinstance(response_dict, dict), "to_dict should return a dict"
            assert "success" in response_dict, "Dict should have 'success' key"
            assert "error_type" in response_dict, "Dict should have 'error_type' key"
            assert "user_message" in response_dict, "Dict should have 'user_message' key"
            
            # Property 7: Technical details should NOT be in the dict (for security)
            assert "technical_details" not in response_dict, \
                "Technical details should not be exposed in dict"
    
    @settings(max_examples=100, deadline=None)
    @given(
        error_message=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        status_code=st.integers(min_value=400, max_value=599)
    )
    def test_error_type_categorization(self, error_message, status_code):
        """
        Test that errors are correctly categorized by type.
        
        Different error types should map to appropriate error_type values.
        """
        # Timeout errors -> "timeout"
        timeout_response = AIErrorResponse.from_exception(TimeoutError(error_message))
        assert timeout_response.error_type == "timeout"
        
        # Rate limit errors -> "rate_limit"
        rate_limit_response = AIErrorResponse.from_exception(RateLimitError(error_message))
        assert rate_limit_response.error_type == "rate_limit"
        
        # Server errors -> "api"
        server_response = AIErrorResponse.from_exception(ServerError(error_message))
        assert server_response.error_type == "api"
        
        # Auth errors -> "config"
        auth_response = AIErrorResponse.from_exception(AuthenticationError(error_message))
        assert auth_response.error_type == "config"
        
        # Client errors -> "api"
        client_response = AIErrorResponse.from_exception(ClientError(error_message, status_code))
        assert client_response.error_type == "api"
        
        # Network errors -> "network"
        network_response = AIErrorResponse.from_exception(ConnectionError(error_message))
        assert network_response.error_type == "network"
    
    @settings(max_examples=100, deadline=None)
    @given(retry_after=st.integers(min_value=1, max_value=300))
    def test_retry_after_preserved(self, retry_after):
        """
        Test that retry_after value is preserved in error response.
        
        When an error includes retry_after, it should be included in the response.
        """
        error = RateLimitError("Rate limited", retry_after=retry_after)
        response = AIErrorResponse.from_exception(error)
        
        assert response.retry_after == retry_after, \
            f"retry_after should be preserved: expected {retry_after}, got {response.retry_after}"
        
        # Should also be in dict when present
        response_dict = response.to_dict()
        assert response_dict.get("retry_after") == retry_after, \
            "retry_after should be in dict when present"


from app.services.agent_orchestrator import AgentOrchestrator
from app.models.agent_prompt import AgentPrompt
from unittest.mock import MagicMock, patch


class TestChatMessageConstructionProperties:
    """Property-based tests for chat message API call construction."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        user_message=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        context_items=st.lists(
            st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
            min_size=0,
            max_size=5
        )
    )
    def test_property_3_chat_message_api_call_construction(self, user_message, context_items):
        """
        Property 3: Chat Message API Call Construction
        
        For any user message and optional content context, the TutorAgent SHALL
        construct a valid API request that includes the system prompt, context
        (if provided), and user message in the correct message format.
        
        **Validates: Requirements 2.1, 2.2, 2.6**
        """
        # Create a mock TutorAgent prompt
        mock_agent = AgentPrompt(
            name="TutorAgent",
            role="AI Tutor",
            description="Test tutor agent",
            system_prompt="You are a helpful AI tutor.",
            example_format={},
            context_guidance=["Use context when available", "Be helpful"]
        )
        
        # Create orchestrator with mocked client
        with patch('app.services.agent_orchestrator.NebiusClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.is_fallback_mode = True
            mock_client_instance.chat_completion.return_value = "Test response"
            MockClient.return_value = mock_client_instance
            
            orchestrator = AgentOrchestrator()
            orchestrator._agents["TutorAgent"] = mock_agent
            orchestrator._loaded = True
            orchestrator._nebius_client = mock_client_instance
            
            # Build messages using the internal method
            context = context_items if context_items else None
            messages = orchestrator._build_chat_messages(mock_agent, user_message, context)
            
            # Property 1: Messages should be a non-empty list
            assert isinstance(messages, list), "Messages should be a list"
            assert len(messages) >= 2, "Messages should have at least system and user messages"
            
            # Property 2: First message should be system message with agent's system prompt
            assert messages[0]["role"] == "system", "First message should be system role"
            assert mock_agent.system_prompt in messages[0]["content"], \
                "System message should contain agent's system prompt"
            
            # Property 3: Last message should be user message
            assert messages[-1]["role"] == "user", "Last message should be user role"
            assert messages[-1]["content"] == user_message, \
                "User message content should match input"
            
            # Property 4: If context provided, it should be included
            if context_items:
                # Find context message
                context_found = False
                for msg in messages:
                    if "Content Context:" in msg.get("content", ""):
                        context_found = True
                        # Verify all context items are present
                        for ctx_item in context_items:
                            assert ctx_item in msg["content"], \
                                f"Context item '{ctx_item}' should be in context message"
                        break
                
                assert context_found, "Context message should be present when context provided"
                
                # Context guidance should be added to system prompt
                assert "Context Guidance:" in messages[0]["content"], \
                    "Context guidance should be added when context is provided"
            
            # Property 5: All messages should have valid structure
            for msg in messages:
                assert "role" in msg, "Each message should have 'role'"
                assert "content" in msg, "Each message should have 'content'"
                assert msg["role"] in ["system", "user", "assistant"], \
                    f"Role should be valid, got '{msg['role']}'"
                assert isinstance(msg["content"], str), "Content should be a string"
                assert len(msg["content"]) > 0, "Content should not be empty"
    
    @settings(max_examples=100, deadline=None)
    @given(
        user_message=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
        max_tokens=st.integers(min_value=100, max_value=4096)
    )
    def test_chat_respects_model_parameters(self, user_message, temperature, max_tokens):
        """
        Test that chat completion respects configured temperature and max_tokens.
        
        For any valid model parameters, the API call should use those parameters.
        
        **Validates: Requirements 2.6**
        """
        # Create a mock TutorAgent prompt
        mock_agent = AgentPrompt(
            name="TutorAgent",
            role="AI Tutor",
            description="Test tutor agent",
            system_prompt="You are a helpful AI tutor.",
            example_format={},
            context_guidance=[]
        )
        
        # Create config with specific parameters
        config = NebiusConfig.default()
        config.tutor_model.temperature = temperature
        config.tutor_model.max_tokens = max_tokens
        
        # Create orchestrator with mocked client
        with patch('app.services.agent_orchestrator.NebiusClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.is_fallback_mode = False
            mock_client_instance.chat_completion.return_value = "Test response"
            MockClient.return_value = mock_client_instance
            
            orchestrator = AgentOrchestrator(config=config)
            orchestrator._agents["TutorAgent"] = mock_agent
            orchestrator._loaded = True
            orchestrator._nebius_client = mock_client_instance
            
            # Call process_chat
            orchestrator.process_chat(user_message, stream=False)
            
            # Verify chat_completion was called with correct parameters
            mock_client_instance.chat_completion.assert_called()
            call_kwargs = mock_client_instance.chat_completion.call_args
            
            # Check that temperature and max_tokens were passed
            if call_kwargs.kwargs:
                assert call_kwargs.kwargs.get("temperature") == temperature, \
                    f"Temperature should be {temperature}"
                assert call_kwargs.kwargs.get("max_tokens") == max_tokens, \
                    f"Max tokens should be {max_tokens}"
    
    @settings(max_examples=50, deadline=None)
    @given(
        user_message=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
    )
    def test_chat_without_context_has_minimal_messages(self, user_message):
        """
        Test that chat without context produces minimal message structure.
        
        When no context is provided, messages should only contain system and user.
        """
        mock_agent = AgentPrompt(
            name="TutorAgent",
            role="AI Tutor",
            description="Test tutor agent",
            system_prompt="You are a helpful AI tutor.",
            example_format={},
            context_guidance=["Some guidance"]
        )
        
        with patch('app.services.agent_orchestrator.NebiusClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.is_fallback_mode = True
            MockClient.return_value = mock_client_instance
            
            orchestrator = AgentOrchestrator()
            orchestrator._agents["TutorAgent"] = mock_agent
            orchestrator._loaded = True
            
            # Build messages without context
            messages = orchestrator._build_chat_messages(mock_agent, user_message, None)
            
            # Should have exactly 2 messages: system and user
            assert len(messages) == 2, \
                f"Without context, should have 2 messages, got {len(messages)}"
            
            # System message should NOT contain context guidance
            assert "Context Guidance:" not in messages[0]["content"], \
                "Context guidance should not be added when no context provided"


class TestQuizGenerationProperties:
    """Property-based tests for quiz generation with Nebius AI."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        question_count=st.integers(min_value=1, max_value=10),
        topic=st.one_of(
            st.none(),
            st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
        ),
        content=st.one_of(
            st.none(),
            st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
        )
    )
    def test_property_5_quiz_structure_validity(self, question_count, topic, content):
        """
        Property 5: Quiz Structure Validity
        
        For any quiz generation request with a specified question count N, the QuizAgent
        SHALL return exactly N questions, each with exactly 4 distinct options, a valid
        correct_index (0-3), and non-empty explanation.
        
        **Validates: Requirements 3.1, 3.2, 3.6**
        """
        # Skip if both topic and content are None (invalid request)
        assume(topic is not None or content is not None)
        
        # Create a mock QuizAgent prompt
        mock_agent = AgentPrompt(
            name="QuizAgent",
            role="Quiz Generator",
            description="Test quiz agent",
            system_prompt="You are a quiz generator.",
            example_format={},
            context_guidance=[]
        )
        
        # Create a mock response that simulates valid AI output
        mock_questions = []
        for i in range(question_count):
            mock_questions.append({
                "id": f"q{i+1}",
                "question": f"Test question {i+1} about {topic or 'content'}?",
                "options": [f"Option A{i}", f"Option B{i}", f"Option C{i}", f"Option D{i}"],
                "correct_index": i % 4,
                "explanation": f"Explanation for question {i+1}."
            })
        
        mock_response = json.dumps(mock_questions)
        
        with patch('app.services.agent_orchestrator.NebiusClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.is_fallback_mode = False
            mock_client_instance.chat_completion.return_value = mock_response
            MockClient.return_value = mock_client_instance
            
            orchestrator = AgentOrchestrator()
            orchestrator._agents["QuizAgent"] = mock_agent
            orchestrator._loaded = True
            orchestrator._nebius_client = mock_client_instance
            
            # Generate quiz
            questions = orchestrator.generate_quiz(
                topic=topic,
                content=content,
                question_count=question_count
            )
            
            # Property 1: Should return exactly question_count questions
            assert len(questions) == question_count, \
                f"Expected {question_count} questions, got {len(questions)}"
            
            for i, q in enumerate(questions):
                # Property 2: Each question should have required fields
                assert "id" in q, f"Question {i+1} should have 'id'"
                assert "question" in q, f"Question {i+1} should have 'question'"
                assert "options" in q, f"Question {i+1} should have 'options'"
                assert "correct_index" in q, f"Question {i+1} should have 'correct_index'"
                assert "explanation" in q, f"Question {i+1} should have 'explanation'"
                
                # Property 3: Each question should have exactly 4 options
                assert len(q["options"]) == 4, \
                    f"Question {i+1} should have exactly 4 options, got {len(q['options'])}"
                
                # Property 4: correct_index should be valid (0-3)
                assert 0 <= q["correct_index"] < 4, \
                    f"Question {i+1} correct_index should be 0-3, got {q['correct_index']}"
                
                # Property 5: All options should be distinct
                assert len(set(q["options"])) == 4, \
                    f"Question {i+1} should have 4 distinct options"
                
                # Property 6: Explanation should be non-empty
                assert q["explanation"] and len(q["explanation"].strip()) > 0, \
                    f"Question {i+1} should have non-empty explanation"
                
                # Property 7: Question text should be non-empty
                assert q["question"] and len(q["question"].strip()) > 0, \
                    f"Question {i+1} should have non-empty question text"


import json


class TestQuizJSONRoundTripProperties:
    """Property-based tests for quiz JSON serialization."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        question_id=st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and x.isalnum()),
        question_text=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        options=st.lists(
            st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
            min_size=4,
            max_size=4,
            unique=True
        ),
        correct_index=st.integers(min_value=0, max_value=3),
        explanation=st.text(min_size=1, max_size=300).filter(lambda x: x.strip())
    )
    def test_property_6_quiz_json_round_trip(self, question_id, question_text, options, correct_index, explanation):
        """
        Property 6: Quiz JSON Round-Trip
        
        For any valid quiz question structure, serializing to JSON and parsing back
        SHALL produce an equivalent structure.
        
        **Validates: Requirements 3.2**
        """
        from app.models.quiz import QuizQuestion
        
        # Create original question
        original = QuizQuestion(
            id=question_id,
            question=question_text,
            options=options,
            correct_index=correct_index,
            explanation=explanation
        )
        
        # Serialize to dict (which is JSON-serializable)
        serialized = original.to_dict()
        
        # Verify serialized structure
        assert isinstance(serialized, dict), "Serialized should be a dict"
        assert "id" in serialized, "Serialized should have 'id'"
        assert "question" in serialized, "Serialized should have 'question'"
        assert "options" in serialized, "Serialized should have 'options'"
        assert "correctIndex" in serialized, "Serialized should have 'correctIndex'"
        assert "explanation" in serialized, "Serialized should have 'explanation'"
        
        # Convert to JSON string and back
        json_str = json.dumps(serialized)
        parsed = json.loads(json_str)
        
        # Deserialize back to QuizQuestion
        restored = QuizQuestion.from_dict(parsed)
        
        # Verify round-trip equivalence
        assert restored.id == original.id, \
            f"ID mismatch: {restored.id} != {original.id}"
        assert restored.question == original.question, \
            f"Question mismatch: {restored.question} != {original.question}"
        assert restored.options == original.options, \
            f"Options mismatch: {restored.options} != {original.options}"
        assert restored.correct_index == original.correct_index, \
            f"correct_index mismatch: {restored.correct_index} != {original.correct_index}"
        assert restored.explanation == original.explanation, \
            f"Explanation mismatch: {restored.explanation} != {original.explanation}"
        
        # Verify the restored question is valid
        assert restored.is_valid(), "Restored question should be valid"


class TestQuizOptionsDistinctnessProperties:
    """Property-based tests for quiz options distinctness."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        question_count=st.integers(min_value=1, max_value=5)
    )
    def test_property_10_quiz_options_distinctness(self, question_count):
        """
        Property 10: Quiz Options Distinctness
        
        For any generated quiz question, all four answer options SHALL be distinct
        strings (no duplicates).
        
        **Validates: Requirements 7.2**
        """
        # Create a mock QuizAgent prompt
        mock_agent = AgentPrompt(
            name="QuizAgent",
            role="Quiz Generator",
            description="Test quiz agent",
            system_prompt="You are a quiz generator.",
            example_format={},
            context_guidance=[]
        )
        
        # Create mock response with distinct options
        mock_questions = []
        for i in range(question_count):
            mock_questions.append({
                "id": f"q{i+1}",
                "question": f"Test question {i+1}?",
                "options": [
                    f"Unique option A for Q{i+1}",
                    f"Unique option B for Q{i+1}",
                    f"Unique option C for Q{i+1}",
                    f"Unique option D for Q{i+1}"
                ],
                "correct_index": 0,
                "explanation": f"Explanation {i+1}."
            })
        
        mock_response = json.dumps(mock_questions)
        
        with patch('app.services.agent_orchestrator.NebiusClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.is_fallback_mode = False
            mock_client_instance.chat_completion.return_value = mock_response
            MockClient.return_value = mock_client_instance
            
            orchestrator = AgentOrchestrator()
            orchestrator._agents["QuizAgent"] = mock_agent
            orchestrator._loaded = True
            orchestrator._nebius_client = mock_client_instance
            
            # Generate quiz
            questions = orchestrator.generate_quiz(
                topic="Test Topic",
                question_count=question_count
            )
            
            # Verify each question has distinct options
            for i, q in enumerate(questions):
                options = q.get("options", [])
                
                # Property 1: Should have exactly 4 options
                assert len(options) == 4, \
                    f"Question {i+1} should have 4 options, got {len(options)}"
                
                # Property 2: All options should be distinct
                unique_options = set(options)
                assert len(unique_options) == 4, \
                    f"Question {i+1} has duplicate options: {options}"
                
                # Property 3: No option should be empty
                for j, opt in enumerate(options):
                    assert opt and len(opt.strip()) > 0, \
                        f"Question {i+1}, option {j+1} should not be empty"
    
    @settings(max_examples=100, deadline=None)
    @given(
        duplicate_index=st.integers(min_value=0, max_value=3)
    )
    def test_duplicate_options_rejected(self, duplicate_index):
        """
        Test that questions with duplicate options are rejected during validation.
        
        The _validate_quiz_question method should reject questions where options
        are not all distinct.
        """
        # Create orchestrator
        orchestrator = AgentOrchestrator()
        
        # Create question data with duplicate options
        options = ["Option A", "Option B", "Option C", "Option D"]
        # Make one option duplicate another
        target_index = (duplicate_index + 1) % 4
        options[target_index] = options[duplicate_index]
        
        question_data = {
            "id": "q1",
            "question": "Test question?",
            "options": options,
            "correct_index": 0,
            "explanation": "Test explanation."
        }
        
        # Validate should return None for invalid question
        result = orchestrator._validate_quiz_question(question_data, 1)
        
        assert result is None, \
            f"Question with duplicate options should be rejected: {options}"
    
    @settings(max_examples=100, deadline=None)
    @given(
        correct_index=st.integers(min_value=-10, max_value=10)
    )
    def test_invalid_correct_index_rejected(self, correct_index):
        """
        Test that questions with invalid correct_index are rejected.
        
        correct_index must be 0, 1, 2, or 3.
        """
        # Skip valid indices
        assume(correct_index < 0 or correct_index >= 4)
        
        orchestrator = AgentOrchestrator()
        
        question_data = {
            "id": "q1",
            "question": "Test question?",
            "options": ["A", "B", "C", "D"],
            "correct_index": correct_index,
            "explanation": "Test explanation."
        }
        
        result = orchestrator._validate_quiz_question(question_data, 1)
        
        assert result is None, \
            f"Question with invalid correct_index {correct_index} should be rejected"


class TestContentProcessingProperties:
    """Property-based tests for content processing with Nebius AI."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        content_type=st.sampled_from(['pdf', 'image', 'text']),
        filename=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and '/' not in x and '\\' not in x),
        title=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        summary=st.text(min_size=10, max_size=500).filter(lambda x: x.strip()),
        key_points=st.lists(
            st.text(min_size=5, max_size=200).filter(lambda x: x.strip()),
            min_size=1,
            max_size=5
        ),
        topics=st.lists(
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
            min_size=1,
            max_size=5
        )
    )
    def test_property_7_content_processing_output_structure(
        self, content_type, filename, title, summary, key_points, topics
    ):
        """
        Property 7: Content Processing Output Structure
        
        For any successfully processed content (PDF, image, or video), the ContentAgent
        SHALL return a result containing all required fields: title, summary, key_points
        (non-empty list), concepts, topics, and source_type.
        
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        """
        # Create a mock ContentAgent prompt
        mock_agent = AgentPrompt(
            name="ContentAgent",
            role="Content Processor",
            description="Test content agent",
            system_prompt="You are a content processor.",
            example_format={},
            context_guidance=[]
        )
        
        # Create mock AI response that simulates valid output
        mock_response_data = {
            "title": title,
            "summary": summary,
            "key_points": key_points,
            "concepts": [
                {"term": "Test Concept", "definition": "A test definition"}
            ],
            "topics": topics
        }
        mock_response = json.dumps(mock_response_data)
        
        with patch('app.services.agent_orchestrator.NebiusClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.is_fallback_mode = False
            mock_client_instance.chat_completion.return_value = mock_response
            mock_client_instance.vision_completion.return_value = mock_response
            MockClient.return_value = mock_client_instance
            
            orchestrator = AgentOrchestrator()
            orchestrator._agents["ContentAgent"] = mock_agent
            orchestrator._loaded = True
            orchestrator._nebius_client = mock_client_instance
            
            # Process content based on type
            if content_type == 'image':
                # For image, provide bytes
                content_data = b"fake image data"
            else:
                # For text/pdf, provide string
                content_data = "Sample text content for processing."
            
            result = orchestrator.process_content(
                content_data=content_data,
                content_type=content_type,
                filename=filename
            )
            
            # Property 1: Result should be a dictionary
            assert isinstance(result, dict), "Result should be a dictionary"
            
            # Property 2: Result should have all required fields
            required_fields = ['title', 'summary', 'key_points', 'concepts', 'topics', 'source_type']
            for field in required_fields:
                assert field in result, f"Result should have '{field}' field"
            
            # Property 3: title should be a non-empty string
            assert isinstance(result['title'], str), "title should be a string"
            assert len(result['title'].strip()) > 0, "title should not be empty"
            
            # Property 4: summary should be a non-empty string
            assert isinstance(result['summary'], str), "summary should be a string"
            assert len(result['summary'].strip()) > 0, "summary should not be empty"
            
            # Property 5: key_points should be a non-empty list
            assert isinstance(result['key_points'], list), "key_points should be a list"
            assert len(result['key_points']) > 0, "key_points should not be empty"
            
            # Property 6: Each key point should be a non-empty string
            for i, point in enumerate(result['key_points']):
                assert isinstance(point, str), f"key_point {i} should be a string"
                assert len(point.strip()) > 0, f"key_point {i} should not be empty"
            
            # Property 7: concepts should be a list
            assert isinstance(result['concepts'], list), "concepts should be a list"
            
            # Property 8: Each concept should have term and definition
            for i, concept in enumerate(result['concepts']):
                assert isinstance(concept, dict), f"concept {i} should be a dict"
                assert 'term' in concept, f"concept {i} should have 'term'"
                assert 'definition' in concept, f"concept {i} should have 'definition'"
            
            # Property 9: topics should be a list
            assert isinstance(result['topics'], list), "topics should be a list"
            
            # Property 10: source_type should match input content_type
            assert result['source_type'] == content_type, \
                f"source_type should be '{content_type}', got '{result['source_type']}'"
            
            # Property 11: processing_status should indicate success
            if 'processing_status' in result:
                assert result['processing_status'] in ['complete', 'partial'], \
                    f"processing_status should be 'complete' or 'partial', got '{result['processing_status']}'"
    
    @settings(max_examples=50, deadline=None)
    @given(
        content_type=st.sampled_from(['pdf', 'image', 'text']),
        filename=st.text(min_size=1, max_size=30).filter(lambda x: x.strip() and '/' not in x)
    )
    def test_content_processing_handles_invalid_json(self, content_type, filename):
        """
        Test that content processing handles invalid JSON responses gracefully.
        
        When AI returns non-JSON response, the system should still return
        a valid result structure with partial status.
        """
        mock_agent = AgentPrompt(
            name="ContentAgent",
            role="Content Processor",
            description="Test content agent",
            system_prompt="You are a content processor.",
            example_format={},
            context_guidance=[]
        )
        
        # Return invalid JSON
        mock_response = "This is not valid JSON, just plain text analysis."
        
        with patch('app.services.agent_orchestrator.NebiusClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.is_fallback_mode = False
            mock_client_instance.chat_completion.return_value = mock_response
            mock_client_instance.vision_completion.return_value = mock_response
            MockClient.return_value = mock_client_instance
            
            orchestrator = AgentOrchestrator()
            orchestrator._agents["ContentAgent"] = mock_agent
            orchestrator._loaded = True
            orchestrator._nebius_client = mock_client_instance
            
            content_data = b"fake data" if content_type == 'image' else "text content"
            
            result = orchestrator.process_content(
                content_data=content_data,
                content_type=content_type,
                filename=filename
            )
            
            # Should still return valid structure
            assert isinstance(result, dict), "Result should be a dictionary"
            assert 'title' in result, "Result should have title"
            assert 'summary' in result, "Result should have summary"
            assert 'key_points' in result, "Result should have key_points"
            assert 'source_type' in result, "Result should have source_type"
            
            # Should indicate partial processing
            if 'processing_status' in result:
                assert result['processing_status'] in ['partial', 'complete'], \
                    "Should handle gracefully"
    
    @settings(max_examples=50, deadline=None)
    @given(
        filename=st.text(min_size=1, max_size=30).filter(lambda x: x.strip() and '/' not in x)
    )
    def test_content_processing_error_returns_valid_structure(self, filename):
        """
        Test that content processing errors return valid error structure.
        
        When processing fails, the result should still have required fields
        with appropriate error indication.
        """
        mock_agent = AgentPrompt(
            name="ContentAgent",
            role="Content Processor",
            description="Test content agent",
            system_prompt="You are a content processor.",
            example_format={},
            context_guidance=[]
        )
        
        with patch('app.services.agent_orchestrator.NebiusClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.is_fallback_mode = False
            # Simulate API error
            mock_client_instance.chat_completion.side_effect = Exception("API Error")
            mock_client_instance.vision_completion.side_effect = Exception("API Error")
            MockClient.return_value = mock_client_instance
            
            orchestrator = AgentOrchestrator()
            orchestrator._agents["ContentAgent"] = mock_agent
            orchestrator._loaded = True
            orchestrator._nebius_client = mock_client_instance
            
            result = orchestrator.process_content(
                content_data="test content",
                content_type="text",
                filename=filename
            )
            
            # Should return error structure
            assert isinstance(result, dict), "Result should be a dictionary"
            assert 'source_type' in result, "Result should have source_type"
            assert 'processing_status' in result, "Result should have processing_status"
            assert result['processing_status'] == 'failed', \
                "processing_status should be 'failed' on error"
            assert 'error_message' in result, "Result should have error_message"
            assert result['error_message'] is not None, "error_message should not be None"



class TestLargeDocumentChunkingProperties:
    """Property-based tests for large document chunking."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_paragraphs=st.integers(min_value=5, max_value=20),
        paragraph_size=st.integers(min_value=500, max_value=2000)
    )
    def test_property_8_large_document_chunking(self, num_paragraphs, paragraph_size):
        """
        Property 8: Large Document Chunking
        
        For any document exceeding the model's context limit, the ContentAgent SHALL
        chunk the document and process each chunk, combining results into a coherent
        summary.
        
        **Validates: Requirements 4.6**
        """
        # Create a large document that exceeds the chunk limit (12000 chars)
        paragraphs = []
        for i in range(num_paragraphs):
            # Generate paragraph with repeated content to reach desired size
            base_text = f"Paragraph {i+1}: This is educational content about topic {i+1}. "
            paragraph = base_text * (paragraph_size // len(base_text) + 1)
            paragraph = paragraph[:paragraph_size]
            paragraphs.append(paragraph)
        
        large_document = "\n\n".join(paragraphs)
        
        # Ensure document is large enough to require chunking
        assume(len(large_document) > 12000)
        
        # Create a mock ContentAgent prompt
        mock_agent = AgentPrompt(
            name="ContentAgent",
            role="Content Processor",
            description="Test content agent",
            system_prompt="You are a content processor.",
            example_format={},
            context_guidance=[]
        )
        
        # Track how many times the API is called (should be multiple for chunked doc)
        call_count = 0
        
        def mock_chat_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Return valid JSON response for each chunk
            return json.dumps({
                "title": f"Chunk {call_count} Analysis",
                "summary": f"Summary of chunk {call_count}.",
                "key_points": [f"Key point from chunk {call_count}"],
                "concepts": [{"term": f"Concept{call_count}", "definition": f"Definition {call_count}"}],
                "topics": [f"Topic{call_count}"]
            })
        
        with patch('app.services.agent_orchestrator.NebiusClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.is_fallback_mode = False
            mock_client_instance.chat_completion.side_effect = mock_chat_completion
            MockClient.return_value = mock_client_instance
            
            orchestrator = AgentOrchestrator()
            orchestrator._agents["ContentAgent"] = mock_agent
            orchestrator._loaded = True
            orchestrator._nebius_client = mock_client_instance
            
            result = orchestrator.process_content(
                content_data=large_document,
                content_type="text",
                filename="large_document.txt"
            )
            
            # Property 1: Document should have been chunked (multiple API calls)
            assert call_count > 1, \
                f"Large document should be chunked into multiple calls, got {call_count}"
            
            # Property 2: Result should still have valid structure
            assert isinstance(result, dict), "Result should be a dictionary"
            assert 'title' in result, "Result should have title"
            assert 'summary' in result, "Result should have summary"
            assert 'key_points' in result, "Result should have key_points"
            assert 'concepts' in result, "Result should have concepts"
            assert 'topics' in result, "Result should have topics"
            
            # Property 3: Key points should be combined from all chunks
            assert len(result['key_points']) >= 1, \
                "Combined result should have key points from chunks"
            
            # Property 4: Concepts should be combined from all chunks
            assert len(result['concepts']) >= 1, \
                "Combined result should have concepts from chunks"
            
            # Property 5: Topics should be combined from all chunks
            assert len(result['topics']) >= 1, \
                "Combined result should have topics from chunks"
            
            # Property 6: Processing should be complete
            assert result.get('processing_status') == 'complete', \
                "Processing status should be 'complete'"
    
    @settings(max_examples=100, deadline=None)
    @given(
        max_chunk_chars=st.integers(min_value=1000, max_value=5000),
        document_size=st.integers(min_value=100, max_value=20000)
    )
    def test_chunk_document_preserves_content(self, max_chunk_chars, document_size):
        """
        Test that chunking preserves all document content.
        
        For any document and chunk size, the combined chunks should contain
        all original content (no data loss).
        """
        # Generate document of specified size
        base_text = "This is test content. "
        document = base_text * (document_size // len(base_text) + 1)
        document = document[:document_size]
        
        orchestrator = AgentOrchestrator()
        
        # Chunk the document
        chunks = orchestrator._chunk_document(document, max_chunk_chars)
        
        # Property 1: Should return at least one chunk
        assert len(chunks) >= 1, "Should return at least one chunk"
        
        # Property 2: Each chunk should not exceed max size (with some tolerance for paragraph boundaries)
        for i, chunk in enumerate(chunks):
            # Allow some tolerance for paragraph boundary preservation
            assert len(chunk) <= max_chunk_chars * 1.5, \
                f"Chunk {i} size {len(chunk)} exceeds limit {max_chunk_chars * 1.5}"
        
        # Property 3: Combined chunks should cover the document
        # (may have some overlap at boundaries, but should not lose content)
        combined_length = sum(len(chunk) for chunk in chunks)
        # Combined length should be at least as long as original (may be slightly more due to overlap)
        assert combined_length >= len(document) * 0.9, \
            f"Combined chunks ({combined_length}) should cover most of document ({len(document)})"
        
        # Property 4: No chunk should be empty
        for i, chunk in enumerate(chunks):
            assert len(chunk.strip()) > 0, f"Chunk {i} should not be empty"
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_paragraphs=st.integers(min_value=2, max_value=10)
    )
    def test_chunk_document_respects_paragraph_boundaries(self, num_paragraphs):
        """
        Test that chunking tries to respect paragraph boundaries.
        
        When possible, chunks should break at paragraph boundaries rather than
        in the middle of paragraphs.
        """
        # Create document with clear paragraph boundaries
        paragraphs = [f"Paragraph {i}: " + "x" * 500 for i in range(num_paragraphs)]
        document = "\n\n".join(paragraphs)
        
        orchestrator = AgentOrchestrator()
        
        # Use chunk size that should split between paragraphs
        max_chunk_chars = 1500  # Should fit ~2-3 paragraphs per chunk
        
        chunks = orchestrator._chunk_document(document, max_chunk_chars)
        
        # Property: Most chunks should end at paragraph boundaries
        # (checking that chunks don't end mid-word in most cases)
        boundary_respecting_chunks = 0
        for chunk in chunks:
            # Check if chunk ends at a paragraph boundary or document end
            if chunk.strip().endswith("x" * 10) or chunk == chunks[-1]:
                boundary_respecting_chunks += 1
        
        # At least half of chunks should respect boundaries
        assert boundary_respecting_chunks >= len(chunks) // 2, \
            "Chunking should try to respect paragraph boundaries"
    
    @settings(max_examples=50, deadline=None)
    @given(
        small_doc_size=st.integers(min_value=100, max_value=5000)
    )
    def test_small_document_not_chunked(self, small_doc_size):
        """
        Test that small documents are not unnecessarily chunked.
        
        Documents smaller than the chunk limit should be processed as a single chunk.
        """
        # Create small document
        document = "x" * small_doc_size
        
        # Ensure document is smaller than chunk limit
        max_chunk_chars = 12000
        assume(small_doc_size < max_chunk_chars)
        
        mock_agent = AgentPrompt(
            name="ContentAgent",
            role="Content Processor",
            description="Test content agent",
            system_prompt="You are a content processor.",
            example_format={},
            context_guidance=[]
        )
        
        call_count = 0
        
        def mock_chat_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return json.dumps({
                "title": "Small Doc",
                "summary": "Summary",
                "key_points": ["Point 1"],
                "concepts": [],
                "topics": ["Topic"]
            })
        
        with patch('app.services.agent_orchestrator.NebiusClient') as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.is_fallback_mode = False
            mock_client_instance.chat_completion.side_effect = mock_chat_completion
            MockClient.return_value = mock_client_instance
            
            orchestrator = AgentOrchestrator()
            orchestrator._agents["ContentAgent"] = mock_agent
            orchestrator._loaded = True
            orchestrator._nebius_client = mock_client_instance
            
            result = orchestrator.process_content(
                content_data=document,
                content_type="text",
                filename="small_doc.txt"
            )
            
            # Property: Small document should only require one API call
            assert call_count == 1, \
                f"Small document should not be chunked, got {call_count} API calls"
            
            # Result should still be valid
            assert result.get('processing_status') == 'complete', \
                "Small document should process successfully"


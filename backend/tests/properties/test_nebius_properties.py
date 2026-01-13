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

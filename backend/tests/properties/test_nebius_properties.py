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

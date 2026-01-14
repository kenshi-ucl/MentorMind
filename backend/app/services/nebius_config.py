"""Configuration management for Nebius AI integration."""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ModelConfig:
    """Configuration for a specific AI model."""
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    fallback_model_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "ModelConfig":
        """Create ModelConfig from dictionary."""
        return cls(
            model_id=data.get("model_id", ""),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2048),
            top_p=data.get("top_p", 1.0),
            fallback_model_id=data.get("fallback_model_id")
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "model_id": self.model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p
        }
        if self.fallback_model_id:
            result["fallback_model_id"] = self.fallback_model_id
        return result
    
    def get_model_id_with_fallback(self, use_fallback: bool = False) -> str:
        """Get the model ID, using fallback if requested and available."""
        if use_fallback and self.fallback_model_id:
            return self.fallback_model_id
        return self.model_id


@dataclass
class NebiusConfig:
    """Configuration for Nebius AI integration."""
    api_key: Optional[str]
    base_url: str = "https://api.tokenfactory.nebius.com/v1/"
    tutor_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_id="openai/gpt-oss-120b",
        temperature=0.7,
        max_tokens=2048
    ))
    quiz_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_id="openai/gpt-oss-120b",
        temperature=0.3,
        max_tokens=4096
    ))
    content_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_id="openai/gpt-oss-120b",
        temperature=0.5,
        max_tokens=4096
    ))
    vision_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_id="google/gemma-3-27b-it-fast",
        temperature=0.5,
        max_tokens=2048
    ))
    embedding_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_id="intfloat/e5-mistral-7b-instruct"
    ))
    retry_attempts: int = 3
    retry_delay: float = 1.0
    max_retry_delay: float = 30.0
    timeout: float = 30.0
    
    @classmethod
    def from_file(cls, path: str) -> "NebiusConfig":
        """
        Load configuration from JSON file.
        
        Args:
            path: Path to the JSON configuration file.
            
        Returns:
            NebiusConfig instance with loaded settings.
            
        Raises:
            FileNotFoundError: If the config file doesn't exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        nebius_data = data.get("nebius", data)
        models_data = nebius_data.get("models", {})
        retry_data = nebius_data.get("retry", {})
        
        # Load API key from environment variable
        api_key = os.environ.get("NEBIUS_API_KEY")
        
        return cls(
            api_key=api_key,
            base_url=nebius_data.get("base_url", "https://api.tokenfactory.nebius.com/v1/"),
            tutor_model=ModelConfig.from_dict(models_data.get("tutor", {})) if models_data.get("tutor") else cls._default_tutor_model(),
            quiz_model=ModelConfig.from_dict(models_data.get("quiz", {})) if models_data.get("quiz") else cls._default_quiz_model(),
            content_model=ModelConfig.from_dict(models_data.get("content", {})) if models_data.get("content") else cls._default_content_model(),
            vision_model=ModelConfig.from_dict(models_data.get("vision", {})) if models_data.get("vision") else cls._default_vision_model(),
            embedding_model=ModelConfig.from_dict(models_data.get("embedding", {})) if models_data.get("embedding") else cls._default_embedding_model(),
            retry_attempts=retry_data.get("max_attempts", 3),
            retry_delay=retry_data.get("base_delay", 1.0),
            max_retry_delay=retry_data.get("max_delay", 30.0),
            timeout=nebius_data.get("timeout", 30.0)
        )
    
    @classmethod
    def default(cls) -> "NebiusConfig":
        """
        Create default configuration.
        
        Loads API key from NEBIUS_API_KEY environment variable.
        
        Returns:
            NebiusConfig instance with default settings.
        """
        api_key = os.environ.get("NEBIUS_API_KEY")
        
        return cls(
            api_key=api_key,
            tutor_model=cls._default_tutor_model(),
            quiz_model=cls._default_quiz_model(),
            content_model=cls._default_content_model(),
            vision_model=cls._default_vision_model(),
            embedding_model=cls._default_embedding_model()
        )
    
    @staticmethod
    def _default_tutor_model() -> ModelConfig:
        return ModelConfig(
            model_id="openai/gpt-oss-120b",
            temperature=0.7,
            max_tokens=2048,
            fallback_model_id="deepseek-ai/DeepSeek-V3"
        )
    
    @staticmethod
    def _default_quiz_model() -> ModelConfig:
        return ModelConfig(
            model_id="openai/gpt-oss-120b",
            temperature=0.3,
            max_tokens=4096,
            fallback_model_id="deepseek-ai/DeepSeek-V3"
        )
    
    @staticmethod
    def _default_content_model() -> ModelConfig:
        return ModelConfig(
            model_id="openai/gpt-oss-120b",
            temperature=0.5,
            max_tokens=4096,
            fallback_model_id="deepseek-ai/DeepSeek-V3"
        )
    
    @staticmethod
    def _default_vision_model() -> ModelConfig:
        return ModelConfig(
            model_id="google/gemma-3-27b-it-fast",
            temperature=0.5,
            max_tokens=2048,
            fallback_model_id="google/gemma-3-27b-it"
        )
    
    @staticmethod
    def _default_embedding_model() -> ModelConfig:
        return ModelConfig(
            model_id="intfloat/e5-mistral-7b-instruct",
            fallback_model_id="BAAI/bge-en-icl"
        )
    
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and len(self.api_key) > 0
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "nebius": {
                "base_url": self.base_url,
                "models": {
                    "tutor": self.tutor_model.to_dict(),
                    "quiz": self.quiz_model.to_dict(),
                    "content": self.content_model.to_dict(),
                    "vision": self.vision_model.to_dict(),
                    "embedding": self.embedding_model.to_dict()
                },
                "retry": {
                    "max_attempts": self.retry_attempts,
                    "base_delay": self.retry_delay,
                    "max_delay": self.max_retry_delay
                },
                "timeout": self.timeout
            }
        }

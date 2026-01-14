"""Client for Nebius AI API interactions."""
import base64
import logging
import os
from typing import Generator, Optional, Union

from app.services.nebius_config import NebiusConfig, ModelConfig

logger = logging.getLogger(__name__)


class NebiusClient:
    """Client for Nebius AI API interactions using OpenAI-compatible API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[NebiusConfig] = None
    ):
        """
        Initialize the Nebius client.
        
        Args:
            api_key: Nebius API key. If None, reads from NEBIUS_API_KEY env var.
            config: Nebius configuration. Uses defaults if None.
        """
        self._config = config or NebiusConfig.default()
        
        # Override API key if provided directly
        if api_key is not None:
            self._config.api_key = api_key
        
        self._client = None
        self._fallback_mode = False
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the OpenAI client for Nebius API."""
        if not self._config.has_api_key():
            logger.warning(
                "NEBIUS_API_KEY not configured. Running in fallback mode with placeholder responses. "
                "To enable real AI responses, set the NEBIUS_API_KEY environment variable."
            )
            self._fallback_mode = True
            self._fallback_reason = "missing_api_key"
            return
        
        try:
            from openai import OpenAI
            
            self._client = OpenAI(
                api_key=self._config.api_key,
                base_url=self._config.base_url
            )
            self._fallback_mode = False
            self._fallback_reason = None
            logger.info("Nebius client initialized successfully")
        except ImportError:
            logger.error(
                "OpenAI package not installed. Running in fallback mode. "
                "Install with: pip install openai"
            )
            self._fallback_mode = True
            self._fallback_reason = "missing_openai_package"
        except Exception as e:
            logger.error(f"Failed to initialize Nebius client: {e}. Running in fallback mode.")
            self._fallback_mode = True
            self._fallback_reason = f"initialization_error: {str(e)}"
    
    @property
    def is_fallback_mode(self) -> bool:
        """Check if client is running in fallback mode."""
        return self._fallback_mode
    
    @property
    def fallback_reason(self) -> Optional[str]:
        """Get the reason for fallback mode, if applicable."""
        return getattr(self, '_fallback_reason', None)
    
    @property
    def config(self) -> NebiusConfig:
        """Get the current configuration."""
        return self._config
    
    def chat_completion(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        use_fallback: bool = False
    ) -> Union[str, Generator[str, None, None]]:
        """
        Generate a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Model identifier. Uses tutor_model from config if None.
            temperature: Sampling temperature (0-2). Uses config default if None.
            max_tokens: Maximum tokens to generate. Uses config default if None.
            stream: Whether to stream the response.
            use_fallback: Whether to use the fallback model.
            
        Returns:
            Generated text or generator for streaming.
        """
        if self._fallback_mode:
            return self._fallback_chat_response(messages, stream)
        
        model_config = self._config.tutor_model
        
        # Determine which model to use
        if model is None:
            model = model_config.get_model_id_with_fallback(use_fallback)
        
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature if temperature is not None else model_config.temperature,
                max_tokens=max_tokens if max_tokens is not None else model_config.max_tokens,
                stream=stream
            )
            
            if stream:
                return self._stream_response(response)
            else:
                return response.choices[0].message.content or ""
                
        except Exception as e:
            # If primary model fails and we haven't tried fallback yet, try fallback
            if not use_fallback and model_config.fallback_model_id:
                logger.warning(
                    f"Primary model '{model}' failed: {e}. "
                    f"Trying fallback model '{model_config.fallback_model_id}'"
                )
                return self.chat_completion(
                    messages=messages,
                    model=model_config.fallback_model_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    use_fallback=True
                )
            logger.error(f"Chat completion failed: {e}")
            raise
    
    def _stream_response(self, response) -> Generator[str, None, None]:
        """Stream response chunks."""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _fallback_chat_response(
        self,
        messages: list[dict],
        stream: bool
    ) -> Union[str, Generator[str, None, None]]:
        """Generate fallback response when API is unavailable."""
        user_message = ""
        has_context = False
        
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
            # Check if there's a context message
            if "Content Context:" in msg.get("content", ""):
                has_context = True
        
        # Log warning about fallback mode
        logger.warning(
            f"Returning fallback chat response. Reason: {self._fallback_reason}. "
            f"User message preview: '{user_message[:50]}...'"
        )
        
        if has_context:
            fallback_text = (
                f"⚠️ **Fallback Mode Active**\n\n"
                f"I received your message: \"{user_message[:100]}{'...' if len(user_message) > 100 else ''}\"\n\n"
                "I have context from your uploaded content, but the AI service is currently unavailable.\n\n"
                "**To enable real AI responses:**\n"
                "1. Set the `NEBIUS_API_KEY` environment variable\n"
                "2. Restart the backend server\n\n"
                "_This is a placeholder response._"
            )
        else:
            fallback_text = (
                f"⚠️ **Fallback Mode Active**\n\n"
                f"I received your message: \"{user_message[:100]}{'...' if len(user_message) > 100 else ''}\"\n\n"
                "The AI service is currently unavailable.\n\n"
                "**To enable real AI responses:**\n"
                "1. Set the `NEBIUS_API_KEY` environment variable\n"
                "2. Restart the backend server\n\n"
                "_This is a placeholder response._"
            )
        
        if stream:
            def stream_fallback():
                # Stream word by word for a more natural feel
                words = fallback_text.split(' ')
                for i, word in enumerate(words):
                    yield word + (' ' if i < len(words) - 1 else '')
            return stream_fallback()
        
        return fallback_text
    
    def vision_completion(
        self,
        prompt: str,
        image_data: Union[bytes, str],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_fallback: bool = False
    ) -> str:
        """
        Generate a completion with image input.
        
        Args:
            prompt: Text prompt describing what to analyze.
            image_data: Base64 encoded image string or raw bytes.
            model: Vision model identifier. Uses vision_model from config if None.
            temperature: Sampling temperature. Uses config default if None.
            max_tokens: Maximum tokens. Uses config default if None.
            use_fallback: Whether to use the fallback model.
            
        Returns:
            Generated analysis text.
        """
        if self._fallback_mode:
            return self._fallback_vision_response(prompt)
        
        model_config = self._config.vision_model
        
        # Determine which model to use
        if model is None:
            model = model_config.get_model_id_with_fallback(use_fallback)
        
        # Convert bytes to base64 if needed
        if isinstance(image_data, bytes):
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        else:
            image_base64 = image_data
        
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=temperature if temperature is not None else model_config.temperature,
                max_tokens=max_tokens if max_tokens is not None else model_config.max_tokens
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            # If primary model fails and we haven't tried fallback yet, try fallback
            if not use_fallback and model_config.fallback_model_id:
                logger.warning(
                    f"Primary vision model '{model}' failed: {e}. "
                    f"Trying fallback model '{model_config.fallback_model_id}'"
                )
                return self.vision_completion(
                    prompt=prompt,
                    image_data=image_data,
                    model=model_config.fallback_model_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    use_fallback=True
                )
            logger.error(f"Vision completion failed: {e}")
            raise
    
    def _fallback_vision_response(self, prompt: str) -> str:
        """Generate fallback response for vision requests."""
        logger.warning(
            f"Returning fallback vision response. Reason: {self._fallback_reason}. "
            f"Prompt preview: '{prompt[:50]}...'"
        )
        return (
            f"⚠️ **Fallback Mode Active**\n\n"
            f"Vision analysis requested with prompt: \"{prompt[:100]}{'...' if len(prompt) > 100 else ''}\"\n\n"
            "The AI vision service is currently unavailable.\n\n"
            "**To enable real AI vision analysis:**\n"
            "1. Set the `NEBIUS_API_KEY` environment variable\n"
            "2. Restart the backend server\n\n"
            "_This is a placeholder response._"
        )
    
    def create_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        use_fallback: bool = False
    ) -> list[float]:
        """
        Create an embedding vector for text.
        
        Args:
            text: Text to embed.
            model: Embedding model identifier. Uses embedding_model from config if None.
            use_fallback: Whether to use the fallback model.
            
        Returns:
            Embedding vector (dimensions depend on model).
        """
        if self._fallback_mode:
            return self._fallback_embedding()
        
        model_config = self._config.embedding_model
        
        # Determine which model to use
        if model is None:
            model = model_config.get_model_id_with_fallback(use_fallback)
        
        try:
            response = self._client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            # If primary model fails and we haven't tried fallback yet, try fallback
            if not use_fallback and model_config.fallback_model_id:
                logger.warning(
                    f"Primary embedding model '{model}' failed: {e}. "
                    f"Trying fallback model '{model_config.fallback_model_id}'"
                )
                return self.create_embedding(
                    text=text,
                    model=model_config.fallback_model_id,
                    use_fallback=True
                )
            logger.error(f"Embedding creation failed: {e}")
            raise
    
    def _fallback_embedding(self) -> list[float]:
        """Generate fallback embedding when API is unavailable."""
        logger.warning(
            f"Returning fallback embedding (zero vector). Reason: {self._fallback_reason}"
        )
        # Return a zero vector of typical embedding size
        return [0.0] * 4096

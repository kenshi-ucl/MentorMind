"""Retry handler with exponential backoff for Nebius API calls.

Handles retries for:
- Timeout errors
- Rate limit errors (429)
- Server errors (5xx)

Does not retry:
- Client errors (4xx except 429)
- Invalid API key errors
"""
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryableError(Exception):
    """Base exception for errors that can be retried."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class TimeoutError(RetryableError):
    """Raised when an API call times out."""
    pass


class RateLimitError(RetryableError):
    """Raised when rate limit is exceeded (429)."""
    pass


class ServerError(RetryableError):
    """Raised for server errors (5xx)."""
    pass


class ClientError(Exception):
    """Raised for client errors (4xx except 429). Not retryable."""
    
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(ClientError):
    """Raised for authentication failures (401). Not retryable."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class RetryHandler:
    """Handles API call retries with exponential backoff.
    
    Implements exponential backoff with jitter for resilient API calls.
    Retries on timeout, rate limit (429), and server errors (5xx).
    Does not retry on client errors (4xx except 429).
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize the retry handler.
        
        Args:
            max_attempts: Maximum number of retry attempts (default 3).
            base_delay: Initial delay between retries in seconds (default 1.0).
            max_delay: Maximum delay between retries in seconds (default 30.0).
            exponential_base: Base for exponential backoff calculation (default 2.0).
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def calculate_delay(self, attempt: int, retry_after: Optional[int] = None) -> float:
        """
        Calculate delay before next retry using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-indexed).
            retry_after: Optional server-specified retry delay in seconds.
            
        Returns:
            Delay in seconds before next retry.
        """
        if retry_after is not None and retry_after > 0:
            # Respect server-specified retry-after, but cap at max_delay
            return min(float(retry_after), self.max_delay)
        
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # Cap at max_delay
        return min(delay, self.max_delay)
    
    def should_retry(self, error: Exception) -> bool:
        """
        Determine if an error should trigger a retry.
        
        Args:
            error: The exception that occurred.
            
        Returns:
            True if the error is retryable, False otherwise.
        """
        # Retryable errors
        if isinstance(error, (TimeoutError, RateLimitError, ServerError)):
            return True
        
        # Check for OpenAI SDK specific errors
        try:
            from openai import APITimeoutError, RateLimitError as OpenAIRateLimitError
            from openai import APIStatusError
            
            if isinstance(error, APITimeoutError):
                return True
            
            if isinstance(error, OpenAIRateLimitError):
                return True
            
            if isinstance(error, APIStatusError):
                # Retry on 5xx server errors
                if hasattr(error, 'status_code') and 500 <= error.status_code < 600:
                    return True
                # Retry on 429 rate limit
                if hasattr(error, 'status_code') and error.status_code == 429:
                    return True
                
        except ImportError:
            pass
        
        # Non-retryable
        if isinstance(error, (ClientError, AuthenticationError)):
            return False
        
        return False
    
    def get_retry_after(self, error: Exception) -> Optional[int]:
        """
        Extract retry-after value from error if available.
        
        Args:
            error: The exception that occurred.
            
        Returns:
            Retry-after value in seconds, or None if not available.
        """
        if isinstance(error, RetryableError) and error.retry_after is not None:
            return error.retry_after
        
        # Check for OpenAI SDK specific errors with headers
        try:
            from openai import APIStatusError
            
            if isinstance(error, APIStatusError):
                if hasattr(error, 'response') and error.response is not None:
                    retry_after = error.response.headers.get('retry-after')
                    if retry_after:
                        try:
                            return int(retry_after)
                        except ValueError:
                            pass
        except ImportError:
            pass
        
        return None
    
    def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Execute a function with retry logic.
        
        Retries on:
        - Timeout errors
        - Rate limit errors (429)
        - Server errors (5xx)
        
        Does not retry on:
        - Client errors (4xx except 429)
        - Invalid API key (401)
        
        Args:
            func: The function to execute.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
            
        Returns:
            The result of the function call.
            
        Raises:
            The last exception if all retries fail.
        """
        last_error: Optional[Exception] = None
        
        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                last_error = e
                
                # Check if we should retry
                if not self.should_retry(e):
                    logger.warning(
                        f"Non-retryable error on attempt {attempt + 1}: {type(e).__name__}: {e}"
                    )
                    raise
                
                # Check if we have more attempts
                if attempt + 1 >= self.max_attempts:
                    logger.error(
                        f"All {self.max_attempts} retry attempts exhausted. "
                        f"Last error: {type(e).__name__}: {e}"
                    )
                    raise
                
                # Calculate delay
                retry_after = self.get_retry_after(e)
                delay = self.calculate_delay(attempt, retry_after)
                
                logger.warning(
                    f"Retryable error on attempt {attempt + 1}/{self.max_attempts}: "
                    f"{type(e).__name__}: {e}. Retrying in {delay:.2f}s..."
                )
                
                time.sleep(delay)
        
        # This should never be reached, but just in case
        if last_error is not None:
            raise last_error
        
        raise RuntimeError("Unexpected state in retry handler")



@dataclass
class AIErrorResponse:
    """Standardized error response from AI operations.
    
    Provides a consistent structure for error responses that separates
    user-facing messages from technical details for logging.
    
    Attributes:
        success: Always False for error responses.
        error_type: Category of error ("config", "network", "api", "response", "timeout", "rate_limit").
        user_message: Safe message to display to the user.
        technical_details: Detailed error info for logging (not shown to users).
        retry_after: Seconds to wait before retry (if applicable).
    """
    success: bool = False
    error_type: str = "unknown"
    user_message: str = "An unexpected error occurred. Please try again later."
    technical_details: Optional[str] = None
    retry_after: Optional[int] = None
    
    @classmethod
    def from_exception(cls, error: Exception) -> "AIErrorResponse":
        """
        Create an AIErrorResponse from an exception.
        
        Maps different exception types to appropriate user messages
        while preserving technical details for logging.
        
        Args:
            error: The exception to convert.
            
        Returns:
            AIErrorResponse with appropriate error categorization.
        """
        technical_details = f"{type(error).__name__}: {str(error)}"
        
        # Handle our custom exceptions
        if isinstance(error, TimeoutError):
            return cls(
                error_type="timeout",
                user_message="The AI service is taking too long to respond. Please try again.",
                technical_details=technical_details,
                retry_after=error.retry_after
            )
        
        if isinstance(error, RateLimitError):
            retry_msg = ""
            if error.retry_after:
                retry_msg = f" Please wait {error.retry_after} seconds before trying again."
            return cls(
                error_type="rate_limit",
                user_message=f"The AI service is currently busy.{retry_msg}",
                technical_details=technical_details,
                retry_after=error.retry_after
            )
        
        if isinstance(error, ServerError):
            return cls(
                error_type="api",
                user_message="The AI service is temporarily unavailable. Please try again later.",
                technical_details=technical_details,
                retry_after=error.retry_after
            )
        
        if isinstance(error, AuthenticationError):
            return cls(
                error_type="config",
                user_message="AI service configuration error. Please contact support.",
                technical_details=technical_details
            )
        
        if isinstance(error, ClientError):
            return cls(
                error_type="api",
                user_message="There was a problem with the request. Please try again.",
                technical_details=technical_details
            )
        
        # Handle OpenAI SDK specific errors
        try:
            from openai import APITimeoutError, RateLimitError as OpenAIRateLimitError
            from openai import APIStatusError, AuthenticationError as OpenAIAuthError
            
            if isinstance(error, APITimeoutError):
                return cls(
                    error_type="timeout",
                    user_message="The AI service is taking too long to respond. Please try again.",
                    technical_details=technical_details
                )
            
            if isinstance(error, OpenAIRateLimitError):
                retry_after = None
                if hasattr(error, 'response') and error.response:
                    retry_header = error.response.headers.get('retry-after')
                    if retry_header:
                        try:
                            retry_after = int(retry_header)
                        except ValueError:
                            pass
                
                retry_msg = ""
                if retry_after:
                    retry_msg = f" Please wait {retry_after} seconds before trying again."
                
                return cls(
                    error_type="rate_limit",
                    user_message=f"The AI service is currently busy.{retry_msg}",
                    technical_details=technical_details,
                    retry_after=retry_after
                )
            
            if isinstance(error, OpenAIAuthError):
                return cls(
                    error_type="config",
                    user_message="AI service configuration error. Please contact support.",
                    technical_details=technical_details
                )
            
            if isinstance(error, APIStatusError):
                status_code = getattr(error, 'status_code', 0)
                
                if 500 <= status_code < 600:
                    return cls(
                        error_type="api",
                        user_message="The AI service is temporarily unavailable. Please try again later.",
                        technical_details=technical_details
                    )
                
                return cls(
                    error_type="api",
                    user_message="There was a problem with the AI service. Please try again.",
                    technical_details=technical_details
                )
                
        except ImportError:
            pass
        
        # Handle network errors
        if isinstance(error, (ConnectionError, OSError)):
            return cls(
                error_type="network",
                user_message="Unable to connect to the AI service. Please check your connection.",
                technical_details=technical_details
            )
        
        # Default fallback
        return cls(
            error_type="unknown",
            user_message="An unexpected error occurred. Please try again later.",
            technical_details=technical_details
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "success": self.success,
            "error_type": self.error_type,
            "user_message": self.user_message
        }
        
        if self.retry_after is not None:
            result["retry_after"] = self.retry_after
        
        return result
    
    def log_error(self, logger_instance: Optional[logging.Logger] = None) -> None:
        """
        Log the error with technical details.
        
        Args:
            logger_instance: Logger to use. Uses module logger if None.
        """
        log = logger_instance or logger
        log.error(
            f"AI Error [{self.error_type}]: {self.user_message} | "
            f"Details: {self.technical_details}"
        )

# Design Document: Nebius AI Integration

## Overview

This design describes the integration of Nebius AI API into MentorMind to replace placeholder AI responses with real AI-powered functionality. The integration uses the OpenAI-compatible API provided by Nebius Token Factory, enabling seamless integration with the existing agent architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AgentOrchestrator                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   NebiusClient                            │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │  │
│  │  │ Text Model  │ │ Vision Model│ │ Embedding Model     │ │  │
│  │  │ gpt-oss-120b│ │ Gemma-3-27b │ │ e5-mistral-7b       │ │  │
│  │  └──────┬──────┘ └──────┬──────┘ └──────────┬──────────┘ │  │
│  │         │               │                    │            │  │
│  │         └───────────────┴────────────────────┘            │  │
│  │                         │                                  │  │
│  │              ┌──────────▼──────────┐                      │  │
│  │              │   Nebius API        │                      │  │
│  │              │ api.tokenfactory.   │                      │  │
│  │              │ nebius.com/v1/      │                      │  │
│  │              └─────────────────────┘                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │TutorAgent  │  │ QuizAgent  │  │ContentAgent│                │
│  │(Text Model)│  │(Text Model)│  │(Vision+Text)│               │
│  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### NebiusClient

Central client for all Nebius API interactions.

```python
class NebiusClient:
    """Client for Nebius AI API interactions."""
    
    def __init__(self, api_key: str | None = None):
        """
        Initialize the Nebius client.
        
        Args:
            api_key: Nebius API key. If None, reads from NEBIUS_API_KEY env var.
        """
        pass
    
    def chat_completion(
        self,
        messages: list[dict],
        model: str = "openai/gpt-oss-120b",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> str | Generator[str, None, None]:
        """
        Generate a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Model identifier.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream the response.
            
        Returns:
            Generated text or generator for streaming.
        """
        pass
    
    def vision_completion(
        self,
        prompt: str,
        image_data: bytes | str,
        model: str = "google/gemma-3-27b-it-fast"
    ) -> str:
        """
        Generate a completion with image input.
        
        Args:
            prompt: Text prompt describing what to analyze.
            image_data: Base64 encoded image or raw bytes.
            model: Vision model identifier.
            
        Returns:
            Generated analysis text.
        """
        pass
    
    def create_embedding(
        self,
        text: str,
        model: str = "intfloat/e5-mistral-7b-instruct"
    ) -> list[float]:
        """
        Create an embedding vector for text.
        
        Args:
            text: Text to embed.
            model: Embedding model identifier.
            
        Returns:
            Embedding vector (4096 dimensions).
        """
        pass
```

### NebiusConfig

Configuration management for model selection and parameters.

```python
@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0

@dataclass
class NebiusConfig:
    """Configuration for Nebius AI integration."""
    api_key: str | None
    base_url: str = "https://api.tokenfactory.nebius.com/v1/"
    tutor_model: ModelConfig
    quiz_model: ModelConfig
    content_model: ModelConfig
    vision_model: ModelConfig
    embedding_model: ModelConfig
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    
    @classmethod
    def from_file(cls, path: str) -> "NebiusConfig":
        """Load configuration from JSON file."""
        pass
    
    @classmethod
    def default(cls) -> "NebiusConfig":
        """Create default configuration."""
        pass
```

### Updated AgentOrchestrator

Enhanced orchestrator with real AI integration.

```python
class AgentOrchestrator:
    """Service for orchestrating AI agent operations with Nebius integration."""
    
    def __init__(
        self,
        prompts_dir: str | None = None,
        config: NebiusConfig | None = None
    ):
        """
        Initialize the orchestrator.
        
        Args:
            prompts_dir: Path to agent prompt JSON files.
            config: Nebius configuration. Uses defaults if None.
        """
        pass
    
    def process_chat(
        self,
        message: str,
        context: list[str] | None = None,
        stream: bool = False
    ) -> str | Generator[str, None, None]:
        """
        Process a chat message through TutorAgent with real AI.
        
        Args:
            message: User's message.
            context: Optional content context.
            stream: Whether to stream the response.
            
        Returns:
            AI-generated response or stream generator.
        """
        pass
    
    def generate_quiz(
        self,
        topic: str | None = None,
        content: str | None = None,
        question_count: int = 5
    ) -> list[dict]:
        """
        Generate quiz questions using QuizAgent with real AI.
        
        Args:
            topic: Quiz topic.
            content: Content to base questions on.
            question_count: Number of questions.
            
        Returns:
            List of question dictionaries with validated structure.
        """
        pass
    
    def process_content(
        self,
        content_data: bytes | str,
        content_type: str,
        filename: str
    ) -> dict:
        """
        Process uploaded content using ContentAgent with real AI.
        
        Args:
            content_data: Raw content data.
            content_type: MIME type or file extension.
            filename: Original filename.
            
        Returns:
            Extracted information dictionary.
        """
        pass
```

### RetryHandler

Handles retries with exponential backoff.

```python
class RetryHandler:
    """Handles API call retries with exponential backoff."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0
    ):
        pass
    
    def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Retries on:
        - Timeout errors
        - Rate limit errors (429)
        - Server errors (5xx)
        
        Does not retry on:
        - Client errors (4xx except 429)
        - Invalid API key
        """
        pass
```

## Data Models

### Quiz Question Structure

```python
@dataclass
class QuizQuestion:
    """Structure for AI-generated quiz questions."""
    id: str
    question: str
    options: list[str]  # Exactly 4 options
    correct_index: int  # 0-3
    explanation: str
    
    def validate(self) -> bool:
        """Validate question structure."""
        return (
            len(self.options) == 4 and
            0 <= self.correct_index < 4 and
            len(set(self.options)) == 4  # All options distinct
        )
```

### Content Extraction Result

```python
@dataclass
class ContentExtraction:
    """Structure for extracted content information."""
    title: str
    summary: str
    key_points: list[str]
    concepts: list[dict]  # {"term": str, "definition": str}
    topics: list[str]
    source_type: str  # "pdf", "image", "video"
    processing_status: str  # "complete", "partial", "failed"
    error_message: str | None = None
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: API Configuration Loading

*For any* valid API key string set in the NEBIUS_API_KEY environment variable, the NebiusClient SHALL correctly load and use that key for authentication.

**Validates: Requirements 1.1**

### Property 2: Fallback on Missing API Key

*For any* system state where NEBIUS_API_KEY is not set, the AgentOrchestrator SHALL return placeholder responses without throwing exceptions.

**Validates: Requirements 1.2**

### Property 3: Chat Message API Call Construction

*For any* user message and optional content context, the TutorAgent SHALL construct a valid API request that includes the system prompt, context (if provided), and user message in the correct message format.

**Validates: Requirements 2.1, 2.2, 2.6**

### Property 4: API Error Graceful Handling

*For any* API failure (timeout, rate limit, server error), the system SHALL return a user-friendly error message without exposing internal details or crashing.

**Validates: Requirements 2.4, 5.4, 5.5**

### Property 5: Quiz Structure Validity

*For any* quiz generation request with a specified question count N, the QuizAgent SHALL return exactly N questions, each with exactly 4 distinct options, a valid correct_index (0-3), and non-empty explanation.

**Validates: Requirements 3.1, 3.2, 3.6**

### Property 6: Quiz JSON Round-Trip

*For any* valid quiz question structure, serializing to JSON and parsing back SHALL produce an equivalent structure.

**Validates: Requirements 3.2**

### Property 7: Content Processing Output Structure

*For any* successfully processed content (PDF, image, or video), the ContentAgent SHALL return a result containing all required fields: title, summary, key_points (non-empty list), concepts, topics, and source_type.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 8: Large Document Chunking

*For any* document exceeding the model's context limit, the ContentAgent SHALL chunk the document and process each chunk, combining results into a coherent summary.

**Validates: Requirements 4.6**

### Property 9: Retry on Timeout

*For any* API call that times out, the RetryHandler SHALL retry up to the configured maximum attempts (default 3) with exponential backoff before returning an error.

**Validates: Requirements 5.1**

### Property 10: Quiz Options Distinctness

*For any* generated quiz question, all four answer options SHALL be distinct strings (no duplicates).

**Validates: Requirements 7.2**

## Error Handling

### Error Categories

1. **Configuration Errors**
   - Missing API key → Fall back to placeholder mode
   - Invalid configuration file → Use defaults with warning

2. **Network Errors**
   - Timeout → Retry with exponential backoff
   - Connection refused → Retry then graceful error

3. **API Errors**
   - 401 Unauthorized → Log error, return "AI service configuration error"
   - 429 Rate Limited → Queue request, inform user of delay
   - 500+ Server Error → Retry then graceful error

4. **Response Errors**
   - Invalid JSON from quiz generation → Retry with stricter prompt
   - Incomplete response → Return partial result with warning

### Error Response Format

```python
@dataclass
class AIErrorResponse:
    """Standardized error response from AI operations."""
    success: bool = False
    error_type: str  # "config", "network", "api", "response"
    user_message: str  # Safe to show to user
    technical_details: str | None = None  # For logging only
    retry_after: int | None = None  # Seconds to wait before retry
```

## Testing Strategy

### Unit Tests

- Test configuration loading from environment and file
- Test message construction for each agent type
- Test error response parsing
- Test retry logic with mocked failures

### Property-Based Tests

Using Hypothesis for Python:

1. **Configuration Property Test**: Generate random API key strings, verify they're correctly loaded
2. **Quiz Structure Property Test**: Generate quiz requests, verify output structure validity
3. **Error Handling Property Test**: Generate various error scenarios, verify graceful handling
4. **Chunking Property Test**: Generate large documents, verify chunking occurs correctly

### Integration Tests

- Test actual API calls with test API key (if available)
- Test end-to-end flow: upload content → generate quiz → answer questions

### Test Configuration

```python
# Property test settings
HYPOTHESIS_SETTINGS = {
    "max_examples": 100,
    "deadline": None,  # AI calls can be slow
}
```

## Configuration File Format

```json
{
  "nebius": {
    "base_url": "https://api.tokenfactory.nebius.com/v1/",
    "models": {
      "tutor": {
        "model_id": "openai/gpt-oss-120b",
        "temperature": 0.7,
        "max_tokens": 2048
      },
      "quiz": {
        "model_id": "openai/gpt-oss-120b",
        "temperature": 0.3,
        "max_tokens": 4096
      },
      "content": {
        "model_id": "openai/gpt-oss-120b",
        "temperature": 0.5,
        "max_tokens": 4096
      },
      "vision": {
        "model_id": "google/gemma-3-27b-it-fast",
        "temperature": 0.5,
        "max_tokens": 2048
      },
      "embedding": {
        "model_id": "intfloat/e5-mistral-7b-instruct"
      }
    },
    "retry": {
      "max_attempts": 3,
      "base_delay": 1.0,
      "max_delay": 30.0
    },
    "timeout": 30.0
  }
}
```

## Implementation Notes

1. **OpenAI Compatibility**: Nebius uses OpenAI-compatible API, so we use the `openai` Python package with custom base_url.

2. **Streaming**: For better UX, TutorAgent responses should stream to show progress.

3. **JSON Mode**: For QuizAgent, use structured output prompting to ensure valid JSON.

4. **Vision Input**: Images must be base64 encoded for the vision model API.

5. **Rate Limiting**: Nebius has per-model rate limits; implement client-side tracking.

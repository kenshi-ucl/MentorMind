# Requirements Document

## Introduction

This feature integrates Nebius AI API into MentorMind to replace placeholder AI responses with real AI-powered functionality. The integration covers three AI capabilities: text-to-text generation for tutoring and quiz generation, embeddings for content understanding, and vision models for processing uploaded images and documents.

## Glossary

- **Nebius_API**: The Nebius AI inference API providing access to various AI models
- **Text_Model**: Nebius text-to-text model (e.g., gpt-oss-120b, DeepSeek-V3) for generating tutoring responses and quizzes
- **Embedding_Model**: Nebius embedding model (e.g., e5-mistral-7b-instruct) for semantic understanding of content
- **Vision_Model**: Nebius vision model (e.g., Gemma-3-27b-it) for processing images and visual content
- **API_Key**: Secret credential for authenticating with Nebius API
- **Token_Factory**: Nebius API endpoint base URL (api.tokenfactory.nebius.com)
- **TutorAgent**: AI agent using Text_Model to answer questions and explain concepts
- **QuizAgent**: AI agent using Text_Model to generate quiz questions
- **ContentAgent**: AI agent using Vision_Model and Text_Model to extract information from uploaded content
- **Rate_Limiter**: Component that manages API request frequency to avoid exceeding limits

## Requirements

### Requirement 1: Nebius API Configuration

**User Story:** As a developer, I want to configure Nebius API credentials securely, so that the application can authenticate with Nebius services.

#### Acceptance Criteria

1. THE MentorMind_System SHALL load the Nebius API key from the NEBIUS_API_KEY environment variable
2. WHEN the API key is not configured THEN THE MentorMind_System SHALL log a warning and fall back to placeholder responses
3. THE MentorMind_System SHALL use "https://api.tokenfactory.nebius.com/v1/" as the base URL for all Nebius API calls
4. THE MentorMind_System SHALL store model configuration (model names, parameters) in a configuration file for easy updates

### Requirement 2: TutorAgent Real AI Integration

**User Story:** As a learner, I want to receive intelligent, contextual responses from the AI tutor, so that I can get meaningful help with my questions.

#### Acceptance Criteria

1. WHEN a user sends a message to TutorAgent THEN THE Text_Model SHALL generate a contextual response based on the system prompt and user message
2. WHEN content context is provided THEN THE TutorAgent SHALL include the context in the prompt to provide content-aware responses
3. WHEN the user requests simplification THEN THE TutorAgent SHALL generate a simpler explanation using appropriate prompt engineering
4. IF the Nebius API call fails THEN THE TutorAgent SHALL return a user-friendly error message and log the error details
5. THE TutorAgent SHALL use streaming responses to provide faster perceived response times
6. WHEN generating responses THEN THE TutorAgent SHALL respect the configured temperature and max_tokens parameters

### Requirement 3: QuizAgent Real AI Integration

**User Story:** As a learner, I want AI-generated quizzes with meaningful questions, so that I can effectively test my understanding.

#### Acceptance Criteria

1. WHEN a quiz is requested THEN THE QuizAgent SHALL generate questions using the Text_Model with structured output format
2. THE QuizAgent SHALL generate questions in valid JSON format with question, options, correct_index, and explanation fields
3. WHEN a topic is provided THEN THE QuizAgent SHALL generate questions specifically about that topic
4. WHEN content context is provided THEN THE QuizAgent SHALL generate questions based on the uploaded content
5. IF the generated response is not valid JSON THEN THE QuizAgent SHALL retry with a more explicit format instruction
6. THE QuizAgent SHALL generate the requested number of questions (default 5, configurable)

### Requirement 4: ContentAgent Real AI Integration

**User Story:** As a learner, I want the AI to intelligently extract key information from my uploaded materials, so that I can learn from them effectively.

#### Acceptance Criteria

1. WHEN a PDF is uploaded THEN THE ContentAgent SHALL extract text and use the Text_Model to summarize key points
2. WHEN an image is uploaded THEN THE ContentAgent SHALL use the Vision_Model to analyze and describe the content
3. WHEN a video is uploaded THEN THE ContentAgent SHALL extract frames and use the Vision_Model to understand visual content
4. THE ContentAgent SHALL return structured output with title, summary, key_points, concepts, and topics
5. IF content processing fails THEN THE ContentAgent SHALL return partial results with an error indication
6. THE ContentAgent SHALL handle large documents by chunking and summarizing in parts

### Requirement 5: Error Handling and Resilience

**User Story:** As a user, I want the application to handle AI service issues gracefully, so that my experience is not disrupted.

#### Acceptance Criteria

1. WHEN a Nebius API call times out THEN THE MentorMind_System SHALL retry up to 3 times with exponential backoff
2. WHEN rate limits are exceeded THEN THE MentorMind_System SHALL queue requests and inform the user of the delay
3. IF all retries fail THEN THE MentorMind_System SHALL return a graceful error message suggesting the user try again later
4. THE MentorMind_System SHALL log all API errors with request details for debugging
5. WHEN the API returns an error response THEN THE MentorMind_System SHALL parse the error and provide a meaningful message to the user

### Requirement 6: Model Selection and Configuration

**User Story:** As a developer, I want to easily switch between different Nebius models, so that I can optimize for cost, speed, or quality.

#### Acceptance Criteria

1. THE MentorMind_System SHALL support configuring different models for each agent type (Tutor, Quiz, Content)
2. THE MentorMind_System SHALL allow configuration of model parameters (temperature, max_tokens, top_p) per agent
3. WHEN a configured model is unavailable THEN THE MentorMind_System SHALL fall back to a default model
4. THE configuration SHALL support both "Base" and "Fast" model variants for cost/speed tradeoffs

### Requirement 7: Response Formatting

**User Story:** As a learner, I want AI responses to be well-formatted and readable, so that I can easily understand the information.

#### Acceptance Criteria

1. THE TutorAgent SHALL format responses with proper markdown for code blocks, lists, and emphasis
2. THE QuizAgent SHALL ensure all generated options are distinct and plausible
3. THE ContentAgent SHALL organize extracted information in a clear hierarchical structure
4. WHEN the AI generates code examples THEN THE MentorMind_System SHALL properly escape and format them for display


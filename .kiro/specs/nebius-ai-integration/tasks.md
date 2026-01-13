# Implementation Plan: Nebius AI Integration

## Overview

This implementation plan integrates Nebius AI API into MentorMind, replacing placeholder responses with real AI-powered functionality. The implementation uses Python with the OpenAI SDK (Nebius-compatible) and Hypothesis for property-based testing.

## Tasks

- [x] 1. Set up Nebius client infrastructure
  - [x] 1.1 Create NebiusConfig dataclass and configuration loader
    - Create `backend/app/services/nebius_config.py`
    - Implement ModelConfig and NebiusConfig dataclasses
    - Add `from_file()` and `default()` class methods
    - Load API key from NEBIUS_API_KEY environment variable
    - _Requirements: 1.1, 1.4, 6.1, 6.2_
  - [x] 1.2 Create Nebius AI configuration JSON file
    - Create `backend/config/nebius.json` with model configurations
    - Configure tutor, quiz, content, vision, and embedding models
    - Set default parameters (temperature, max_tokens)
    - _Requirements: 1.3, 1.4, 6.4_
  - [x] 1.3 Create NebiusClient class
    - Create `backend/app/services/nebius_client.py`
    - Implement `chat_completion()` method using OpenAI SDK
    - Implement `vision_completion()` method for image analysis
    - Implement `create_embedding()` method
    - Handle API key validation and fallback mode
    - _Requirements: 1.1, 1.2, 1.3_
  - [x] 1.4 Write property test for API configuration loading
    - **Property 1: API Configuration Loading**
    - **Validates: Requirements 1.1**

- [x] 2. Implement retry and error handling
  - [x] 2.1 Create RetryHandler class
    - Create `backend/app/services/retry_handler.py`
    - Implement exponential backoff logic
    - Handle timeout, rate limit (429), and server errors (5xx)
    - Skip retry for client errors (4xx except 429)
    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 2.2 Create AIErrorResponse dataclass
    - Define standardized error response structure
    - Include user_message, technical_details, retry_after fields
    - _Requirements: 5.4, 5.5_
  - [x] 2.3 Write property test for retry on timeout
    - **Property 9: Retry on Timeout**
    - **Validates: Requirements 5.1**
  - [x] 2.4 Write property test for graceful error handling
    - **Property 4: API Error Graceful Handling**
    - **Validates: Requirements 2.4, 5.4, 5.5**

- [x] 3. Checkpoint - Verify infrastructure
  - Ensure configuration loads correctly
  - Verify retry logic works with mocked failures
  - Ask the user if questions arise

- [ ] 4. Integrate TutorAgent with Nebius
  - [ ] 4.1 Update AgentOrchestrator.process_chat() method
    - Integrate NebiusClient for real AI responses
    - Build messages array with system prompt and context
    - Implement streaming response support
    - Add fallback to placeholder when API unavailable
    - _Requirements: 2.1, 2.2, 2.5, 2.6_
  - [ ] 4.2 Write property test for chat message API call construction
    - **Property 3: Chat Message API Call Construction**
    - **Validates: Requirements 2.1, 2.2, 2.6**
  - [ ] 4.3 Update chat route to support streaming
    - Modify `/api/chat/message` endpoint
    - Add Server-Sent Events (SSE) support for streaming
    - _Requirements: 2.5_

- [ ] 5. Integrate QuizAgent with Nebius
  - [ ] 5.1 Update AgentOrchestrator.generate_quiz() method
    - Integrate NebiusClient for real quiz generation
    - Use structured output prompting for JSON format
    - Implement JSON validation and retry on invalid format
    - _Requirements: 3.1, 3.2, 3.5, 3.6_
  - [ ] 5.2 Write property test for quiz structure validity
    - **Property 5: Quiz Structure Validity**
    - **Validates: Requirements 3.1, 3.2, 3.6**
  - [ ] 5.3 Write property test for quiz JSON round-trip
    - **Property 6: Quiz JSON Round-Trip**
    - **Validates: Requirements 3.2**
  - [ ] 5.4 Write property test for quiz options distinctness
    - **Property 10: Quiz Options Distinctness**
    - **Validates: Requirements 7.2**

- [ ] 6. Checkpoint - Verify TutorAgent and QuizAgent
  - Test chat with real AI responses
  - Test quiz generation produces valid questions
  - Ensure all tests pass
  - Ask the user if questions arise

- [ ] 7. Integrate ContentAgent with Nebius
  - [ ] 7.1 Update AgentOrchestrator.process_content() method
    - Integrate NebiusClient for content analysis
    - Use Text_Model for PDF text summarization
    - Use Vision_Model for image analysis
    - Implement document chunking for large files
    - _Requirements: 4.1, 4.2, 4.6_
  - [ ] 7.2 Add video frame extraction support
    - Extract key frames from uploaded videos
    - Send frames to Vision_Model for analysis
    - Combine frame analyses into summary
    - _Requirements: 4.3_
  - [ ] 7.3 Write property test for content processing output structure
    - **Property 7: Content Processing Output Structure**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
  - [ ] 7.4 Write property test for large document chunking
    - **Property 8: Large Document Chunking**
    - **Validates: Requirements 4.6**

- [ ] 8. Checkpoint - Verify ContentAgent
  - Test PDF upload and summarization
  - Test image upload and analysis
  - Ensure all tests pass
  - Ask the user if questions arise

- [ ] 9. Add fallback mode and final integration
  - [ ] 9.1 Implement placeholder fallback mode
    - Detect when API key is missing
    - Return placeholder responses with warning
    - Log warning about missing configuration
    - _Requirements: 1.2_
  - [ ] 9.2 Write property test for fallback on missing API key
    - **Property 2: Fallback on Missing API Key**
    - **Validates: Requirements 1.2**
  - [ ] 9.3 Update frontend to handle streaming responses
    - Modify ChatInterface to consume SSE stream
    - Show typing indicator during streaming
    - _Requirements: 2.5_
  - [ ] 9.4 Add model fallback configuration
    - Implement fallback model selection when primary unavailable
    - _Requirements: 6.3_

- [ ] 10. Final checkpoint - Complete integration verification
  - Run all property-based tests
  - Test end-to-end flow with real API
  - Verify fallback mode works correctly
  - Ask the user if questions arise

## Notes

- All tasks including property-based tests are required
- Backend uses Python with OpenAI SDK for Nebius API compatibility
- Property tests use Hypothesis library
- API key must be set in NEBIUS_API_KEY environment variable for real AI
- Without API key, system falls back to placeholder responses

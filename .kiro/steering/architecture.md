# MentorMind Architecture

> Steering document for MentorMind AI Tutor — Kiro Hackathon Project

## System Overview

MentorMind is a personal AI tutor application built with a React (Vite) frontend and Flask backend. The system employs three specialized AI agents powered by Nebius AI to provide interactive learning experiences.

## Design Principles

1. **Modular Agents** — AI agent prompts stored in JSON for easy iteration
2. **Spec-Driven Development** — Features defined in `.kiro/specs/` before implementation
3. **Graceful Degradation** — Falls back to placeholders if AI unavailable
4. **Streaming First** — Use streaming responses for better UX
5. **Context Injection** — Uploaded content enhances all agent responses

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React + Vite)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Landing  │ │   Chat   │ │  Quiz    │ │ Progress │           │
│  │  Page    │ │Interface │ │Component │ │Dashboard │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │            │                   │
│  ┌────┴────────────┴────────────┴────────────┴────┐             │
│  │              Context Providers                  │             │
│  │         (AuthContext, ThemeContext)            │             │
│  └────────────────────┬───────────────────────────┘             │
└───────────────────────┼─────────────────────────────────────────┘
                        │ HTTP/REST + Streaming
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (Flask)                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Routes                            │    │
│  │  /auth  │  /chat  │  /content  │  /quiz  │  /progress   │    │
│  └────┬────────┬──────────┬───────────┬──────────┬─────────┘    │
│       │        │          │           │          │               │
│  ┌────┴────┐ ┌─┴──────────┴───────────┴──┐ ┌────┴────┐          │
│  │  Auth   │ │    Agent Orchestrator      │ │Progress │          │
│  │ Service │ │                            │ │ Service │          │
│  └─────────┘ └──────────┬─────────────────┘ └─────────┘          │
│                         │                                        │
│              ┌──────────┼──────────┐                             │
│              ▼          ▼          ▼                             │
│         ┌────────┐ ┌────────┐ ┌────────┐                        │
│         │ Tutor  │ │  Quiz  │ │Content │                        │
│         │ Agent  │ │ Agent  │ │ Agent  │                        │
│         └───┬────┘ └───┬────┘ └───┬────┘                        │
│             │          │          │                              │
│             └──────────┴──────────┘                              │
│                        │                                         │
│                        ▼                                         │
│              ┌─────────────────┐                                 │
│              │  Nebius Client  │                                 │
│              │  (AI API)       │                                 │
│              └─────────────────┘                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
mentormind/
├── .kiro/
│   ├── prompts/           # AI agent prompt configurations
│   │   ├── TutorAgent.json
│   │   ├── QuizAgent.json
│   │   └── ContentAgent.json
│   ├── specs/             # Feature specifications
│   │   ├── mentormind-ai-tutor/
│   │   ├── nebius-ai-integration/
│   │   └── friends-communication/
│   └── steering/          # Architecture documentation
│       └── architecture.md
├── frontend/              # React + Vite application
│   └── src/
│       ├── components/    # UI components
│       │   ├── auth/      # Authentication forms
│       │   ├── chat/      # Chat interface
│       │   ├── content/   # Content upload
│       │   ├── layout/    # Main layout, sidebar
│       │   ├── pages/     # Page views
│       │   ├── progress/  # Progress dashboard
│       │   ├── quiz/      # Quiz components
│       │   └── ui/        # Shared UI components
│       ├── context/       # React contexts
│       │   ├── AuthContext.jsx
│       │   └── ThemeContext.jsx
│       └── lib/           # Utilities
├── backend/               # Flask application
│   ├── app/
│   │   ├── models/        # Data models
│   │   ├── routes/        # API endpoints
│   │   └── services/      # Business logic
│   │       ├── agent_orchestrator.py
│   │       ├── nebius_client.py
│   │       └── nebius_config.py
│   ├── config/            # Configuration files
│   │   └── nebius.json
│   ├── tests/             # Backend tests
│   │   └── properties/    # Property-based tests
│   └── uploads/           # User uploaded files
├── public/                # Static assets
├── mix.py                 # Build runner
├── DEVLOG.md              # Development log
└── README.md
```

## Agent System

### Agent Loading Flow

```
1. AgentOrchestrator initializes
2. Loads prompt configurations from .kiro/prompts/*.json
3. Creates AgentPrompt objects for each agent
4. Initializes NebiusClient with API credentials
5. Caches agents for subsequent requests
```

### TutorAgent Flow

```
User Question
     │
     ▼
POST /api/chat/message (or /api/chat/stream)
     │
     ▼
AgentOrchestrator.process_chat()
     │
     ├── Load TutorAgent prompt from JSON
     ├── Build prompt with conversation history
     ├── Inject content context (if available)
     ├── Call Nebius API (streaming or sync)
     │
     ▼
Response streamed/returned to frontend
```

### QuizAgent Flow

```
Quiz Request (topic or content_id)
     │
     ▼
POST /api/quiz/generate
     │
     ▼
AgentOrchestrator.generate_quiz()
     │
     ├── Load QuizAgent prompt from JSON
     ├── Build prompt with topic/content
     ├── Call Nebius API with JSON schema
     ├── Parse and validate JSON response
     │
     ▼
Quiz questions returned
     │
     ▼
User answers questions
     │
     ▼
POST /api/quiz/submit
     │
     ├── Calculate score
     ├── Update progress
     │
     ▼
Results returned with explanations
```

### ContentAgent Flow

```
File Upload (PDF/Video/Image)
     │
     ▼
POST /api/content/upload
     │
     ├── Validate file type
     ├── Save file to uploads/
     │
     ▼
ContentService.process_content()
     │
     ├── Extract text (PDF) or frames (video)
     ├── Chunk large content
     │
     ▼
AgentOrchestrator.process_content()
     │
     ├── Load ContentAgent prompt
     ├── Use Vision model for images
     ├── Use Text model for text content
     ├── Synthesize chunks if needed
     │
     ▼
Summary and key points stored
     │
     ▼
Content available for TutorAgent and QuizAgent
```

## Nebius AI Integration

### Configuration

```json
// backend/config/nebius.json
{
  "base_url": "https://api.tokenfactory.nebius.com/v1/",
  "models": {
    "text": "DeepSeek-V3",
    "vision": "Gemma-3-27b-it",
    "embedding": "e5-mistral-7b-instruct"
  },
  "defaults": {
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

### Error Handling

```
API Call
     │
     ├── Success → Return response
     │
     ├── Rate Limited → Queue + notify user
     │
     ├── Timeout → Retry (up to 3x with backoff)
     │
     └── All retries failed → Graceful error message
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Authenticate user |
| `/api/auth/anonymous` | POST | Create anonymous session |
| `/api/chat/message` | POST | Send message to TutorAgent |
| `/api/chat/stream` | POST | Stream response from TutorAgent |
| `/api/content/upload` | POST | Upload PDF/video |
| `/api/content/list` | GET | List user's content |
| `/api/quiz/generate` | POST | Generate quiz |
| `/api/quiz/submit` | POST | Submit quiz answers |
| `/api/progress` | GET | Get user progress |
| `/api/health` | GET | Health check |

## Agent Prompt Structure

Each agent prompt JSON file follows this schema:

```json
{
  "name": "AgentName",
  "version": "1.0.0",
  "role": "Agent role description",
  "description": "What the agent does",
  "model": {
    "provider": "nebius",
    "name": "model-name",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 2048
    }
  },
  "system_prompt": "Instructions for the LLM",
  "output_schema": { ... },
  "example_format": {
    "input": { ... },
    "output": { ... }
  },
  "context_guidance": [
    "Guidance for handling context"
  ],
  "capabilities": [ ... ],
  "limitations": [ ... ]
}
```

## Theme System

```
ThemeProvider
     │
     ├── Detects prefers-color-scheme on load
     ├── Persists preference to localStorage
     ├── Applies 'dark' class to document root
     │
     ▼
Components use dark: variants (Tailwind)
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| JSON-based prompts | Easy iteration without code changes |
| Streaming responses | Better perceived performance |
| In-memory → SQLite | Started simple, migrated for persistence |
| Modular agents | Each agent has single responsibility |
| Context injection | Uploaded content enhances all responses |
| Property-based tests | Catches edge cases unit tests miss |

## Coding Standards

- **Python**: Follow PEP 8, use type hints
- **JavaScript**: ES6+, functional components
- **CSS**: Tailwind utility classes, dark mode support
- **Testing**: Hypothesis for property-based tests

## Running the Application

```bash
# Development (both servers)
python mix.py dev

# Frontend only
cd frontend && npm run dev

# Backend only
cd backend && python run.py

# Run tests
cd backend && pytest
```

## Environment Variables

```bash
# backend/.env
NEBIUS_API_KEY=your_api_key_here
FLASK_ENV=development
SECRET_KEY=your_secret_key
```

# MentorMind Architecture

## System Overview

MentorMind is a personal AI tutor application built with a React (Vite) frontend and Flask backend. The system employs three specialized AI agents to provide interactive learning experiences.

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
                        │ HTTP/REST
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
│         └────────┘ └────────┘ └────────┘                        │
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
│   └── steering/          # Architecture documentation
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
│   ├── tests/             # Backend tests
│   └── uploads/           # User uploaded files
├── public/                # Static assets
├── mix.py                 # Build runner
└── README.md
```

## Agent Orchestration Flow

The AgentOrchestrator is the central service that manages all AI agent interactions.

### Agent Loading

```
1. AgentOrchestrator initializes
2. Loads prompt configurations from .kiro/prompts/*.json
3. Creates AgentPrompt objects for each agent
4. Caches agents for subsequent requests
```

### Chat Flow (TutorAgent)

```
User Question
     │
     ▼
POST /api/chat/message
     │
     ▼
AgentOrchestrator.process_chat()
     │
     ├── Load TutorAgent prompt
     ├── Build prompt with context (if content uploaded)
     ├── Call LLM API (placeholder in current implementation)
     │
     ▼
Response returned to frontend
```

### Quiz Generation Flow (QuizAgent)

```
Quiz Request (topic or content_id)
     │
     ▼
POST /api/quiz/generate
     │
     ▼
AgentOrchestrator.generate_quiz()
     │
     ├── Load QuizAgent prompt
     ├── Build prompt with topic/content
     ├── Generate questions via LLM
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

### Content Processing Flow (ContentAgent)

```
File Upload (PDF/Video)
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
     ├── Extract text (PDF parsing / video transcription)
     │
     ▼
AgentOrchestrator.process_content()
     │
     ├── Load ContentAgent prompt
     ├── Extract key points via LLM
     │
     ▼
Summary and key points stored
     │
     ▼
Content available for TutorAgent and QuizAgent
```

## Data Flow

### Authentication

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │────▶│ /api/auth│────▶│  Auth    │
│AuthContext│    │  routes  │     │ Service  │
└──────────┘     └──────────┘     └──────────┘
                                       │
                                       ▼
                                  ┌──────────┐
                                  │  User    │
                                  │ Storage  │
                                  └──────────┘
```

### Progress Tracking

```
Quiz Completion
     │
     ▼
ProgressService.record_quiz_result()
     │
     ├── Update total quizzes
     ├── Update correct answers
     ├── Update topic progress
     ├── Add to history
     │
     ▼
GET /api/progress
     │
     ├── Calculate success rate
     ├── Categorize topics (mastered/needs work)
     │
     ▼
ProgressDashboard displays metrics
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Authenticate user |
| `/api/auth/anonymous` | POST | Create anonymous session |
| `/api/chat/message` | POST | Send message to TutorAgent |
| `/api/content/upload` | POST | Upload PDF/video |
| `/api/content/list` | GET | List user's content |
| `/api/quiz/generate` | POST | Generate quiz |
| `/api/quiz/submit` | POST | Submit quiz answers |
| `/api/progress` | GET | Get user progress |
| `/api/health` | GET | Health check |

## Agent Prompt Structure

Each agent prompt JSON file contains:

```json
{
  "name": "AgentName",
  "role": "Agent role description",
  "description": "What the agent does",
  "system_prompt": "Instructions for the LLM",
  "example_format": {
    "input": { ... },
    "output": { ... }
  },
  "context_guidance": [
    "Guidance for handling context"
  ]
}
```

## Theme System

The theme system uses Tailwind CSS class strategy:

```
ThemeProvider
     │
     ├── Detects prefers-color-scheme on load
     ├── Persists preference to localStorage
     ├── Applies 'dark' class to document root
     │
     ▼
Components use dark: variants
```

## Key Design Decisions

1. **In-Memory Storage**: Current implementation uses in-memory storage for rapid prototyping. Production would use a database.

2. **Modular Agents**: Agent prompts are stored in JSON files for easy modification without code changes.

3. **Context Providers**: React contexts manage global state (auth, theme) to avoid prop drilling.

4. **Service Layer**: Backend services encapsulate business logic, keeping routes thin.

5. **Placeholder LLM Calls**: Agent methods return placeholder responses; real LLM integration would replace these.

## Running the Application

```bash
# Start both frontend and backend
python mix.py dev

# Frontend: http://localhost:5173
# Backend: http://localhost:5000
```

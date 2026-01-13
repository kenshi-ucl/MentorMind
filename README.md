# MentorMind

Your Personal AI Tutor — Learn Smarter

MentorMind is an AI-powered tutoring application that helps users learn through interactive chat, content summarization, quiz generation, and progress tracking.

## Features

- **AI Chat Tutor**: Ask questions and get explanations from the TutorAgent
- **Content Upload**: Upload videos and PDFs for AI-powered summarization
- **Quiz Generation**: Test your knowledge with AI-generated quizzes
- **Progress Tracking**: Monitor your learning progress over time
- **Dark/Light Theme**: Comfortable learning in any lighting condition

## Tech Stack

- **Frontend**: React + Vite, Tailwind CSS, ShadCN UI
- **Backend**: Python Flask
- **AI Agents**: TutorAgent, QuizAgent, ContentAgent

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+

### Installation

1. Clone the repository

2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Development

Run both frontend and backend servers concurrently:

```bash
python mix.py dev
```

This starts:
- Frontend: http://localhost:5173
- Backend: http://localhost:5000

### Build for Production

```bash
python mix.py build
```

## Project Structure

```
mentormind/
├── frontend/           # React + Vite frontend
│   ├── src/
│   │   ├── components/ # UI components
│   │   └── lib/        # Utilities
│   └── public/         # Static assets
├── backend/            # Flask backend
│   ├── app/
│   │   └── routes/     # API endpoints
│   └── run.py          # Server entry point
├── public/             # Shared static assets
├── .kiro/
│   └── prompts/        # AI agent prompt configurations
├── mix.py              # Build runner
└── README.md
```

## License

MIT

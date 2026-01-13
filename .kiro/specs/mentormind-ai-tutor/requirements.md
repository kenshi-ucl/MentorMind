# Requirements Document

## Introduction

MentorMind is a personal AI tutor application that helps users learn smarter through an interactive chat-based interface, content summarization, quiz generation, and progress tracking. The application features a split-pane UI with a React frontend (Vite), Flask backend, and three specialized AI agents (TutorAgent, QuizAgent, ContentAgent).

## Glossary

- **MentorMind_System**: The complete AI tutor application including frontend, backend, and AI agents
- **TutorAgent**: AI agent responsible for answering questions, explaining concepts, and summarizing content
- **QuizAgent**: AI agent that generates multiple-choice quizzes based on topics or summarized content
- **ContentAgent**: AI agent that extracts key information from uploaded videos and PDFs
- **User**: A person interacting with the MentorMind application
- **Anonymous_User**: A user who continues without creating an account
- **Authenticated_User**: A user who has created an account and logged in
- **Lesson_Content**: Educational material including uploaded videos, PDFs, or text-based lessons
- **Progress_Dashboard**: Visual display of user learning metrics and performance over time
- **Theme_Toggle**: UI control for switching between light and dark color modes

## Requirements

### Requirement 1: User Authentication

**User Story:** As a user, I want to create an account or continue anonymously, so that I can begin learning without friction.

#### Acceptance Criteria

1. WHEN a user visits the application THEN THE MentorMind_System SHALL display options to create an account, login, or continue anonymously
2. WHEN a user chooses to continue anonymously THEN THE MentorMind_System SHALL grant immediate access to the chat interface without requiring credentials
3. WHEN a user creates an account THEN THE MentorMind_System SHALL store their credentials securely and create a user profile
4. WHEN an Authenticated_User logs in with valid credentials THEN THE MentorMind_System SHALL authenticate the user and restore their learning history
5. IF a user provides invalid credentials THEN THE MentorMind_System SHALL display an error message and allow retry

### Requirement 2: Landing Page

**User Story:** As a visitor, I want to see a compelling landing page, so that I understand MentorMind's value proposition before starting.

#### Acceptance Criteria

1. WHEN a visitor loads the application THEN THE MentorMind_System SHALL display a hero section with the tagline "Your Personal AI Tutor — Learn Smarter"
2. WHEN the landing page renders THEN THE MentorMind_System SHALL display the MentorMind logo (graduation cap with spark icon)
3. WHEN the landing page renders THEN THE MentorMind_System SHALL display a call-to-action button to start chatting or login
4. WHEN a visitor clicks the call-to-action THEN THE MentorMind_System SHALL navigate to the authentication options

### Requirement 3: Theme and Layout

**User Story:** As a user, I want a visually appealing split-pane interface with theme switching, so that I can learn comfortably in any lighting condition.

#### Acceptance Criteria

1. THE MentorMind_System SHALL display a split-pane layout with a left sidebar for navigation and a main content area
2. THE MentorMind_System SHALL include navigation items: Dashboard, Lessons, Practice, Progress, and Settings in the left sidebar
3. THE MentorMind_System SHALL display a top bar with the app title, theme-switch toggle, and user profile
4. WHEN the application loads THEN THE MentorMind_System SHALL detect the user's prefers-color-scheme setting and apply the corresponding theme
5. WHEN a user clicks the theme toggle THEN THE MentorMind_System SHALL switch between light and dark modes using Tailwind CSS class strategy
6. THE MentorMind_System SHALL use Indigo (#4F46E5) as the primary color and Cyan (#22D3EE) as the accent color

### Requirement 4: Chat Interface (TutorAgent)

**User Story:** As a learner, I want to ask questions and receive explanations from an AI tutor, so that I can understand concepts better.

#### Acceptance Criteria

1. WHEN a user navigates to the chat interface THEN THE MentorMind_System SHALL display a message input field and conversation history
2. WHEN a user submits a question THEN THE TutorAgent SHALL process the question and return an explanatory response
3. WHEN the TutorAgent responds THEN THE MentorMind_System SHALL display the response in the chat conversation with clear formatting
4. WHEN a user requests simplification THEN THE TutorAgent SHALL provide a simpler explanation of the concept
5. WHILE content has been uploaded THEN THE TutorAgent SHALL answer questions based on that summarized content
6. WHEN the TutorAgent is processing a request THEN THE MentorMind_System SHALL display a loading indicator

### Requirement 5: Content Upload and Processing

**User Story:** As a learner, I want to upload study materials (videos or PDFs), so that the AI can help me understand and quiz me on that content.

#### Acceptance Criteria

1. WHEN a user initiates content upload THEN THE MentorMind_System SHALL accept video files and PDF documents
2. WHEN a file is uploaded THEN THE ContentAgent SHALL extract key points and main concepts from the content
3. WHEN content processing completes THEN THE MentorMind_System SHALL display a summary of extracted key points
4. IF content upload fails THEN THE MentorMind_System SHALL display an error message with the reason
5. WHEN content is successfully processed THEN THE MentorMind_System SHALL make it available to TutorAgent and QuizAgent for reference

### Requirement 6: Quiz Generation

**User Story:** As a learner, I want to take quizzes generated from lesson topics or uploaded content, so that I can test my understanding.

#### Acceptance Criteria

1. WHEN a user requests a quiz on a topic THEN THE QuizAgent SHALL generate multiple-choice questions with answers and explanations
2. WHEN a quiz is generated THEN THE MentorMind_System SHALL display questions one at a time with selectable answer options
3. WHEN a user selects an answer THEN THE MentorMind_System SHALL record the response and provide immediate feedback
4. WHEN a quiz is completed THEN THE MentorMind_System SHALL display the score and explanations for incorrect answers
5. WHEN a quiz is completed THEN THE MentorMind_System SHALL store the results for progress tracking

### Requirement 7: Progress Dashboard

**User Story:** As a learner, I want to view my learning progress over time, so that I can track my improvement and identify areas needing attention.

#### Acceptance Criteria

1. WHEN a user navigates to the Progress view THEN THE MentorMind_System SHALL display performance metrics and charts
2. THE Progress_Dashboard SHALL display success rate statistics across quizzes
3. THE Progress_Dashboard SHALL display topics mastered and topics needing improvement
4. THE Progress_Dashboard SHALL visualize learning progress over time using charts
5. WHEN new quiz results are recorded THEN THE Progress_Dashboard SHALL update to reflect the latest data

### Requirement 8: AI Agent Prompt System

**User Story:** As a developer, I want modular AI agent prompts stored in configuration files, so that agents can be easily maintained and improved.

#### Acceptance Criteria

1. THE MentorMind_System SHALL store TutorAgent prompt configuration in .kiro/prompts/TutorAgent.json
2. THE MentorMind_System SHALL store QuizAgent prompt configuration in .kiro/prompts/QuizAgent.json
3. THE MentorMind_System SHALL store ContentAgent prompt configuration in .kiro/prompts/ContentAgent.json
4. WHEN an agent processes a request THEN THE MentorMind_System SHALL load the corresponding prompt template from the configuration file
5. THE agent prompt files SHALL include role description, example format, and context guidance

### Requirement 9: Build System

**User Story:** As a developer, I want a unified build script that launches both frontend and backend servers, so that development is streamlined.

#### Acceptance Criteria

1. WHEN a developer runs `python mix.py dev` THEN THE MentorMind_System SHALL concurrently launch the Vite dev server and Flask server
2. THE MentorMind_System SHALL organize code with /frontend for React+Vite, /backend for Flask, and /public for static assets
3. THE MentorMind_System SHALL include a README.md with setup and usage instructions
4. THE MentorMind_System SHALL include a DEVLOG.md for recording development progress

### Requirement 10: Demo Data and Flow

**User Story:** As a demonstrator, I want seeded demo data and a clear user journey, so that I can showcase MentorMind's capabilities end-to-end.

#### Acceptance Criteria

1. THE MentorMind_System SHALL include example user accounts for demonstration purposes
2. THE MentorMind_System SHALL include sample lesson content and quiz examples
3. THE demo flow SHALL support: Landing page → Login/Anonymous → Chat with TutorAgent → Upload content → Generate quiz → View Progress dashboard

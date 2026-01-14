# Design Document: Database Integration

## Overview

This design describes the integration of SQLite/MySQL database into MentorMind to replace in-memory storage with persistent data storage. The integration uses SQLAlchemy ORM for database operations, providing a clean abstraction layer that supports both SQLite (default) and MySQL (production).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Flask Application                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Route Handlers                         │   │
│  │  /auth  │  /chat  │  /content  │  /quiz  │  /progress    │   │
│  └────┬────────┬──────────┬───────────┬──────────┬──────────┘   │
│       │        │          │           │          │               │
│  ┌────┴────────┴──────────┴───────────┴──────────┴──────────┐   │
│  │                    Service Layer                          │   │
│  │  AuthService │ ContentService │ ProgressService           │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│  ┌────────────────────────┴─────────────────────────────────┐   │
│  │                  SQLAlchemy ORM Layer                     │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐ │   │
│  │  │  User   │ │ Session │ │ Content │ │   QuizResult    │ │   │
│  │  │  Model  │ │  Model  │ │  Model  │ │     Model       │ │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └───────┬─────────┘ │   │
│  │       └───────────┴───────────┴──────────────┘            │   │
│  │                           │                                │   │
│  │              ┌────────────▼────────────┐                  │   │
│  │              │    Database Engine      │                  │   │
│  │              │  SQLite / MySQL         │                  │   │
│  │              └─────────────────────────┘                  │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  mentormind.db  │
                    │   (SQLite)      │
                    └─────────────────┘
```

## Components and Interfaces

### Database Configuration

```python
# backend/app/database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def init_db(app):
    """Initialize database with Flask app."""
    # Default to SQLite
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///data/mentormind.db')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
```

### User Model

```python
# backend/app/models/user.py
from app.database import db
from datetime import datetime
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='user', lazy='dynamic')
    contents = db.relationship('Content', backref='user', lazy='dynamic')
    quiz_results = db.relationship('QuizResult', backref='user', lazy='dynamic')
```

### Session Model

```python
# backend/app/models/session.py
from app.database import db
from datetime import datetime, timedelta
import uuid

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(36), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def create_for_user(cls, user_id, duration_hours=24):
        return cls(
            user_id=user_id,
            token=str(uuid.uuid4()),
            expires_at=datetime.utcnow() + timedelta(hours=duration_hours)
        )
```

### Content Model

```python
# backend/app/models/content.py
from app.database import db
from datetime import datetime
import uuid
import json

class Content(db.Model):
    __tablename__ = 'contents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    title = db.Column(db.String(255), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    key_points_json = db.Column(db.Text, nullable=True)  # JSON array
    topics_json = db.Column(db.Text, nullable=True)  # JSON array
    processing_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def key_points(self):
        return json.loads(self.key_points_json) if self.key_points_json else []
    
    @key_points.setter
    def key_points(self, value):
        self.key_points_json = json.dumps(value) if value else None
    
    @property
    def topics(self):
        return json.loads(self.topics_json) if self.topics_json else []
    
    @topics.setter
    def topics(self, value):
        self.topics_json = json.dumps(value) if value else None
```

### QuizResult Model

```python
# backend/app/models/quiz_result.py
from app.database import db
from datetime import datetime
import uuid
import json

class QuizResult(db.Model):
    __tablename__ = 'quiz_results'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.String(36), nullable=False)
    topic = db.Column(db.String(255), nullable=True)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    answers_json = db.Column(db.Text, nullable=True)  # JSON object
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def answers(self):
        return json.loads(self.answers_json) if self.answers_json else {}
    
    @answers.setter
    def answers(self, value):
        self.answers_json = json.dumps(value) if value else None
    
    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100, 1)
```

### Updated AuthService

```python
# backend/app/services/auth_service.py
from app.database import db
from app.models.user import User
from app.models.session import Session
from werkzeug.security import generate_password_hash, check_password_hash

class AuthService:
    def register(self, email: str, password: str, name: str) -> dict:
        """Register a new user."""
        existing = User.query.filter_by(email=email).first()
        if existing:
            return None
        
        user = User(
            email=email,
            name=name,
            password_hash=generate_password_hash(password),
            is_anonymous=False
        )
        db.session.add(user)
        db.session.commit()
        
        session = Session.create_for_user(user.id)
        db.session.add(session)
        db.session.commit()
        
        return {'user': user, 'session': session}
    
    def login(self, email: str, password: str) -> dict:
        """Authenticate user and create session."""
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return None
        
        user.last_login = datetime.utcnow()
        session = Session.create_for_user(user.id)
        db.session.add(session)
        db.session.commit()
        
        return {'user': user, 'session': session}
    
    def create_anonymous(self) -> dict:
        """Create anonymous user and session."""
        user = User(
            name='Anonymous User',
            is_anonymous=True
        )
        db.session.add(user)
        db.session.commit()
        
        session = Session.create_for_user(user.id)
        db.session.add(session)
        db.session.commit()
        
        return {'user': user, 'session': session}
    
    def validate_token(self, token: str) -> User:
        """Validate session token and return user."""
        session = Session.query.filter_by(token=token).first()
        if not session or session.is_expired:
            return None
        return session.user
    
    def logout(self, token: str) -> bool:
        """Invalidate session."""
        session = Session.query.filter_by(token=token).first()
        if session:
            db.session.delete(session)
            db.session.commit()
            return True
        return False
```

### Updated ProgressService

```python
# backend/app/services/progress_service.py
from app.database import db
from app.models.quiz_result import QuizResult
from collections import defaultdict

class ProgressService:
    def record_quiz_result(self, user_id: str, quiz_id: str, topic: str,
                          score: int, total: int, answers: dict) -> QuizResult:
        """Record a quiz result."""
        result = QuizResult(
            user_id=user_id,
            quiz_id=quiz_id,
            topic=topic,
            score=score,
            total_questions=total,
            answers=answers
        )
        db.session.add(result)
        db.session.commit()
        return result
    
    def get_progress(self, user_id: str) -> dict:
        """Get aggregated progress for user."""
        results = QuizResult.query.filter_by(user_id=user_id).all()
        
        if not results:
            return {
                'totalQuizzes': 0,
                'totalQuestions': 0,
                'correctAnswers': 0,
                'successRate': 0,
                'topicProgress': {},
                'recentActivity': []
            }
        
        total_questions = sum(r.total_questions for r in results)
        correct_answers = sum(r.score for r in results)
        
        # Topic-wise progress
        topic_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        for r in results:
            if r.topic:
                topic_stats[r.topic]['correct'] += r.score
                topic_stats[r.topic]['total'] += r.total_questions
        
        topic_progress = {}
        for topic, stats in topic_stats.items():
            percentage = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            topic_progress[topic] = {
                'percentage': round(percentage, 1),
                'quizzes': len([r for r in results if r.topic == topic])
            }
        
        # Recent activity (last 10)
        recent = sorted(results, key=lambda r: r.created_at, reverse=True)[:10]
        recent_activity = [{
            'quizId': r.quiz_id,
            'topic': r.topic,
            'score': r.score,
            'total': r.total_questions,
            'percentage': r.percentage,
            'date': r.created_at.isoformat()
        } for r in recent]
        
        return {
            'totalQuizzes': len(results),
            'totalQuestions': total_questions,
            'correctAnswers': correct_answers,
            'successRate': round((correct_answers / total_questions * 100), 1) if total_questions > 0 else 0,
            'topicProgress': topic_progress,
            'recentActivity': recent_activity
        }
```

### Updated ContentService

```python
# backend/app/services/content_service.py
from app.database import db
from app.models.content import Content
import os

class ContentService:
    def __init__(self, upload_dir: str = 'uploads'):
        self.upload_dir = upload_dir
    
    def save_content(self, user_id: str, filename: str, content_type: str,
                    file_data: bytes) -> Content:
        """Save uploaded content."""
        # Create user-specific directory
        user_dir = os.path.join(self.upload_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(user_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Create database record
        content = Content(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_path=file_path,
            file_size=len(file_data),
            processing_status='pending'
        )
        db.session.add(content)
        db.session.commit()
        
        return content
    
    def update_content_metadata(self, content_id: str, title: str, summary: str,
                               key_points: list, topics: list) -> Content:
        """Update content with extracted metadata."""
        content = Content.query.get(content_id)
        if content:
            content.title = title
            content.summary = summary
            content.key_points = key_points
            content.topics = topics
            content.processing_status = 'complete'
            db.session.commit()
        return content
    
    def get_user_content(self, user_id: str) -> list:
        """Get all content for a user."""
        return Content.query.filter_by(user_id=user_id).order_by(
            Content.created_at.desc()
        ).all()
    
    def get_content(self, content_id: str, user_id: str) -> Content:
        """Get specific content if owned by user."""
        return Content.query.filter_by(id=content_id, user_id=user_id).first()
    
    def delete_content(self, content_id: str, user_id: str) -> bool:
        """Delete content and file."""
        content = self.get_content(content_id, user_id)
        if content:
            # Delete file
            if os.path.exists(content.file_path):
                os.remove(content.file_path)
            # Delete record
            db.session.delete(content)
            db.session.commit()
            return True
        return False
```

## Data Models

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐
│    User     │       │   Session   │
├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ id (PK)     │
│ email       │  │    │ user_id (FK)│──┐
│ name        │  │    │ token       │  │
│ password    │  │    │ created_at  │  │
│ is_anonymous│  │    │ expires_at  │  │
│ created_at  │  │    └─────────────┘  │
│ last_login  │  │                     │
└─────────────┘  │    ┌─────────────┐  │
                 │    │   Content   │  │
                 │    ├─────────────┤  │
                 ├───▶│ id (PK)     │  │
                 │    │ user_id (FK)│◀─┤
                 │    │ filename    │  │
                 │    │ content_type│  │
                 │    │ file_path   │  │
                 │    │ title       │  │
                 │    │ summary     │  │
                 │    │ key_points  │  │
                 │    │ created_at  │  │
                 │    └─────────────┘  │
                 │                     │
                 │    ┌─────────────┐  │
                 │    │ QuizResult  │  │
                 │    ├─────────────┤  │
                 └───▶│ id (PK)     │  │
                      │ user_id (FK)│◀─┘
                      │ quiz_id     │
                      │ topic       │
                      │ score       │
                      │ total       │
                      │ answers     │
                      │ created_at  │
                      └─────────────┘
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: User Persistence Round-Trip

*For any* valid user registration data (email, password, name), registering the user and then retrieving by email SHALL return the same user data (excluding password which is hashed).

**Validates: Requirements 2.1, 2.3, 2.5**

### Property 2: Authentication Correctness

*For any* registered user with email and password, logging in with correct credentials SHALL succeed and return a valid session, while logging in with incorrect credentials SHALL fail.

**Validates: Requirements 2.2**

### Property 3: Session Lifecycle Validity

*For any* authenticated user session, the token SHALL be valid until expiration, and SHALL be invalid after expiration or logout.

**Validates: Requirements 3.1, 3.3, 3.4**

### Property 4: Content User Isolation

*For any* two different users A and B, content uploaded by user A SHALL NOT be visible when listing content for user B, and vice versa.

**Validates: Requirements 4.3**

### Property 5: Content Persistence Round-Trip

*For any* uploaded content with metadata, saving and then retrieving the content SHALL return the same metadata (filename, content_type, title, summary, key_points).

**Validates: Requirements 4.1, 4.5**

### Property 6: Content Deletion Completeness

*For any* deleted content, both the database record AND the physical file SHALL be removed.

**Validates: Requirements 4.4**

### Property 7: Progress Calculation Accuracy

*For any* user with N quiz results, the progress metrics (totalQuizzes, totalQuestions, correctAnswers, successRate) SHALL be mathematically consistent with the stored quiz results.

**Validates: Requirements 5.1, 5.3, 5.5**

### Property 8: Topic Progress Tracking

*For any* user with quiz results across multiple topics, the topic-wise progress SHALL correctly aggregate scores per topic.

**Validates: Requirements 5.4**

### Property 9: Data Persistence Across Restarts

*For any* data stored in the database, restarting the application SHALL NOT lose or corrupt the data.

**Validates: Requirements 6.2**

## Error Handling

### Error Categories

1. **Database Connection Errors**
   - Connection refused → Return 503 Service Unavailable
   - Connection timeout → Retry with backoff, then 503

2. **Query Errors**
   - Constraint violation → Return 400 Bad Request with message
   - Not found → Return 404 Not Found
   - General query error → Log and return 500 Internal Server Error

3. **Transaction Errors**
   - Deadlock → Retry transaction
   - Rollback required → Rollback and return appropriate error

4. **Authentication Errors**
   - Invalid token → Return 401 Unauthorized
   - Expired session → Return 401 with "Session expired" message
   - Missing token → Return 401 with "Authorization required" message

### Error Response Format

```python
{
    "error": "User-friendly error message",
    "code": "ERROR_CODE",
    "details": {}  # Optional additional details
}
```

## Testing Strategy

### Unit Tests

- Test model creation and field validation
- Test service methods with mocked database
- Test error handling for various failure scenarios

### Property-Based Tests

Using Hypothesis for Python:

1. **User Round-Trip Test**: Generate random user data, verify persistence
2. **Session Validity Test**: Generate sessions with various expiration times
3. **Content Isolation Test**: Generate multiple users and content, verify isolation
4. **Progress Calculation Test**: Generate quiz results, verify math accuracy

### Integration Tests

- Test full authentication flow (register → login → validate → logout)
- Test content upload and retrieval flow
- Test quiz completion and progress tracking

### Test Configuration

```python
# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

# Property test settings
HYPOTHESIS_SETTINGS = {
    "max_examples": 100,
    "deadline": None,
}
```

## File Structure

```
backend/
├── app/
│   ├── __init__.py          # Updated with db init
│   ├── database.py          # NEW: Database configuration
│   ├── models/
│   │   ├── __init__.py      # Export all models
│   │   ├── user.py          # NEW: User model
│   │   ├── session.py       # NEW: Session model
│   │   ├── content.py       # NEW: Content model
│   │   └── quiz_result.py   # NEW: QuizResult model
│   ├── services/
│   │   ├── auth_service.py  # UPDATED: Use database
│   │   ├── content_service.py # UPDATED: Use database
│   │   └── progress_service.py # UPDATED: Use database
│   └── routes/
│       ├── auth.py          # UPDATED: Use new auth service
│       ├── content.py       # UPDATED: Use new content service
│       └── progress.py      # UPDATED: Use new progress service
├── data/                    # NEW: Database storage directory
│   └── mentormind.db        # SQLite database file
└── tests/
    └── properties/
        └── test_database_properties.py  # NEW: Property tests
```

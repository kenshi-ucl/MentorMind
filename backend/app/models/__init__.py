"""
Models package for MentorMind.

Exports all SQLAlchemy ORM models and utility functions.
"""
from app.models.user import User
from app.models.session import Session
from app.models.content import (
    Content, 
    get_file_type, 
    is_allowed_file, 
    ALLOWED_EXTENSIONS, 
    ALLOWED_FILE_TYPES
)
from app.models.quiz_result import QuizResult
from app.models.agent_prompt import AgentPrompt
from app.models.progress import UserProgress, TopicProgress, ProgressEntry

__all__ = [
    # SQLAlchemy ORM Models
    "User",
    "Session",
    "Content",
    "QuizResult",
    # Legacy models (for compatibility)
    "AgentPrompt",
    "UserProgress",
    "TopicProgress",
    "ProgressEntry",
    # Content utilities
    "get_file_type",
    "is_allowed_file",
    "ALLOWED_EXTENSIONS",
    "ALLOWED_FILE_TYPES",
]

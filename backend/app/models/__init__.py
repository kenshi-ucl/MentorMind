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
from app.models.conversation import Conversation, Message

# Friends & Communication models
from app.models.friend import Friend
from app.models.friend_request import FriendRequest, RequestStatus
from app.models.direct_chat import DirectChat
from app.models.message import DirectMessage, GroupMessage
from app.models.group_learning import GroupLearning
from app.models.group_member import GroupMember
from app.models.call import Call, CallParticipant
from app.models.user_presence import UserPresence

__all__ = [
    # SQLAlchemy ORM Models
    "User",
    "Session",
    "Content",
    "QuizResult",
    "Conversation",
    "Message",
    # Friends & Communication Models
    "Friend",
    "FriendRequest",
    "RequestStatus",
    "DirectChat",
    "DirectMessage",
    "GroupMessage",
    "GroupLearning",
    "GroupMember",
    "Call",
    "CallParticipant",
    "UserPresence",
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

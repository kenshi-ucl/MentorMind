"""
Session model for database persistence.

Defines the Session table with SQLAlchemy ORM for storing user authentication sessions.
"""
import uuid
from datetime import datetime, timedelta

from app.database import db


class Session(db.Model):
    """Session model representing authenticated user sessions."""
    
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(36), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<Session {self.id}: user={self.user_id}>'
    
    @property
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def create_for_user(cls, user_id: str, duration_hours: int = 24) -> 'Session':
        """
        Create a new session for a user.
        
        Args:
            user_id: The ID of the user to create a session for.
            duration_hours: How long the session should be valid (default 24 hours).
            
        Returns:
            A new Session instance (not yet committed to database).
        """
        return cls(
            user_id=user_id,
            token=str(uuid.uuid4()),
            expires_at=datetime.utcnow() + timedelta(hours=duration_hours)
        )
    
    def refresh(self, duration_hours: int = 24) -> None:
        """
        Refresh the session expiration time.
        
        Args:
            duration_hours: How long to extend the session (default 24 hours).
        """
        self.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
    
    def to_dict(self) -> dict:
        """Convert session to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired
        }

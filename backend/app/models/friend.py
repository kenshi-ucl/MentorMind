"""
Friend model for storing user friendships.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from app.database import db


class Friend(db.Model):
    """Model representing a friendship between two users."""
    __tablename__ = 'friends'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    friend_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Ensure unique friendship pairs
    __table_args__ = (
        UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),
    )
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='friendships')
    friend = db.relationship('User', foreign_keys=[friend_id])
    
    def to_dict(self):
        """Convert friendship to dictionary."""
        return {
            'id': self.id,
            'userId': self.user_id,
            'friendId': self.friend_id,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

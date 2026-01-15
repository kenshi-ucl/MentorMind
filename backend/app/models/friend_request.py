"""
FriendRequest model for managing friend request states.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from app.database import db
import enum


class RequestStatus(enum.Enum):
    """Enum for friend request status."""
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'


class FriendRequest(db.Model):
    """Model representing a friend request between users."""
    __tablename__ = 'friend_requests'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    recipient_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_requests')
    
    def to_dict(self, include_users=False):
        """Convert friend request to dictionary."""
        result = {
            'id': self.id,
            'senderId': self.sender_id,
            'recipientId': self.recipient_id,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_users:
            result['sender'] = self.sender.to_dict() if self.sender else None
            result['recipient'] = self.recipient.to_dict() if self.recipient else None
        return result
